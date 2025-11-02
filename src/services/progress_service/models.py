from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()

class LessonProgress(models.Model):
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
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    video_watched_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Percentage of video watched (0-100)")
    resources_downloaded = models.IntegerField(default=0)
    tokens_earned = models.IntegerField(default=0)
    # Blockchain callback/log integration
    blockchain_event_tx_hash = models.CharField(max_length=255, null=True, blank=True)
    last_blockchain_status = models.TextField(blank=True)
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
    total_points = models.IntegerField(default=0)
    points_earned = models.IntegerField(default=0)
    percentage_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    passing_score = models.IntegerField(default=70)
    is_passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.IntegerField(default=0)
    attempt_number = models.IntegerField(default=1)
    tokens_earned = models.IntegerField(default=0)
    responses = models.JSONField(default=dict, help_text="User answers to questions {question_id: answer}")
    blockchain_event_tx_hash = models.CharField(max_length=255, null=True, blank=True)
    last_blockchain_status = models.TextField(blank=True)
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
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='question_responses')
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
    user_response = models.TextField()
    points_possible = models.IntegerField(default=1)
    points_earned = models.IntegerField(default=0)
    is_correct = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'question_responses'
        ordering = ['question_id']
    def __str__(self):
        return f"Q{self.question_id} - {self.quiz_attempt.user.email}"

class ModuleProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='module_progress')
    module_id = models.IntegerField()
    module_title = models.CharField(max_length=255)
    course_id = models.IntegerField()
    total_lessons = models.IntegerField(default=0)
    lessons_completed = models.IntegerField(default=0)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    total_quizzes = models.IntegerField(default=0)
    quizzes_passed = models.IntegerField(default=0)
    average_quiz_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_time_minutes = models.IntegerField(default=0)
    tokens_earned = models.IntegerField(default=0)
    blockchain_event_tx_hash = models.CharField(max_length=255, null=True, blank=True)
    last_blockchain_status = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'module_progress'
        unique_together = ['user', 'module_id']
        ordering = ['-updated_at']
    def __str__(self):
        return f"{self.user.email} - {self.module_title}"

class CourseProgress(models.Model):
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
    total_modules = models.IntegerField(default=0)
    modules_completed = models.IntegerField(default=0)
    total_lessons = models.IntegerField(default=0)
    lessons_completed = models.IntegerField(default=0)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    total_quizzes = models.IntegerField(default=0)
    quizzes_passed = models.IntegerField(default=0)
    average_quiz_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    enrolled_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_time_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tokens_earned = models.IntegerField(default=0)
    certificate_issued = models.BooleanField(default=False)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    blockchain_event_tx_hash = models.CharField(max_length=255, null=True, blank=True)
    last_blockchain_status = models.TextField(blank=True)
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_snapshots')
    course_id = models.IntegerField()
    lessons_completed = models.IntegerField(default=0)
    quizzes_passed = models.IntegerField(default=0)
    average_quiz_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_time_minutes = models.IntegerField(default=0)
    tokens_earned = models.IntegerField(default=0)
    snapshot_date = models.DateField(auto_now_add=True)
    blockchain_event_tx_hash = models.CharField(max_length=255, null=True, blank=True)
    last_blockchain_status = models.TextField(blank=True)
    class Meta:
        db_table = 'progress_snapshots'
        unique_together = ['user', 'course_id', 'snapshot_date']
        ordering = ['-snapshot_date']
    def __str__(self):
        return f"{self.user.email} - {self.snapshot_date}"
