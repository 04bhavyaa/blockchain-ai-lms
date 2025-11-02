"""
AI Recommendations service serializers
"""

from rest_framework import serializers
from .models import (
    UserPreference, RecommendationFeedback, LearningPath,
    UserCourseInteraction
)


class UserPreferenceSerializer(serializers.ModelSerializer):
    """User preference serializer"""
    
    class Meta:
        model = UserPreference
        fields = [
            'id', 'preferred_categories', 'preferred_difficulty',
            'learning_style', 'courses_completed', 'courses_enrolled',
            'avg_rating_given', 'last_interaction', 'updated_at'
        ]
        read_only_fields = [
            'id', 'courses_completed', 'courses_enrolled',
            'avg_rating_given', 'last_interaction', 'updated_at'
        ]


class UserCourseInteractionSerializer(serializers.ModelSerializer):
    """User course interaction serializer"""
    
    class Meta:
        model = UserCourseInteraction
        fields = [
            'id', 'course_id', 'interaction_type', 'rating',
            'time_spent_minutes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RecommendationFeedbackSerializer(serializers.ModelSerializer):
    """Recommendation feedback serializer"""
    
    class Meta:
        model = RecommendationFeedback
        fields = ['id', 'recommended_course_id', 'feedback_type', 'comments', 'created_at']
        read_only_fields = ['id', 'created_at']


class LearningPathSerializer(serializers.ModelSerializer):
    """Learning path serializer"""
    
    class Meta:
        model = LearningPath
        fields = [
            'id', 'path_name', 'courses_in_path', 'current_course_index',
            'completion_percentage', 'estimated_completion_days', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RecommendationResponseSerializer(serializers.Serializer):
    """Recommendation response serializer"""
    
    course_id = serializers.IntegerField()
    course_name = serializers.CharField()
    category = serializers.CharField()
    difficulty_level = serializers.CharField()
    score = serializers.DecimalField(max_digits=3, decimal_places=2)
    avg_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_enrollments = serializers.IntegerField()
    match_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class SimilarCourseSerializer(serializers.Serializer):
    """Similar courses response serializer"""
    
    course_id = serializers.IntegerField()
    course_name = serializers.CharField()
    similarity_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    category = serializers.CharField()
    avg_rating = serializers.DecimalField(max_digits=3, decimal_places=2)


class TrendingCourseSerializer(serializers.Serializer):
    """Trending courses response serializer"""
    
    course_id = serializers.IntegerField()
    course_name = serializers.CharField()
    total_enrollments = serializers.IntegerField()
    avg_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    trend_score = serializers.DecimalField(max_digits=5, decimal_places=2)
