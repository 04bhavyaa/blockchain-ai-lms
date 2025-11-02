from django.contrib import admin
from .models import (
    LessonProgress, QuizAttempt, QuestionResponse,
    ModuleProgress, CourseProgress, ProgressSnapshot
)

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson_title', 'status', 'video_watched_percentage', 'completed_at', 'tokens_earned', 'blockchain_event_tx_hash']
    list_filter = ['status', 'completed_at']
    search_fields = ['user__email', 'lesson_title']
    readonly_fields = ['started_at', 'completed_at', 'blockchain_event_tx_hash', 'last_blockchain_status']

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz_title', 'attempt_number', 'percentage_score', 'is_passed', 'tokens_earned', 'blockchain_event_tx_hash']
    list_filter = ['is_passed', 'completed_at']
    search_fields = ['user__email', 'quiz_title']
    readonly_fields = ['started_at', 'completed_at', 'blockchain_event_tx_hash', 'last_blockchain_status']

@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    list_display = ['question_id', 'question_type', 'is_correct', 'points_earned']
    list_filter = ['is_correct', 'question_type']

@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'module_title', 'completion_percentage', 'average_quiz_score', 'tokens_earned', 'blockchain_event_tx_hash']
    list_filter = ['completion_percentage']
    search_fields = ['user__email', 'module_title']
    readonly_fields = ['updated_at', 'blockchain_event_tx_hash', 'last_blockchain_status']

@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_title', 'status', 'completion_percentage', 'certificate_issued', 'tokens_earned', 'blockchain_event_tx_hash']
    list_filter = ['status', 'certificate_issued']
    search_fields = ['user__email', 'course_title']
    readonly_fields = ['enrolled_at', 'updated_at', 'certificate_issued_at', 'blockchain_event_tx_hash', 'last_blockchain_status']

@admin.register(ProgressSnapshot)
class ProgressSnapshotAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_id', 'completion_percentage', 'snapshot_date', 'tokens_earned', 'blockchain_event_tx_hash']
    list_filter = ['snapshot_date']
    search_fields = ['user__email']
    readonly_fields = ['snapshot_date', 'blockchain_event_tx_hash', 'last_blockchain_status']
