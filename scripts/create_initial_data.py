#!/usr/bin/env python
"""
Script to create initial exam sections and sample questions
Run this after migrations: python manage.py shell < scripts/create_initial_data.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uas_exam.settings')
django.setup()

from exams.models import ExamSection, Question, QuestionOption, MockExam, ExamConfiguration


def create_exam_sections():
    """Create the 6 standard UAS exam sections"""
    sections_data = [
        {
            'name': 'reasoning',
            'display_name': 'Reasoning Skills',
            'duration_minutes': 25,
            'max_score': 20,
            'min_pass_score': 0.1,
            'instructions': 'This section assesses your logical reasoning and problem-solving skills. You have 25 minutes to complete this section. Wrong answers will result in negative marking.'
        },
        {
            'name': 'english',
            'display_name': 'English Language Skills',
            'duration_minutes': 20,
            'max_score': 20,
            'min_pass_score': 3.0,
            'instructions': 'This section assesses your English reading comprehension and language skills. You have 20 minutes to complete this section. Wrong answers will result in negative marking.'
        },
        {
            'name': 'mathematical',
            'display_name': 'Mathematical Skills',
            'duration_minutes': 25,
            'max_score': 20,
            'min_pass_score': 0.1,
            'instructions': 'This section assesses your basic mathematical skills including calculations, percentages, equations, and geometry. You have 25 minutes and can use the built-in calculator. Wrong answers will result in negative marking.'
        },
        {
            'name': 'advanced_math',
            'display_name': 'Advanced Mathematical Skills',
            'duration_minutes': 30,
            'max_score': 20,
            'min_pass_score': 1.0,
            'instructions': 'This section assesses advanced mathematics and physics concepts. You have 30 minutes and can use the built-in calculator. Wrong answers will result in negative marking.'
        },
        {
            'name': 'ethical',
            'display_name': 'Ethical Skills',
            'duration_minutes': 10,
            'max_score': 20,
            'min_pass_score': 1.0,
            'instructions': 'This section assesses your ability to recognize ethical issues and make ethical decisions. You have 10 minutes to complete this section. Wrong answers will result in negative marking.'
        },
        {
            'name': 'emotional',
            'display_name': 'Emotional Intelligence Skills',
            'duration_minutes': 10,
            'max_score': 20,
            'min_pass_score': 1.0,
            'instructions': 'This section assesses your emotional intelligence and ability to understand and manage emotions. You have 10 minutes to complete this section. Wrong answers will result in negative marking.'
        }
    ]
    
    created_sections = []
    for section_data in sections_data:
        section, created = ExamSection.objects.get_or_create(
            name=section_data['name'],
            defaults=section_data
        )
        if created:
            print(f"Created section: {section.display_name}")
        else:
            print(f"Section already exists: {section.display_name}")
        created_sections.append(section)
    
    return created_sections


def create_sample_questions():
    """Create sample questions for each section"""
    
    # Sample questions for Reasoning Skills
    reasoning_section = ExamSection.objects.get(name='reasoning')
    
    reasoning_questions = [
        {
            'question_text': 'If all roses are flowers and some flowers are red, which of the following must be true?',
            'options': [
                ('A', 'All roses are red', False),
                ('B', 'Some roses are red', False),
                ('C', 'All flowers are roses', False),
                ('D', 'Some flowers are roses', True)
            ]
        },
        {
            'question_text': 'In a sequence: 2, 6, 18, 54, ... What is the next number?',
            'options': [
                ('A', '108', False),
                ('B', '162', True),
                ('C', '216', False),
                ('D', '324', False)
            ]
        }
    ]
    
    # Sample questions for English Language Skills
    english_section = ExamSection.objects.get(name='english')
    
    english_questions = [
        {
            'question_text': 'Choose the word that best completes the sentence: "The research findings were _______ with previous studies."',
            'options': [
                ('A', 'consistent', True),
                ('B', 'resistant', False),
                ('C', 'persistent', False),
                ('D', 'insistent', False)
            ]
        },
        {
            'question_text': 'What is the main idea of this passage: "Climate change represents one of the most significant challenges of our time, requiring immediate action from governments, businesses, and individuals worldwide."',
            'options': [
                ('A', 'Climate change affects only governments', False),
                ('B', 'Climate change is a major global challenge requiring collective action', True),
                ('C', 'Only businesses can solve climate change', False),
                ('D', 'Climate change is not urgent', False)
            ]
        }
    ]
    
    # Sample questions for Mathematical Skills
    math_section = ExamSection.objects.get(name='mathematical')
    
    math_questions = [
        {
            'question_text': 'If 25% of a number is 45, what is the number?',
            'options': [
                ('A', '180', True),
                ('B', '135', False),
                ('C', '225', False),
                ('D', '160', False)
            ]
        },
        {
            'question_text': 'What is the area of a rectangle with length 12 cm and width 8 cm?',
            'options': [
                ('A', '40 cm²', False),
                ('B', '96 cm²', True),
                ('C', '20 cm²', False),
                ('D', '48 cm²', False)
            ]
        }
    ]
    
    # Create questions for each section
    sections_questions = [
        (reasoning_section, reasoning_questions),
        (english_section, english_questions),
        (math_section, math_questions)
    ]
    
    for section, questions in sections_questions:
        for q_data in questions:
            question = Question.objects.create(
                section=section,
                question_text=q_data['question_text'],
                difficulty='medium',
                points=1,
                negative_points=0.25
            )
            
            for option_letter, option_text, is_correct in q_data['options']:
                QuestionOption.objects.create(
                    question=question,
                    option_letter=option_letter,
                    option_text=option_text,
                    is_correct=is_correct
                )
            
            print(f"Created question for {section.display_name}: {q_data['question_text'][:50]}...")


def create_mock_exam():
    """Create a complete mock exam with all sections"""
    sections = ExamSection.objects.filter(is_active=True)
    
    mock_exam, created = MockExam.objects.get_or_create(
        name="International UAS Mock Exam",
        defaults={
            'description': 'Complete mock examination covering all 6 sections of the International UAS entrance exam.'
        }
    )
    
    if created:
        mock_exam.sections.set(sections)
        print(f"Created mock exam: {mock_exam.name}")
    else:
        print(f"Mock exam already exists: {mock_exam.name}")


def create_exam_configuration():
    """Create default exam configuration"""
    config, created = ExamConfiguration.objects.get_or_create(
        id=1,
        defaults={
            'exam_instructions': '''
Welcome to the International UAS Mock Exam System.

IMPORTANT INSTRUCTIONS:
1. This exam consists of 6 sections with specific time limits for each section.
2. You can complete sections in any order, but once started, a section must be completed.
3. Wrong answers result in negative marking (penalty scores).
4. You can leave questions unanswered to avoid negative points.
5. Your progress is automatically saved every 30 seconds.
6. Ensure stable internet connection throughout the exam.

Good luck with your preparation!
            ''',
            'negative_marking_info': '''
NEGATIVE MARKING POLICY:
- Correct answer: +1 point
- Wrong answer: -0.25 points  
- Unanswered: 0 points

Choose your answers carefully to avoid penalty points.
            ''',
            'technical_requirements': '''
TECHNICAL REQUIREMENTS:
- Stable internet connection
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Quiet environment for concentration
- Ensure your device is fully charged or connected to power
- Close all other applications and browser tabs
            ''',
            'auto_save_interval': 30,
            'allow_section_navigation': False,
            'show_results_immediately': True
        }
    )
    
    if created:
        print("Created exam configuration")
    else:
        print("Exam configuration already exists")


def main():
    """Run all initialization functions"""
    print("Creating initial exam data...")
    
    # Create exam sections
    sections = create_exam_sections()
    
    # Create sample questions
    create_sample_questions()
    
    # Create mock exam
    create_mock_exam()
    
    # Create exam configuration
    create_exam_configuration()
    
    print("\nInitial data creation completed!")
    print(f"Created {ExamSection.objects.count()} exam sections")
    print(f"Created {Question.objects.count()} sample questions")
    print(f"Created {MockExam.objects.count()} mock exam(s)")


if __name__ == '__main__':
    main()
