from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class ExamSection(models.Model):
    """Represents the 6 different sections of the UAS exam"""
    SECTION_CHOICES = [
        ('reasoning', 'Reasoning Skills'),
        ('english', 'English Language Skills'),
        ('mathematical', 'Mathematical Skills'),
        ('advanced_math', 'Advanced Mathematical Skills'),
        ('ethical', 'Ethical Skills'),
        ('emotional', 'Emotional Intelligence Skills'),
    ]
    
    name = models.CharField(max_length=50, choices=SECTION_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField(help_text="Duration in minutes")
    max_score = models.PositiveIntegerField(default=20)
    min_pass_score = models.FloatField(default=1.0, help_text="Minimum score to pass this section")
    has_negative_marking = models.BooleanField(default=True)
    instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class Question(models.Model):
    """Individual questions for each exam section"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    section = models.ForeignKey(ExamSection, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    points = models.PositiveIntegerField(default=1)
    negative_points = models.FloatField(default=0.25, help_text="Points deducted for wrong answer")
    explanation = models.TextField(blank=True, help_text="Explanation for the correct answer")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['section', 'id']
    
    def __str__(self):
        return f"{self.section.display_name} - Q{self.id}"


class QuestionOption(models.Model):
    """Multiple choice options for each question"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    option_letter = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    
    class Meta:
        ordering = ['option_letter']
        unique_together = ['question', 'option_letter']
    
    def __str__(self):
        return f"{self.question} - Option {self.option_letter}"


class MockExam(models.Model):
    """A complete mock exam instance"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sections = models.ManyToManyField(ExamSection)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def total_duration(self):
        """Calculate total exam duration including transition time"""
        section_time = sum(section.duration_minutes for section in self.sections.all())
        transition_time = 15  # 15 minutes for transitions
        return section_time + transition_time


class ExamAttempt(models.Model):
    """User's attempt at taking a mock exam"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('auto_submitted', 'Auto Submitted'),
        ('terminated', 'Terminated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_attempts')
    exam = models.ForeignKey(MockExam, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    current_section = models.ForeignKey(ExamSection, on_delete=models.SET_NULL, null=True, blank=True)
    total_score = models.FloatField(null=True, blank=True)
    percentage_score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'exam', 'created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.exam.name} ({self.status})"
    
    def duration_taken(self):
        """Calculate time taken for the exam"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return timezone.now() - self.start_time
        return None


class SectionAttempt(models.Model):
    """User's attempt at a specific section within an exam"""
    exam_attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='section_attempts')
    section = models.ForeignKey(ExamSection, on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    max_possible_score = models.PositiveIntegerField(null=True, blank=True)
    questions_answered = models.PositiveIntegerField(default=0)
    questions_correct = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['exam_attempt', 'section']
    
    def __str__(self):
        return f"{self.exam_attempt.user.username} - {self.section.display_name}"


class UserAnswer(models.Model):
    """User's answer to a specific question"""
    section_attempt = models.ForeignKey(SectionAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.FloatField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['section_attempt', 'question']
    
    def __str__(self):
        return f"{self.section_attempt.exam_attempt.user.username} - Q{self.question.id}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate if answer is correct and points earned"""
        if self.selected_option:
            self.is_correct = self.selected_option.is_correct
            if self.is_correct:
                self.points_earned = self.question.points
            else:
                self.points_earned = -self.question.negative_points if self.question.section.has_negative_marking else 0
        super().save(*args, **kwargs)


class ExamConfiguration(models.Model):
    """Global exam configuration settings"""
    exam_instructions = models.TextField(default="Please read all instructions carefully before starting the exam.")
    negative_marking_info = models.TextField(default="Wrong answers will result in negative marking.")
    technical_requirements = models.TextField(default="Ensure stable internet connection and quiet environment.")
    auto_save_interval = models.PositiveIntegerField(default=30, help_text="Auto-save interval in seconds")
    allow_section_navigation = models.BooleanField(default=False, help_text="Allow users to navigate between sections")
    show_results_immediately = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Exam Configuration"
        verbose_name_plural = "Exam Configuration"
    
    def __str__(self):
        return f"Exam Configuration (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
