"""
Progress service views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    LessonProgress, QuizAttempt, QuestionResponse,
    ModuleProgress, CourseProgress, ProgressSnapshot
)
from .serializers import (
    LessonProgressSerializer, QuizAttemptSerializer, QuestionResponseSerializer,
    ModuleProgressSerializer, CourseProgressSerializer, ProgressSnapshotSerializer,
    UpdateLessonProgressSerializer, SubmitQuizSerializer, ProgressDashboardSerializer
)
from src.shared.exceptions import ValidationError, ResourceNotFoundError
from src.shared.constants import TOKEN_REWARDS

logger = logging.getLogger(__name__)


class LessonProgressViewSet(viewsets.ModelViewSet):
    """Lesson progress tracking"""
    
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LessonProgress.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def mark_progress(self, request):
        """Mark lesson progress"""
        
        serializer = UpdateLessonProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        lesson_id = serializer.validated_data['lesson_id']
        status_val = serializer.validated_data['status']
        video_watched = serializer.validated_data.get('video_watched_percentage', 0)
        time_spent = serializer.validated_data.get('time_spent_minutes', 0)
        
        try:
            progress, created = LessonProgress.objects.get_or_create(
                user=request.user,
                lesson_id=lesson_id,
                defaults={'lesson_title': f'Lesson {lesson_id}'}
            )
            
            # Update progress
            progress.status = status_val
            progress.video_watched_percentage = video_watched
            progress.time_spent_minutes = time_spent
            
            if status_val == 'in_progress' and not progress.started_at:
                progress.started_at = timezone.now()
            
            # Mark complete and award tokens
            if status_val == 'completed' and not progress.completed_at:
                progress.completed_at = timezone.now()
                progress.tokens_earned = TOKEN_REWARDS.get('LESSON_COMPLETE', 5)
                
                # Add tokens to user
                request.user.token_balance += progress.tokens_earned
                request.user.save()
            
            progress.save()
            
            logger.info(
                f"Lesson progress updated: {request.user.email} - "
                f"Lesson {lesson_id} - {status_val}"
            )
            
            return Response({
                'status': 'success',
                'message': f'Lesson marked as {status_val}',
                'data': LessonProgressSerializer(progress).data,
                'tokens_earned': progress.tokens_earned,
            })
        
        except Exception as e:
            logger.error(f"Error updating lesson progress: {str(e)}")
            raise ValidationError(str(e))
    
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        """Get lesson progress for a course"""
        
        course_id = request.query_params.get('course_id')
        if not course_id:
            raise ValidationError("course_id parameter required")
        
        lessons = self.get_queryset().filter(course_id=course_id)
        serializer = self.get_serializer(lessons, many=True)
        
        return Response({'status': 'success', 'data': serializer.data})


class QuizAttemptViewSet(viewsets.ModelViewSet):
    """Quiz attempts tracking"""
    
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def submit_quiz(self, request):
        """
        Submit quiz attempt
        Calculate score and award tokens if passed
        """
        
        serializer = SubmitQuizSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        quiz_id = serializer.validated_data['quiz_id']
        responses = serializer.validated_data['responses']
        
        try:
            # Get previous attempts count
            attempt_count = self.get_queryset().filter(quiz_id=quiz_id).count() + 1
            
            # Create quiz attempt record
            attempt = QuizAttempt.objects.create(
                user=request.user,
                quiz_id=quiz_id,
                quiz_title=f'Quiz {quiz_id}',
                attempt_number=attempt_count,
                status='submitted',
                responses=responses,
            )
            
            # Score the quiz (simplified - would call actual scoring service)
            total_points = 0
            points_earned = 0
            
            # Calculate scoring based on responses
            for question_id, answer in responses.items():
                # This would fetch actual question and score
                # For now, simplified mock scoring
                points = self._score_question(int(question_id), answer)
                total_points += 1
                points_earned += points
                
                # Create question response record
                QuestionResponse.objects.create(
                    quiz_attempt=attempt,
                    question_id=int(question_id),
                    question_text=f'Question {question_id}',
                    question_type='multiple_choice',
                    user_response=answer,
                    points_possible=1,
                    points_earned=points,
                    is_correct=points == 1,
                )
            
            # Update attempt with scores
            attempt.total_points = total_points
            attempt.points_earned = points_earned
            attempt.percentage_score = (points_earned / total_points * 100) if total_points > 0 else 0
            attempt.completed_at = timezone.now()
            
            # Check if passed
            attempt.is_passed = attempt.percentage_score >= attempt.passing_score
            
            # Award tokens if passed [web:152]
            if attempt.is_passed:
                attempt.tokens_earned = TOKEN_REWARDS.get('QUIZ_COMPLETE', 20)
                request.user.token_balance += attempt.tokens_earned
                request.user.save()
            
            attempt.save()
            
            logger.info(
                f"Quiz submitted: {request.user.email} - Quiz {quiz_id} - "
                f"Score: {attempt.percentage_score}% - Passed: {attempt.is_passed}"
            )
            
            return Response({
                'status': 'success',
                'message': 'Quiz submitted successfully',
                'data': QuizAttemptSerializer(attempt).data,
                'is_passed': attempt.is_passed,
                'tokens_earned': attempt.tokens_earned,
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error submitting quiz: {str(e)}")
            raise ValidationError(str(e))
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get quiz attempt history"""
        
        quiz_id = request.query_params.get('quiz_id')
        attempts = self.get_queryset()
        
        if quiz_id:
            attempts = attempts.filter(quiz_id=quiz_id)
        
        attempts = attempts.order_by('-completed_at')
        page = self.paginate_queryset(attempts)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(attempts, many=True)
        return Response({'status': 'success', 'data': serializer.data})
    
    def _score_question(self, question_id, answer):
        """Score a single question (simplified)"""
        # In production: fetch correct answer from question table
        # For now: simplified mock
        return 1 if answer else 0


class CourseProgressViewSet(viewsets.ModelViewSet):
    """Course-level progress tracking"""
    
    serializer_class = CourseProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CourseProgress.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_courses(self, request):
        """Get user's course progress"""
        
        courses = self.get_queryset().order_by('-updated_at')
        page = self.paginate_queryset(courses)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(courses, many=True)
        return Response({'status': 'success', 'data': serializer.data})
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get progress dashboard overview"""
        
        all_courses = self.get_queryset()
        
        dashboard_data = {
            'total_courses_enrolled': all_courses.count(),
            'courses_in_progress': all_courses.filter(status='in_progress').count(),
            'courses_completed': all_courses.filter(status='completed').count(),
            'overall_completion': all_courses.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0,
            'total_tokens_earned': all_courses.aggregate(Sum('tokens_earned'))['tokens_earned__sum'] or 0,
            'total_time_hours': all_courses.aggregate(Sum('total_time_hours'))['total_time_hours__sum'] or 0,
            'average_quiz_score': all_courses.aggregate(Avg('average_quiz_score'))['average_quiz_score__avg'] or 0,
        }
        
        # Get current course (most recently updated)
        current = all_courses.filter(status='in_progress').first()
        if current:
            dashboard_data['current_course'] = CourseProgressSerializer(current).data
        
        serializer = ProgressDashboardSerializer(dashboard_data)
        return Response({'status': 'success', 'data': serializer.data})
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        """Mark course as completed and issue certificate"""
        
        try:
            course = self.get_object()
        except CourseProgress.DoesNotExist:
            raise ResourceNotFoundError("Course not found")
        
        course.status = 'completed'
        course.completed_at = timezone.now()
        course.completion_percentage = 100
        
        # Award tokens for course completion
        course.tokens_earned += TOKEN_REWARDS.get('COURSE_COMPLETE', 100)
        request.user.token_balance += TOKEN_REWARDS.get('COURSE_COMPLETE', 100)
        request.user.save()
        
        # Mark certificate as ready to issue
        course.certificate_issued = True
        course.certificate_issued_at = timezone.now()
        
        course.save()
        
        logger.info(f"Course completed: {request.user.email} - Course {course.course_id}")
        
        return Response({
            'status': 'success',
            'message': 'Course marked as completed!',
            'data': CourseProgressSerializer(course).data,
            'tokens_earned': TOKEN_REWARDS.get('COURSE_COMPLETE', 100),
        })


class ProgressSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """Progress snapshots for analytics"""
    
    serializer_class = ProgressSnapshotSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ProgressSnapshot.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        """Get progress snapshots for a course"""
        
        course_id = request.query_params.get('course_id')
        if not course_id:
            raise ValidationError("course_id parameter required")
        
        snapshots = self.get_queryset().filter(course_id=course_id).order_by('snapshot_date')
        serializer = self.get_serializer(snapshots, many=True)
        
        return Response({'status': 'success', 'data': serializer.data})
