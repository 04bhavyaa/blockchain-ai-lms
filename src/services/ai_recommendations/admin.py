"""
Django admin configuration for AI Recommendation Service
"""
from django.contrib import admin
from .models import (
    UserPreference, CourseVector, UserCourseInteraction,
    RecommendationCache, LearningPath, RecommendationFeedback
)


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_difficulty', 'learning_style', 'courses_completed', 'updated_at']
    list_filter = ['preferred_difficulty', 'learning_style', 'updated_at']
    search_fields = ['user__email']
    readonly_fields = ['courses_completed', 'courses_enrolled', 'avg_rating_given', 'updated_at']


@admin.register(CourseVector)
class CourseVectorAdmin(admin.ModelAdmin):
    list_display = ['course_id', 'course_name', 'category', 'difficulty_level', 'total_enrollments']
    list_filter = ['category', 'difficulty_level']
    search_fields = ['course_name', 'course_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserCourseInteraction)
class UserCourseInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_id', 'interaction_type', 'rating', 'created_at']
    list_filter = ['interaction_type', 'created_at']
    search_fields = ['user__email', 'course_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(RecommendationCache)
class RecommendationCacheAdmin(admin.ModelAdmin):
    list_display = ['user', 'algorithm_version', 'updated_at', 'expires_at', 'is_expired']
    list_filter = ['algorithm_version', 'updated_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ['user', 'path_name', 'current_course_index', 'completion_percentage', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__email', 'path_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RecommendationFeedback)
class RecommendationFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'recommended_course_id', 'feedback_type', 'created_at']
    list_filter = ['feedback_type', 'created_at']
    search_fields = ['user__email', 'recommended_course_id']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
