"""
Progress service serializers
"""

from rest_framework import serializers
from .models import (
    LessonProgress, QuizAttempt, QuestionResponse,
    ModuleProgress, CourseProgress, ProgressSnapshot
)


class LessonProgressSerializer(serializers.ModelSerializer):
    """Lesson progress serializer"""
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'lesson_id', 'lesson_title', 'status', 'video_watched_percentage',
            'time_spent_minutes', 'tokens_earned', 'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at']


class QuestionResponseSerializer(serializers.ModelSerializer):
    """Individual question response serializer"""
    
    class Meta:
        model = QuestionResponse
        fields = [
            'id', 'question_id', 'question_text', 'question_type',
            'user_response', 'is_correct', 'points_earned', 'feedback'
        ]
        read_only_fields = ['id', 'is_correct', 'points_earned', 'feedback']


class QuizAttemptSerializer(serializers.ModelSerializer):
    """Quiz attempt serializer"""
    
    question_responses = QuestionResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz_id', 'quiz_title', 'attempt_number', 'status',
            'total_points', 'points_earned', 'percentage_score', 'is_passed',
            'time_spent_minutes', 'tokens_earned', 'started_at', 'completed_at',
            'question_responses'
        ]
        read_only_fields = [
            'id', 'percentage_score', 'is_passed', 'tokens_earned',
            'started_at', 'completed_at', 'question_responses'
        ]


class ModuleProgressSerializer(serializers.ModelSerializer):
    """Module progress serializer"""
    
    class Meta:
        model = ModuleProgress
        fields = [
            'id', 'module_id', 'module_title', 'total_lessons', 'lessons_completed',
            'completion_percentage', 'total_quizzes', 'quizzes_passed',
            'average_quiz_score', 'total_time_minutes', 'tokens_earned',
            'started_at', 'completed_at'
        ]
        read_only_fields = fields


class CourseProgressSerializer(serializers.ModelSerializer):
    """Course progress serializer"""
    
    class Meta:
        model = CourseProgress
        fields = [
            'id', 'course_id', 'course_title', 'status', 'total_modules',
            'modules_completed', 'total_lessons', 'lessons_completed',
            'completion_percentage', 'total_quizzes', 'quizzes_passed',
            'average_quiz_score', 'total_time_hours', 'tokens_earned',
            'certificate_issued', 'enrolled_at', 'started_at', 'completed_at'
        ]
        read_only_fields = fields


class ProgressSnapshotSerializer(serializers.ModelSerializer):
    """Progress snapshot serializer"""
    
    class Meta:
        model = ProgressSnapshot
        fields = [
            'id', 'lessons_completed', 'quizzes_passed', 'average_quiz_score',
            'completion_percentage', 'total_time_minutes', 'tokens_earned',
            'snapshot_date'
        ]


class UpdateLessonProgressSerializer(serializers.Serializer):
    """Update lesson progress"""
    
    lesson_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=['not_started', 'in_progress', 'completed'])
    video_watched_percentage = serializers.IntegerField(required=False, min_value=0, max_value=100)
    time_spent_minutes = serializers.IntegerField(required=False, min_value=0)


class SubmitQuizSerializer(serializers.Serializer):
    """Submit quiz attempt"""
    
    quiz_id = serializers.IntegerField()
    responses = serializers.JSONField()  # {question_id: answer}


class ProgressDashboardSerializer(serializers.Serializer):
    """Progress dashboard overview"""
    
    total_courses_enrolled = serializers.IntegerField()
    courses_in_progress = serializers.IntegerField()
    courses_completed = serializers.IntegerField()
    overall_completion = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_tokens_earned = serializers.IntegerField()
    total_time_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_quiz_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    current_course = CourseProgressSerializer(required=False)
