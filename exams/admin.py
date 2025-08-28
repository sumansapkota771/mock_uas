from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from .models import (
    ExamSection, Question, QuestionOption, MockExam, 
    ExamAttempt, SectionAttempt, UserAnswer, ExamConfiguration
)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    max_num = 4
    fields = ['option_letter', 'option_text', 'is_correct']


@admin.register(ExamSection)
class ExamSectionAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'duration_minutes', 'max_score', 'min_pass_score', 'has_negative_marking', 'is_active', 'question_count']
    list_filter = ['has_negative_marking', 'is_active', 'name']
    search_fields = ['display_name', 'name']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'is_active')
        }),
        ('Scoring Configuration', {
            'fields': ('duration_minutes', 'max_score', 'min_pass_score', 'has_negative_marking')
        }),
        ('Instructions', {
            'fields': ('instructions',),
            'classes': ('collapse',)
        }),
    )
    
    def question_count(self, obj):
        count = obj.questions.filter(is_active=True).count()
        url = reverse('admin:exams_question_changelist') + f'?section__id__exact={obj.id}'
        return format_html('<a href="{}">{} questions</a>', url, count)
    question_count.short_description = 'Active Questions'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'section', 'difficulty', 'points', 'negative_points', 'is_active', 'created_at']
    list_filter = ['section', 'difficulty', 'is_active', 'created_at']
    search_fields = ['question_text']
    ordering = ['section', '-created_at']
    inlines = [QuestionOptionInline]
    
    fieldsets = (
        ('Question Details', {
            'fields': ('section', 'question_text', 'difficulty', 'is_active')
        }),
        ('Scoring', {
            'fields': ('points', 'negative_points')
        }),
        ('Additional Information', {
            'fields': ('explanation', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def question_preview(self, obj):
        preview = obj.question_text[:100] + "..." if len(obj.question_text) > 100 else obj.question_text
        return preview
    question_preview.short_description = 'Question'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new question
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MockExam)
class MockExamAdmin(admin.ModelAdmin):
    list_display = ['name', 'sections_list', 'total_duration_display', 'is_active', 'attempt_count', 'created_at']
    list_filter = ['is_active', 'created_at', 'sections']
    search_fields = ['name', 'description']
    filter_horizontal = ['sections']
    
    def sections_list(self, obj):
        return ", ".join([section.display_name for section in obj.sections.all()])
    sections_list.short_description = 'Sections'
    
    def total_duration_display(self, obj):
        return f"{obj.total_duration()} minutes"
    total_duration_display.short_description = 'Total Duration'
    
    def attempt_count(self, obj):
        count = obj.examattempt_set.count()
        url = reverse('admin:exams_examattempt_changelist') + f'?exam__id__exact={obj.id}'
        return format_html('<a href="{}">{} attempts</a>', url, count)
    attempt_count.short_description = 'Attempts'


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'exam', 'status', 'total_score', 'percentage_score', 'passed', 'start_time', 'duration_display']
    list_filter = ['status', 'passed', 'exam', 'start_time']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'exam__name']
    readonly_fields = ['created_at', 'duration_display', 'section_attempts_summary']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Exam Information', {
            'fields': ('user', 'exam', 'status', 'current_section')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'duration_display', 'created_at')
        }),
        ('Results', {
            'fields': ('total_score', 'percentage_score', 'passed')
        }),
        ('Section Details', {
            'fields': ('section_attempts_summary',),
            'classes': ('collapse',)
        }),
    )
    
    def duration_display(self, obj):
        duration = obj.duration_taken()
        if duration:
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            else:
                return f"{minutes}m {seconds}s"
        return "Not completed"
    duration_display.short_description = 'Duration'
    
    def section_attempts_summary(self, obj):
        attempts = obj.section_attempts.all()
        if not attempts:
            return "No section attempts yet"
        
        html = "<table style='width:100%; border-collapse: collapse;'>"
        html += "<tr style='background-color: #f0f0f0;'><th>Section</th><th>Score</th><th>Questions Correct</th><th>Completed</th></tr>"
        
        for attempt in attempts:
            html += f"<tr>"
            html += f"<td>{attempt.section.display_name}</td>"
            html += f"<td>{attempt.score or 'N/A'}/{attempt.max_possible_score or 'N/A'}</td>"
            html += f"<td>{attempt.questions_correct}/{attempt.questions_answered}</td>"
            html += f"<td>{'Yes' if attempt.is_completed else 'No'}</td>"
            html += f"</tr>"
        
        html += "</table>"
        return mark_safe(html)
    section_attempts_summary.short_description = 'Section Performance'


@admin.register(SectionAttempt)
class SectionAttemptAdmin(admin.ModelAdmin):
    list_display = ['user_display', 'section', 'score_display', 'questions_correct', 'questions_answered', 'is_completed', 'start_time']
    list_filter = ['section', 'is_completed', 'start_time']
    search_fields = ['exam_attempt__user__username', 'section__display_name']
    readonly_fields = ['answers_summary']
    
    def user_display(self, obj):
        return obj.exam_attempt.user.username
    user_display.short_description = 'User'
    
    def score_display(self, obj):
        if obj.score is not None and obj.max_possible_score is not None:
            percentage = (obj.score / obj.max_possible_score) * 100 if obj.max_possible_score > 0 else 0
            return f"{obj.score}/{obj.max_possible_score} ({percentage:.1f}%)"
        return "Not calculated"
    score_display.short_description = 'Score'
    
    def answers_summary(self, obj):
        answers = obj.answers.all()
        if not answers:
            return "No answers recorded"
        
        html = "<table style='width:100%; border-collapse: collapse;'>"
        html += "<tr style='background-color: #f0f0f0;'><th>Question</th><th>Selected</th><th>Correct</th><th>Points</th></tr>"
        
        for answer in answers:
            html += f"<tr>"
            html += f"<td>Q{answer.question.id}</td>"
            html += f"<td>{answer.selected_option.option_letter if answer.selected_option else 'Not answered'}</td>"
            html += f"<td>{'✓' if answer.is_correct else '✗' if answer.is_correct is not None else '-'}</td>"
            html += f"<td>{answer.points_earned}</td>"
            html += f"</tr>"
        
        html += "</table>"
        return mark_safe(html)
    answers_summary.short_description = 'Answer Details'


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['user_display', 'question_display', 'selected_option', 'is_correct', 'points_earned', 'answered_at']
    list_filter = ['is_correct', 'answered_at', 'question__section']
    search_fields = ['section_attempt__exam_attempt__user__username', 'question__question_text']
    
    def user_display(self, obj):
        return obj.section_attempt.exam_attempt.user.username
    user_display.short_description = 'User'
    
    def question_display(self, obj):
        return f"Q{obj.question.id} ({obj.question.section.display_name})"
    question_display.short_description = 'Question'


@admin.register(ExamConfiguration)
class ExamConfigurationAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'auto_save_interval', 'allow_section_navigation', 'show_results_immediately', 'updated_at']
    
    fieldsets = (
        ('Instructions', {
            'fields': ('exam_instructions', 'negative_marking_info', 'technical_requirements')
        }),
        ('Behavior Settings', {
            'fields': ('auto_save_interval', 'allow_section_navigation', 'show_results_immediately')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one configuration instance
        return not ExamConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of configuration
        return False


# Customize admin site header and title
admin.site.site_header = "UAS Mock Exam Administration"
admin.site.site_title = "UAS Exam Admin"
admin.site.index_title = "Welcome to UAS Mock Exam Administration"
