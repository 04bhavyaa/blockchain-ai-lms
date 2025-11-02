from django.contrib import admin
from .models import (
    CourseCategory, Course, Module, Lesson, Quiz, Question, Answer,
    Enrollment, CourseRating, Bookmark
)

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'instructor', 'access_type', 'status',
        'total_enrollments', 'blockchain_unlock_callback', 'certificate_mint_callback'
    ]
    list_filter = [
        'status', 'access_type', 'category', 'created_at'
    ]
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'total_enrollments', 'average_rating', 'total_ratings',
        'created_at', 'updated_at', 'blockchain_unlock_callback',
        'certificate_mint_callback', 'last_blockchain_event'
    ]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']
    search_fields = ['title']
    ordering = ['course', 'order']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'content_type', 'duration_minutes', 'order']
    list_filter = ['content_type', 'module__course']
    search_fields = ['title']
    ordering = ['module', 'order']

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'passing_score', 'max_attempts']
    search_fields = ['title']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'question_type', 'points', 'order']
    list_filter = ['question_type']
    ordering = ['quiz', 'order']

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'is_correct', 'order']
    list_filter = ['is_correct']
    ordering = ['question', 'order']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'course', 'status', 'progress_percentage', 'enrolled_at',
        'blockchain_unlock_tx_hash', 'blockchain_certificate_tx_hash'
    ]
    list_filter = ['status', 'enrolled_at']
    search_fields = ['user__email', 'course__title']
    readonly_fields = [
        'enrolled_at', 'blockchain_unlock_tx_hash', 'blockchain_certificate_tx_hash', 'last_blockchain_status'
    ]

@admin.register(CourseRating)
class CourseRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__email', 'course__title']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'course__title']
    readonly_fields = ['created_at']