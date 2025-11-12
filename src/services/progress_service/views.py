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
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return LessonProgress.objects.filter(user=self.request.user)
    @action(detail=False, methods=['post'])
    def mark_progress(self, request):
        serializer = UpdateLessonProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson_id = serializer.validated_data['lesson_id']
        status_val = serializer.validated_data['status']
        video_watched = serializer.validated_data.get('video_watched_percentage', 0)
        time_spent = serializer.validated_data.get('time_spent_minutes', 0)
        try:
            # Get lesson details for title
            from src.services.courses_service.models import Lesson
            try:
                lesson = Lesson.objects.get(id=lesson_id)
                lesson_title = lesson.title
                course_id_val = lesson.module.course_id
                module_id_val = lesson.module.id
            except Lesson.DoesNotExist:
                lesson_title = f'Lesson {lesson_id}'
                course_id_val = serializer.validated_data.get('course_id')
                module_id_val = None
            
            progress, created = LessonProgress.objects.get_or_create(
                user=request.user,
                lesson_id=lesson_id,
                defaults={
                    'lesson_title': lesson_title,
                    'course_id': course_id_val or serializer.validated_data.get('course_id'),
                    'module_id': module_id_val
                }
            )
            progress.status = status_val
            progress.video_watched_percentage = video_watched
            progress.time_spent_minutes = time_spent
            if status_val == 'in_progress' and not progress.started_at:
                progress.started_at = timezone.now()
            if status_val == 'completed' and not progress.completed_at:
                progress.completed_at = timezone.now()
                progress.tokens_earned = TOKEN_REWARDS.get('LESSON_COMPLETE', 5)
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
    @action(detail=True, methods=['post'])
    def blockchain_callback(self, request, pk=None):
        """Receive blockchain event callback (tx_hash, message)"""
        progress = self.get_object()
        tx_hash = request.data.get('tx_hash')
        message = request.data.get('message', '')
        progress.blockchain_event_tx_hash = tx_hash
        progress.last_blockchain_status = message
        progress.save()
        return Response({'status': 'success', 'updated': True})
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        course_id = request.query_params.get('course_id')
        if not course_id:
            raise ValidationError("course_id parameter required")
        
        lessons = self.get_queryset().filter(course_id=course_id)
        serializer = self.get_serializer(lessons, many=True)
        
        # Also get course progress summary
        from .models import CourseProgress
        try:
            course_progress = CourseProgress.objects.get(user=request.user, course_id=course_id)
            return Response({
                'status': 'success',
                'data': {
                    'completion_percentage': float(course_progress.completion_percentage),
                    'lessons_completed': course_progress.lessons_completed,
                    'status': course_progress.status,
                    'lessons': serializer.data
                }
            })
        except CourseProgress.DoesNotExist:
            # Calculate from lesson progress
            completed_count = lessons.filter(status='completed').count()
            total_count = lessons.count()
            completion = (completed_count / total_count * 100) if total_count > 0 else 0
            
            return Response({
                'status': 'success',
                'data': {
                    'completion_percentage': completion,
                    'lessons_completed': completed_count,
                    'status': 'enrolled',
                    'lessons': serializer.data
                }
            })

class QuizAttemptViewSet(viewsets.ModelViewSet):
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)
    @action(detail=False, methods=['post'])
    def submit_quiz(self, request):
        serializer = SubmitQuizSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz_id = serializer.validated_data['quiz_id']
        responses = serializer.validated_data['responses']
        try:
            attempt_count = self.get_queryset().filter(quiz_id=quiz_id).count() + 1
            attempt = QuizAttempt.objects.create(
                user=request.user,
                quiz_id=quiz_id,
                quiz_title=f'Quiz {quiz_id}',
                attempt_number=attempt_count,
                status='submitted',
                responses=responses,
            )
            # Get quiz and questions
            from src.services.courses_service.models import Quiz, Question, Answer
            try:
                quiz = Quiz.objects.get(id=quiz_id)
                attempt.quiz_title = quiz.title
                attempt.passing_score = quiz.passing_score
            except Quiz.DoesNotExist:
                raise ResourceNotFoundError("Quiz not found")
            
            questions = Question.objects.filter(quiz_id=quiz_id).order_by('order')
            total_points = 0
            points_earned = 0
            
            for question in questions:
                question_id_str = str(question.id)
                user_answer = responses.get(question_id_str)
                total_points += question.points
                
                # Score the answer and create response
                question_points_earned = 0
                is_correct = False
                
                if question.question_type == 'multiple_choice':
                    try:
                        answer_obj = Answer.objects.get(id=int(user_answer), question=question)
                        if answer_obj.is_correct:
                            question_points_earned = question.points
                            points_earned += question.points
                            is_correct = True
                    except (Answer.DoesNotExist, ValueError, TypeError):
                        pass
                elif question.question_type == 'true_false':
                    correct_answer = Answer.objects.filter(question=question, is_correct=True).first()
                    if correct_answer and user_answer and str(user_answer).lower() == str(correct_answer.text).lower():
                        question_points_earned = question.points
                        points_earned += question.points
                        is_correct = True
                else:
                    # For other types, assume correct for now (can be enhanced later)
                    question_points_earned = question.points
                    points_earned += question.points
                    is_correct = True
                
                QuestionResponse.objects.create(
                    quiz_attempt=attempt,
                    question_id=question.id,
                    question_text=question.text,
                    question_type=question.question_type,
                    user_response=str(user_answer) if user_answer else '',
                    points_possible=question.points,
                    points_earned=question_points_earned,
                    is_correct=is_correct,
                )
            attempt.total_points = total_points
            attempt.points_earned = points_earned
            attempt.percentage_score = (points_earned / total_points * 100) if total_points > 0 else 0
            attempt.completed_at = timezone.now()
            attempt.is_passed = attempt.percentage_score >= attempt.passing_score
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
    @action(detail=True, methods=['post'])
    def blockchain_callback(self, request, pk=None):
        attempt = self.get_object()
        tx_hash = request.data.get('tx_hash')
        message = request.data.get('message', '')
        attempt.blockchain_event_tx_hash = tx_hash
        attempt.last_blockchain_status = message
        attempt.save()
        return Response({'status': 'success', 'updated': True})
    @action(detail=False, methods=['get'])
    def history(self, request):
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
        return 1 if answer else 0

class ModuleProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ModuleProgressSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return ModuleProgress.objects.filter(user=self.request.user)
    @action(detail=True, methods=['post'])
    def blockchain_callback(self, request, pk=None):
        progress = self.get_object()
        tx_hash = request.data.get('tx_hash')
        message = request.data.get('message', '')
        progress.blockchain_event_tx_hash = tx_hash
        progress.last_blockchain_status = message
        progress.save()
        return Response({'status': 'success', 'updated': True})

class CourseProgressViewSet(viewsets.ModelViewSet):
    serializer_class = CourseProgressSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return CourseProgress.objects.filter(user=self.request.user)
    @action(detail=False, methods=['get'])
    def my_courses(self, request):
        courses = self.get_queryset().order_by('-updated_at')
        page = self.paginate_queryset(courses)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(courses, many=True)
        return Response({'status': 'success', 'data': serializer.data})
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        all_courses = self.get_queryset()
        dashboard_data = {
            'total_courses_enrolled': all_courses.filter(status='enrolled').count(),
            'courses_in_progress': all_courses.filter(status='in_progress').count(),
            'courses_completed': all_courses.filter(status='completed').count(),
            'overall_completion': all_courses.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0,
            'total_tokens_earned': all_courses.aggregate(Sum('tokens_earned'))['tokens_earned__sum'] or 0,
            'total_time_hours': all_courses.aggregate(Sum('total_time_hours'))['total_time_hours__sum'] or 0,
            'average_quiz_score': all_courses.aggregate(Avg('average_quiz_score'))['average_quiz_score__avg'] or 0,
        }
        current = all_courses.filter(status='in_progress').first()
        if current:
            dashboard_data['current_course'] = CourseProgressSerializer(current).data
        serializer = ProgressDashboardSerializer(dashboard_data)
        return Response({'status': 'success', 'data': serializer.data})
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        try:
            course = self.get_object()
        except CourseProgress.DoesNotExist:
            raise ResourceNotFoundError("Course not found")
        course.status = 'completed'
        course.completed_at = timezone.now()
        course.completion_percentage = 100
        course.tokens_earned += TOKEN_REWARDS.get('COURSE_COMPLETE', 100)
        request.user.token_balance += TOKEN_REWARDS.get('COURSE_COMPLETE', 100)
        request.user.save()
        course.certificate_issued = True
        course.certificate_issued_at = timezone.now()
        course.save()
        
        # Issue blockchain certificate automatically
        from src.services.blockchain_service.models import Certificate
        import hashlib
        
        try:
            # Get course details
            from src.services.courses_service.models import Course
            course_obj = Course.objects.get(id=course.course_id)
            course_name = course_obj.title
        except Course.DoesNotExist:
            course_name = f"Course {course.course_id}"
        
        # Create certificate hash
        cert_data = f"{request.user.id}_{course.course_id}_{course.completed_at.date()}"
        certificate_hash = hashlib.sha256(cert_data.encode()).hexdigest()
        
        # Create certificate record
        certificate, created = Certificate.objects.get_or_create(
            user=request.user,
            course_id=course.course_id,
            defaults={
                'course_name': course_name,
                'completion_date': course.completed_at.date(),
                'certificate_hash': certificate_hash,
                'metadata': {
                    'completion_percentage': float(course.completion_percentage),
                    'tokens_earned': course.tokens_earned,
                    'average_quiz_score': float(course.average_quiz_score) if course.average_quiz_score else 0,
                    'total_time_hours': float(course.total_time_hours) if course.total_time_hours else 0,
                },
                'status': 'pending'
            }
        )
        
        logger.info(f"Course completed: {request.user.email} - Course {course.course_id}")
        if created:
            logger.info(f"Certificate created automatically: {request.user.email} - {course_name}")
        
        return Response({
            'status': 'success',
            'message': 'Course marked as completed!',
            'data': CourseProgressSerializer(course).data,
            'tokens_earned': TOKEN_REWARDS.get('COURSE_COMPLETE', 100),
            'certificate_issued': True,
            'certificate_id': certificate.id
        })
    @action(detail=True, methods=['post'])
    def blockchain_callback(self, request, pk=None):
        progress = self.get_object()
        tx_hash = request.data.get('tx_hash')
        message = request.data.get('message', '')
        progress.blockchain_event_tx_hash = tx_hash
        progress.last_blockchain_status = message
        progress.save()
        return Response({'status': 'success', 'updated': True})

class ProgressSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProgressSnapshotSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return ProgressSnapshot.objects.filter(user=self.request.user)
    @action(detail=True, methods=['post'])
    def blockchain_callback(self, request, pk=None):
        snap = self.get_object()
        tx_hash = request.data.get('tx_hash')
        message = request.data.get('message', '')
        snap.blockchain_event_tx_hash = tx_hash
        snap.last_blockchain_status = message
        snap.save()
        return Response({'status': 'success', 'updated': True})
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        course_id = request.query_params.get('course_id')
        if not course_id:
            raise ValidationError("course_id parameter required")
        snapshots = self.get_queryset().filter(course_id=course_id).order_by('snapshot_date')
        serializer = self.get_serializer(snapshots, many=True)
        return Response({'status': 'success', 'data': serializer.data})
