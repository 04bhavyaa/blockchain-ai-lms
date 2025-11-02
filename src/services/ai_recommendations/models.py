"""
AI Recommendations service models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class UserPreference(models.Model):
    """Store user preferences for recommendation engine"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preference')
    preferred_categories = models.JSONField(
        default=list,
        help_text="List of preferred course categories"
    )
    preferred_difficulty = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        null=True,
        blank=True
    )
    learning_style = models.CharField(
        max_length=50,
        choices=[
            ('video', 'Video Lectures'),
            ('text', 'Text-based'),
            ('interactive', 'Interactive'),
            ('project_based', 'Project-based'),
        ],
        default='video'
    )
    avg_rating_given = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    courses_completed = models.IntegerField(default=0)
    courses_enrolled = models.IntegerField(default=0)
    total_ratings_given = models.IntegerField(default=0)
    last_interaction = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"


class CourseVector(models.Model):
    """Store course feature vectors for content-based filtering"""
    
    course_id = models.IntegerField(unique=True)
    course_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    difficulty_level = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')]
    )
    tags = models.JSONField(default=list, help_text="List of course tags")
    
    # Feature vector for cosine similarity (normalized)
    feature_vector = models.JSONField(
        default=dict,
        help_text="Feature vector for content-based filtering"
    )
    
    # Popularity metrics
    total_enrollments = models.IntegerField(default=0)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    completion_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_vectors'
    
    def __str__(self):
        return self.course_name


class UserCourseInteraction(models.Model):
    """Track user-course interactions for collaborative filtering"""
    
    INTERACTION_TYPES = [
        ('view', 'Viewed'),
        ('enroll', 'Enrolled'),
        ('complete', 'Completed'),
        ('rate', 'Rated'),
        ('bookmark', 'Bookmarked'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_interactions')
    course_id = models.IntegerField()
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    interaction_strength = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0,
        help_text="Weight of interaction (0-1)"
    )
    time_spent_minutes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_course_interactions'
        unique_together = ['user', 'course_id', 'interaction_type']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['course_id', '-updated_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - Course {self.course_id} ({self.interaction_type})"


class RecommendationCache(models.Model):
    """Cache recommendations for faster retrieval"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recommendation_cache')
    recommendations = models.JSONField(
        default=list,
        help_text="List of recommended courses with scores"
    )
    algorithm_version = models.CharField(max_length=50, default='v1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(help_text="Cache expiration time")
    
    class Meta:
        db_table = 'recommendation_cache'
    
    def __str__(self):
        return f"Cache for {self.user.email}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class LearningPath(models.Model):
    """Personalized learning path for users"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='learning_path')
    path_name = models.CharField(max_length=255)
    courses_in_path = models.JSONField(
        default=list,
        help_text="Ordered list of course IDs in learning path"
    )
    current_course_index = models.IntegerField(default=0)
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    estimated_completion_days = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_paths'
    
    def __str__(self):
        return f"Learning Path: {self.path_name} ({self.user.email})"


class RecommendationFeedback(models.Model):
    """User feedback on recommendations for improvement"""
    
    FEEDBACK_TYPES = [
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
        ('already_taken', 'Already Taken'),
        ('not_interested', 'Not Interested'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_feedback')
    recommended_course_id = models.IntegerField()
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    comments = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recommendation_feedback'
        unique_together = ['user', 'recommended_course_id']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - Course {self.recommended_course_id} ({self.feedback_type})"
