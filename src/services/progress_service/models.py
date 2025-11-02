"""
Progress Service Models - Track user learning progress
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class LessonProgress(models.Model):
    """Track lesson completion status and progress"""
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson_id = models.IntegerField()
    lesson_title = models.CharField(max_length=255)
    course_id = models.IntegerField()
    module_id = models.IntegerField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    # Progress metrics
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Video/content metrics
    video_watched_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of video watched (0-100)"
    )
    
    # Resources accessed
    resources_downloaded = models.IntegerField(default=0)
    
    # Token reward
    tokens_earned = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'lesson_progress'
        unique_together = ['user', 'lesson_id']
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', 'course_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.lesson_title}"


class QuizAttempt(models.Model):
    """Track individual quiz attempts"""
    
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('submitted', 'Submitted'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    lesson_id = models.IntegerField()
    quiz_id = models.IntegerField()
    quiz_title = models.CharField(max_length=255)
    course_id = models.IntegerField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    # Scoring
    total_points = models.IntegerField(default=0)
    points_earned = models.IntegerField(default=0)
    percentage_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Pass/Fail
    passing_score = models.IntegerField(default=70)
    is_passed = models.BooleanField(default=False)
    
    # Time tracking
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.IntegerField(default=0)
    
    # Attempt number
    attempt_number = models.IntegerField(default=1)
    
    # Token reward
    tokens_earned = models.IntegerField(default=0)
    
    # Responses
    responses = models.JSONField(
        default=dict,
        help_text="User answers to questions {question_id: answer}"
    )
    
    class Meta:
        db_table = 'quiz_attempts'
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', 'quiz_id']),
            models.Index(fields=['is_passed']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.quiz_title} (Attempt {self.attempt_number})"


class QuestionResponse(models.Model):
    """Store individual question responses"""
    
    quiz_attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='question_responses'
    )
    question_id = models.IntegerField()
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=50,
        choices=[
            ('multiple_choice', 'Multiple Choice'),
            ('true_false', 'True/False'),
            ('short_answer', 'Short Answer'),
            ('essay', 'Essay'),
        ]
    )
    
    # User's response
    user_response = models.TextField()
    
    # Scoring
    points_possible = models.IntegerField(default=1)
    points_earned = models.IntegerField(default=0)
    is_correct = models.BooleanField(default=False)
    
    # Feedback
    feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'question_responses'
        ordering = ['question_id']
    
    def __str__(self):
        return f"Q{self.question_id} - {self.quiz_attempt.user.email}"


class ModuleProgress(models.Model):
    """Track module-level progress"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='module_progress')
    module_id = models.IntegerField()
    module_title = models.CharField(max_length=255)
    course_id = models.IntegerField()
    
    # Progress metrics
    total_lessons = models.IntegerField(default=0)
    lessons_completed = models.IntegerField(default=0)
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Assessment
    total_quizzes = models.IntegerField(default=0)
    quizzes_passed = models.IntegerField(default=0)
    average_quiz_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_time_minutes = models.IntegerField(default=0)
    
    # Tokens
    tokens_earned = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'module_progress'
        unique_together = ['user', 'module_id']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.module_title}"


class CourseProgress(models.Model):
    """Track course-level progress"""
    
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_progress')
    course_id = models.IntegerField()
    course_title = models.CharField(max_length=255)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    
    # Progress metrics
    total_modules = models.IntegerField(default=0)
    modules_completed = models.IntegerField(default=0)
    
    total_lessons = models.IntegerField(default=0)
    lessons_completed = models.IntegerField(default=0)
    
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Assessment metrics
    total_quizzes = models.IntegerField(default=0)
    quizzes_passed = models.IntegerField(default=0)
    average_quiz_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Timing
    enrolled_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_time_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Tokens earned
    tokens_earned = models.IntegerField(default=0)
    
    # Certificate
    certificate_issued = models.BooleanField(default=False)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_progress'
        unique_together = ['user', 'course_id']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['completion_percentage']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.course_title}"


class ProgressSnapshot(models.Model):
    """Daily/weekly snapshots of progress (for analytics)"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_snapshots')
    course_id = models.IntegerField()
    
    # Snapshot data
    lessons_completed = models.IntegerField(default=0)
    quizzes_passed = models.IntegerField(default=0)
    average_quiz_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_time_minutes = models.IntegerField(default=0)
    tokens_earned = models.IntegerField(default=0)
    
    snapshot_date = models.DateField(auto_now_add=True)
    
    class Meta:
        db_table = 'progress_snapshots'
        unique_together = ['user', 'course_id', 'snapshot_date']
        ordering = ['-snapshot_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.snapshot_date}"
