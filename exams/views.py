from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
import json
from datetime import timedelta

from .models import (
    MockExam, ExamSection, Question, QuestionOption, 
    ExamAttempt, SectionAttempt, UserAnswer, ExamConfiguration
)


@login_required
def exam_list(request):
    """List available exams"""
    exams = MockExam.objects.filter(is_active=True).prefetch_related('sections')
    
    # Add total questions count for each exam
    for exam in exams:
        total_questions = 0
        for section in exam.sections.all():
            total_questions += section.questions.filter(is_active=True).count()
        exam.total_questions = total_questions
    
    return render(request, 'exams/exam_list.html', {'exams': exams})


@login_required
def exam_instructions(request):
    """Show exam instructions"""
    exam_id = request.GET.get('exam', 1)
    exam = get_object_or_404(MockExam, id=exam_id, is_active=True)
    
    # Get exam configuration
    config = ExamConfiguration.objects.first()
    if not config:
        config = ExamConfiguration.objects.create()
    
    sections = exam.sections.filter(is_active=True).order_by('name')
    total_duration = exam.total_duration()
    
    context = {
        'exam': exam,
        'config': config,
        'sections': sections,
        'total_duration': total_duration,
    }
    return render(request, 'exams/instructions.html', context)


@login_required
def start_exam(request, exam_id):
    """Start an exam"""
    exam = get_object_or_404(MockExam, id=exam_id, is_active=True)
    
    # Check if user has an ongoing exam attempt
    ongoing_attempt = ExamAttempt.objects.filter(
        user=request.user,
        exam=exam,
        status__in=['not_started', 'in_progress']
    ).first()
    
    if ongoing_attempt:
        messages.info(request, 'You have an ongoing exam. Continuing from where you left off.')
        return redirect('exams:take_exam', exam_id=exam.id)
    
    # Calculate total questions
    total_questions = 0
    for section in exam.sections.all():
        total_questions += section.questions.filter(is_active=True).count()
    
    context = {
        'exam': exam,
        'total_questions': total_questions,
    }
    return render(request, 'exams/start_exam.html', context)


@login_required
def take_exam(request, exam_id):
    """Take exam interface"""
    exam = get_object_or_404(MockExam, id=exam_id, is_active=True)
    
    # Get or create exam attempt
    exam_attempt, created = ExamAttempt.objects.get_or_create(
        user=request.user,
        exam=exam,
        status__in=['not_started', 'in_progress'],
        defaults={
            'status': 'not_started',
            'start_time': timezone.now(),
        }
    )
    
    if created or exam_attempt.status == 'not_started':
        exam_attempt.status = 'in_progress'
        exam_attempt.start_time = timezone.now()
        exam_attempt.save()
    
    # Get current section or first section
    if not exam_attempt.current_section:
        first_section = exam.sections.filter(is_active=True).first()
        exam_attempt.current_section = first_section
        exam_attempt.save()
    
    current_section = exam_attempt.current_section
    
    # Get or create section attempt
    section_attempt, created = SectionAttempt.objects.get_or_create(
        exam_attempt=exam_attempt,
        section=current_section,
        defaults={
            'start_time': timezone.now(),
            'max_possible_score': current_section.max_score,
        }
    )
    
    if created:
        section_attempt.start_time = timezone.now()
        section_attempt.save()
    
    context = {
        'exam': exam,
        'exam_attempt': exam_attempt,
        'current_section': current_section,
        'section_attempt': section_attempt,
    }
    return render(request, 'exams/take_exam.html', context)


@login_required
def exam_section(request, exam_id, section):
    """Individual exam section"""
    exam = get_object_or_404(MockExam, id=exam_id, is_active=True)
    section_obj = get_object_or_404(ExamSection, name=section, is_active=True)
    
    # Get current exam attempt
    exam_attempt = get_object_or_404(
        ExamAttempt,
        user=request.user,
        exam=exam,
        status='in_progress'
    )
    
    # Update current section
    exam_attempt.current_section = section_obj
    exam_attempt.save()
    
    return redirect('exams:take_exam', exam_id=exam.id)


@login_required
def get_questions(request, exam_id):
    """API endpoint to get questions for current section"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    exam = get_object_or_404(MockExam, id=exam_id, is_active=True)
    exam_attempt = get_object_or_404(
        ExamAttempt,
        user=request.user,
        exam=exam,
        status='in_progress'
    )
    
    current_section = exam_attempt.current_section
    if not current_section:
        return JsonResponse({'error': 'No current section'}, status=400)
    
    # Get questions for current section
    questions = Question.objects.filter(
        section=current_section,
        is_active=True
    ).prefetch_related('options').order_by('id')
    
    # Get existing answers
    section_attempt = SectionAttempt.objects.filter(
        exam_attempt=exam_attempt,
        section=current_section
    ).first()
    
    existing_answers = {}
    if section_attempt:
        answers = UserAnswer.objects.filter(section_attempt=section_attempt)
        existing_answers = {
            answer.question.id: answer.selected_option.option_letter 
            for answer in answers if answer.selected_option
        }
    
    # Format questions for JSON response
    questions_data = []
    for question in questions:
        options_data = []
        for option in question.options.all():
            options_data.append({
                'id': option.id,
                'letter': option.option_letter,
                'text': option.option_text,
            })
        
        questions_data.append({
            'id': question.id,
            'text': question.question_text,
            'points': question.points,
            'negative_points': question.negative_points,
            'options': options_data,
            'selected_answer': existing_answers.get(question.id),
        })
    
    # Calculate time remaining
    time_remaining = 0
    if section_attempt and section_attempt.start_time:
        elapsed = timezone.now() - section_attempt.start_time
        total_time = timedelta(minutes=current_section.duration_minutes)
        remaining = total_time - elapsed
        time_remaining = max(0, int(remaining.total_seconds()))
    else:
        time_remaining = current_section.duration_minutes * 60
    
    return JsonResponse({
        'questions': questions_data,
        'section': {
            'id': current_section.id,
            'name': current_section.display_name,
            'duration_minutes': current_section.duration_minutes,
            'time_remaining': time_remaining,
        },
        'existing_answers': existing_answers,
    })


@csrf_exempt
@login_required
def save_answer(request):
    """API endpoint to save user answer"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        option_id = data.get('option_id')
        
        question = get_object_or_404(Question, id=question_id, is_active=True)
        option = get_object_or_404(QuestionOption, id=option_id, question=question)
        
        # Get current exam attempt and section attempt
        exam_attempt = ExamAttempt.objects.filter(
            user=request.user,
            status='in_progress'
        ).first()
        
        if not exam_attempt:
            return JsonResponse({'error': 'No active exam'}, status=400)
        
        section_attempt = SectionAttempt.objects.filter(
            exam_attempt=exam_attempt,
            section=question.section
        ).first()
        
        if not section_attempt:
            return JsonResponse({'error': 'No active section'}, status=400)
        
        # Save or update answer
        answer, created = UserAnswer.objects.update_or_create(
            section_attempt=section_attempt,
            question=question,
            defaults={
                'selected_option': option,
            }
        )
        
        return JsonResponse({
            'success': True,
            'is_correct': answer.is_correct,
            'points_earned': answer.points_earned,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def submit_section(request, exam_id):
    """Submit current section and move to next or finish exam"""
    if request.method != 'POST':
        return redirect('exams:take_exam', exam_id=exam_id)
    
    exam = get_object_or_404(MockExam, id=exam_id, is_active=True)
    exam_attempt = get_object_or_404(
        ExamAttempt,
        user=request.user,
        exam=exam,
        status='in_progress'
    )
    
    current_section = exam_attempt.current_section
    if not current_section:
        messages.error(request, 'No current section to submit.')
        return redirect('exams:exam_list')
    
    # Get section attempt
    section_attempt = SectionAttempt.objects.filter(
        exam_attempt=exam_attempt,
        section=current_section
    ).first()
    
    if section_attempt:
        # Calculate section score
        calculate_section_score(section_attempt)
        
        # Mark section as completed
        section_attempt.is_completed = True
        section_attempt.end_time = timezone.now()
        section_attempt.save()
    
    # Get next section
    exam_sections = list(exam.sections.filter(is_active=True).order_by('name'))
    completed_sections = SectionAttempt.objects.filter(
        exam_attempt=exam_attempt,
        is_completed=True
    ).values_list('section_id', flat=True)
    
    next_section = None
    for section in exam_sections:
        if section.id not in completed_sections:
            next_section = section
            break
    
    if next_section:
        # Move to next section
        exam_attempt.current_section = next_section
        exam_attempt.save()
        
        messages.success(request, f'Section completed! Moving to {next_section.display_name}.')
        return redirect('exams:take_exam', exam_id=exam.id)
    else:
        # All sections completed - finish exam
        finish_exam(exam_attempt)
        messages.success(request, 'Exam completed successfully!')
        return redirect('exams:results', exam_id=exam.id)


def calculate_section_score(section_attempt):
    """Calculate score for a section attempt"""
    answers = UserAnswer.objects.filter(section_attempt=section_attempt)
    
    total_score = 0
    questions_answered = 0
    questions_correct = 0
    
    for answer in answers:
        if answer.selected_option:
            questions_answered += 1
            if answer.is_correct:
                questions_correct += 1
                total_score += answer.question.points
            elif section_attempt.section.has_negative_marking:
                total_score -= answer.question.negative_points
    
    section_attempt.score = max(0, total_score)  # Don't allow negative scores
    section_attempt.questions_answered = questions_answered
    section_attempt.questions_correct = questions_correct
    section_attempt.save()
    
    return section_attempt


def finish_exam(exam_attempt):
    """Finish exam and calculate total score"""
    exam_attempt.status = 'completed'
    exam_attempt.end_time = timezone.now()
    
    # Calculate total score
    section_attempts = SectionAttempt.objects.filter(exam_attempt=exam_attempt)
    total_score = sum(sa.score or 0 for sa in section_attempts)
    max_possible_score = sum(sa.max_possible_score or 0 for sa in section_attempts)
    
    exam_attempt.total_score = total_score
    if max_possible_score > 0:
        exam_attempt.percentage_score = (total_score / max_possible_score) * 100
    else:
        exam_attempt.percentage_score = 0
    
    # Check if passed (all sections must meet minimum pass score)
    passed = True
    for sa in section_attempts:
        if sa.score < sa.section.min_pass_score:
            passed = False
            break
    
    exam_attempt.passed = passed
    exam_attempt.save()
    
    return exam_attempt


@login_required
def submit_exam(request, exam_id):
    """Submit entire exam (emergency submit or time up)"""
    exam = get_object_or_404(MockExam, id=exam_id, is_active=True)
    exam_attempt = get_object_or_404(
        ExamAttempt,
        user=request.user,
        exam=exam,
        status='in_progress'
    )
    
    # Mark current section as completed if exists
    if exam_attempt.current_section:
        section_attempt = SectionAttempt.objects.filter(
            exam_attempt=exam_attempt,
            section=exam_attempt.current_section
        ).first()
        
        if section_attempt and not section_attempt.is_completed:
            calculate_section_score(section_attempt)
            section_attempt.is_completed = True
            section_attempt.end_time = timezone.now()
            section_attempt.save()
    
    # Finish exam
    exam_attempt.status = 'auto_submitted'
    finish_exam(exam_attempt)
    
    messages.warning(request, 'Exam has been automatically submitted.')
    return redirect('exams:results', exam_id=exam.id)


@login_required
def exam_results(request, exam_id):
    """Show exam results"""
    exam = get_object_or_404(MockExam, id=exam_id, is_active=True)
    
    # Get the most recent completed exam attempt
    exam_attempt = ExamAttempt.objects.filter(
        user=request.user,
        exam=exam,
        status__in=['completed', 'auto_submitted']
    ).order_by('-end_time').first()
    
    if not exam_attempt:
        messages.error(request, 'No completed exam found.')
        return redirect('exams:exam_list')
    
    # Get section attempts
    section_attempts = SectionAttempt.objects.filter(
        exam_attempt=exam_attempt
    ).select_related('section').order_by('section__name')
    
    # Add percentage to each section attempt
    for sa in section_attempts:
        if sa.max_possible_score and sa.max_possible_score > 0:
            sa.percentage = (sa.score / sa.max_possible_score) * 100
        else:
            sa.percentage = 0
    
    # Calculate duration
    duration_display = "Not available"
    time_efficiency = 0
    if exam_attempt.start_time and exam_attempt.end_time:
        duration = exam_attempt.end_time - exam_attempt.start_time
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60
        
        if hours > 0:
            duration_display = f"{hours}h {minutes}m {seconds}s"
        else:
            duration_display = f"{minutes}m {seconds}s"
        
        # Calculate time efficiency
        total_allocated_time = exam.total_duration() * 60  # in seconds
        time_taken = duration.total_seconds()
        if total_allocated_time > 0:
            time_efficiency = min(100, (total_allocated_time / time_taken) * 100)
    
    # Generate performance analysis
    strengths = []
    weaknesses = []
    
    for sa in section_attempts:
        percentage = sa.percentage
        if percentage >= 80:
            strengths.append(f"Excellent performance in {sa.section.display_name}")
        elif percentage >= 60:
            strengths.append(f"Good understanding of {sa.section.display_name}")
        elif percentage < 40:
            weaknesses.append(f"Need more practice in {sa.section.display_name}")
        elif percentage < 60:
            weaknesses.append(f"Room for improvement in {sa.section.display_name}")
    
    # Calculate max total score
    max_total_score = sum(sa.max_possible_score or 0 for sa in section_attempts)
    
    context = {
        'exam': exam,
        'exam_attempt': exam_attempt,
        'section_attempts': section_attempts,
        'duration_display': duration_display,
        'time_efficiency': time_efficiency,
        'max_total_score': max_total_score,
        'strengths': strengths,
        'weaknesses': weaknesses,
    }
    return render(request, 'exams/results.html', context)


@csrf_exempt
@login_required
def check_time_remaining(request, exam_id):
    """API endpoint to check remaining time for current section"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    exam = get_object_or_404(MockExam, id=exam_id, is_active=True)
    exam_attempt = ExamAttempt.objects.filter(
        user=request.user,
        exam=exam,
        status='in_progress'
    ).first()
    
    if not exam_attempt or not exam_attempt.current_section:
        return JsonResponse({'error': 'No active exam or section'}, status=400)
    
    section_attempt = SectionAttempt.objects.filter(
        exam_attempt=exam_attempt,
        section=exam_attempt.current_section
    ).first()
    
    if not section_attempt or not section_attempt.start_time:
        return JsonResponse({'error': 'Section not started'}, status=400)
    
    # Calculate time remaining
    elapsed = timezone.now() - section_attempt.start_time
    total_time = timedelta(minutes=exam_attempt.current_section.duration_minutes)
    remaining = total_time - elapsed
    time_remaining = max(0, int(remaining.total_seconds()))
    
    return JsonResponse({
        'time_remaining': time_remaining,
        'section_name': exam_attempt.current_section.display_name,
        'auto_submit': time_remaining <= 0,
    })


@login_required
def auto_save_progress(request):
    """Enhanced auto-save endpoint with better error handling"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Get current exam attempt
        exam_attempt = ExamAttempt.objects.filter(
            user=request.user,
            status='in_progress'
        ).first()
        
        if not exam_attempt:
            return JsonResponse({'error': 'No active exam'}, status=400)
        
        # Update last activity timestamp
        exam_attempt.last_activity = timezone.now()
        exam_attempt.save()
        
        # Save current question index and section progress
        if 'current_question_index' in data:
            section_attempt = SectionAttempt.objects.filter(
                exam_attempt=exam_attempt,
                section=exam_attempt.current_section,
                is_completed=False
            ).first()
            
            if section_attempt:
                section_attempt.current_question_index = data['current_question_index']
                section_attempt.save()
        
        # Save any pending answers
        saved_answers = 0
        if 'answers' in data:
            for answer_data in data['answers']:
                question_id = answer_data.get('question_id')
                option_id = answer_data.get('option_id')
                
                if question_id and option_id:
                    try:
                        question = Question.objects.get(id=question_id, is_active=True)
                        option = QuestionOption.objects.get(id=option_id, question=question)
                        
                        section_attempt = SectionAttempt.objects.filter(
                            exam_attempt=exam_attempt,
                            section=question.section
                        ).first()
                        
                        if section_attempt:
                            UserAnswer.objects.update_or_create(
                                section_attempt=section_attempt,
                                question=question,
                                defaults={'selected_option': option}
                            )
                            saved_answers += 1
                    except (Question.DoesNotExist, QuestionOption.DoesNotExist):
                        continue
        
        return JsonResponse({
            'success': True,
            'saved_answers': saved_answers,
            'timestamp': timezone.now().isoformat(),
            'session_valid': True
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def recover_session(request, exam_id):
    """Recover interrupted exam session"""
    exam = get_object_or_404(MockExam, id=exam_id, is_active=True)
    
    # Find interrupted exam attempt
    exam_attempt = ExamAttempt.objects.filter(
        user=request.user,
        exam=exam,
        status='in_progress'
    ).first()
    
    if not exam_attempt:
        messages.error(request, 'No interrupted session found.')
        return redirect('exams:exam_list')
    
    # Check if session is still valid (within reasonable time limit)
    if exam_attempt.last_activity:
        time_since_activity = timezone.now() - exam_attempt.last_activity
        if time_since_activity.total_seconds() > 3600:  # 1 hour timeout
            exam_attempt.status = 'abandoned'
            exam_attempt.save()
            messages.warning(request, 'Session expired. Please start a new exam.')
            return redirect('exams:exam_list')
    
    # Get current section attempt
    current_section_attempt = SectionAttempt.objects.filter(
        exam_attempt=exam_attempt,
        section=exam_attempt.current_section,
        is_completed=False
    ).first()
    
    if current_section_attempt:
        # Check if section time has expired
        if current_section_attempt.start_time:
            elapsed = timezone.now() - current_section_attempt.start_time
            section_duration = timedelta(minutes=exam_attempt.current_section.duration_minutes)
            
            if elapsed >= section_duration:
                # Auto-submit expired section
                calculate_section_score(current_section_attempt)
                current_section_attempt.is_completed = True
                current_section_attempt.end_time = timezone.now()
                current_section_attempt.save()
                
                # Move to next section or finish exam
                next_section = get_next_section(exam_attempt)
                if next_section:
                    exam_attempt.current_section = next_section
                    exam_attempt.save()
                    messages.warning(request, f'Previous section time expired. Starting {next_section.display_name}.')
                else:
                    finish_exam(exam_attempt)
                    messages.info(request, 'Exam completed. All sections finished.')
                    return redirect('exams:results', exam_id=exam.id)
    
    messages.success(request, 'Session recovered successfully. Continuing from where you left off.')
    return redirect('exams:take_exam', exam_id=exam.id)


@login_required
def get_session_status(request, exam_id):
    """Get current session status and progress"""
    exam = get_object_or_404(MockExam, id=exam_id, is_active=True)
    
    exam_attempt = ExamAttempt.objects.filter(
        user=request.user,
        exam=exam,
        status='in_progress'
    ).first()
    
    if not exam_attempt:
        return JsonResponse({'session_exists': False})
    
    # Get progress information
    total_sections = exam.sections.filter(is_active=True).count()
    completed_sections = SectionAttempt.objects.filter(
        exam_attempt=exam_attempt,
        is_completed=True
    ).count()
    
    current_section_attempt = None
    current_progress = 0
    
    if exam_attempt.current_section:
        current_section_attempt = SectionAttempt.objects.filter(
            exam_attempt=exam_attempt,
            section=exam_attempt.current_section,
            is_completed=False
        ).first()
        
        if current_section_attempt:
            # Calculate progress in current section
            total_questions = exam_attempt.current_section.questions.filter(is_active=True).count()
            answered_questions = UserAnswer.objects.filter(
                section_attempt=current_section_attempt
            ).count()
            
            if total_questions > 0:
                current_progress = (answered_questions / total_questions) * 100
    
    return JsonResponse({
        'session_exists': True,
        'exam_name': exam.name,
        'current_section': exam_attempt.current_section.display_name if exam_attempt.current_section else None,
        'total_sections': total_sections,
        'completed_sections': completed_sections,
        'current_section_progress': current_progress,
        'last_activity': exam_attempt.last_activity.isoformat() if exam_attempt.last_activity else None,
        'can_resume': True
    })

def get_next_section(exam_attempt):
    """Helper function to get the next section"""
    exam_sections = list(exam_attempt.exam.sections.filter(is_active=True).order_by('name'))
    completed_sections = SectionAttempt.objects.filter(
        exam_attempt=exam_attempt,
        is_completed=True
    ).values_list('section_id', flat=True)
    
    for section in exam_sections:
        if section.id not in completed_sections:
            return section
    return None
