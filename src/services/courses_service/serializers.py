"""
Courses service serializers with nested relationships
"""

from rest_framework import serializers
from .models import (
    CourseCategory, Course, Module, Lesson, Quiz, Question, Answer,
    Enrollment, CourseRating, Bookmark
)


class AnswerSerializer(serializers.ModelSerializer):
    """Answer serializer for multiple choice"""
    
    class Meta:
        model = Answer
        fields = ['id', 'text', 'order', 'is_correct']
        read_only_fields = ['id']


class QuestionSerializer(serializers.ModelSerializer):
    """Question serializer with nested answers"""
    
    answers = AnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_type', 'text', 'explanation', 'order', 'points', 'image_url', 'answers']
        read_only_fields = ['id']


class QuizSerializer(serializers.ModelSerializer):
    """Quiz serializer with nested questions"""
    
    questions = QuestionSerializer(many=True, read_only=True)
    total_questions = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'passing_score', 'max_attempts',
            'time_limit_minutes', 'shuffle_questions', 'show_correct_answers',
            'questions', 'total_questions'
        ]
        read_only_fields = ['id', 'questions']
    
    def get_total_questions(self, obj):
        return obj.questions.count()


class LessonSerializer(serializers.ModelSerializer):
    """Lesson serializer with optional quiz"""
    
    quiz = QuizSerializer(read_only=True)
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'content_type', 'content_url',
            'transcript', 'duration_minutes', 'order', 'is_free_preview',
            'resources', 'quiz', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleSerializer(serializers.ModelSerializer):
    """Module serializer with nested lessons"""
    
    lessons = LessonSerializer(many=True, read_only=True)
    total_lessons = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'lessons', 'total_lessons']
        read_only_fields = ['id', 'lessons']
    
    def get_total_lessons(self, obj):
        return obj.lessons.count()


class CourseCategorySerializer(serializers.ModelSerializer):
    """Course category serializer"""
    
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'slug', 'description', 'icon_url']


class CourseDetailedSerializer(serializers.ModelSerializer):
    """Detailed course serializer with all nested content"""
    
    modules = ModuleSerializer(many=True, read_only=True)
    category = CourseCategorySerializer(read_only=True)
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    total_modules = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'category', 'instructor',
            'instructor_name', 'access_type', 'token_cost', 'price_usd',
            'thumbnail_url', 'cover_image_url', 'difficulty_level',
            'duration_hours', 'status', 'is_featured', 'tags',
            'learning_objectives', 'total_enrollments', 'average_rating',
            'total_ratings', 'modules', 'total_modules', 'is_enrolled',
            'is_bookmarked', 'user_progress', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_modules(self, obj):
        return obj.modules.count()
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(user=request.user).exists()
        return False
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.bookmarked_by.filter(user=request.user).exists()
        return False
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.enrollments.get(user=request.user)
                return {
                    'progress_percentage': float(enrollment.progress_percentage),
                    'lessons_completed': enrollment.lessons_completed,
                    'status': enrollment.status
                }
            except Enrollment.DoesNotExist:
                return None
        return None


class CourseListSerializer(serializers.ModelSerializer):
    """Simplified course serializer for list view"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'category', 'category_name', 'instructor_name',
            'access_type', 'thumbnail_url', 'difficulty_level', 'duration_hours',
            'average_rating', 'total_enrollments'
        ]


class EnrollmentSerializer(serializers.ModelSerializer):
    """Enrollment serializer"""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'course_title', 'status', 'enrolled_at',
            'completed_at', 'progress_percentage', 'lessons_completed'
        ]
        read_only_fields = ['id', 'enrolled_at', 'completed_at']


class CourseRatingSerializer(serializers.ModelSerializer):
    """Course rating serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = CourseRating
        fields = ['id', 'course', 'rating', 'review', 'user_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookmarkSerializer(serializers.ModelSerializer):
    """Bookmark serializer"""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Bookmark
        fields = ['id', 'course', 'course_title', 'created_at']
        read_only_fields = ['id', 'created_at']
