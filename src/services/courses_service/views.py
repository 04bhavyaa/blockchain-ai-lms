"""
Courses service views
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
import logging
import requests

from .models import (
    Course, Module, Lesson, Quiz, Question, Answer, Enrollment, CourseRating, Bookmark
)
from .serializers import (
    CourseDetailedSerializer, CourseListSerializer, ModuleSerializer,
    LessonSerializer, QuizSerializer, EnrollmentSerializer,
    CourseRatingSerializer, BookmarkSerializer
)
from src.shared.exceptions import ValidationError, ResourceNotFoundError, PermissionDeniedError
from src.shared.pagination import StandardPagination

logger = logging.getLogger(__name__)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.filter(status='published')
    permission_classes = [AllowAny]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'difficulty_level', 'access_type']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'total_enrollments', 'average_rating']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailedSerializer
        return CourseListSerializer

    def list(self, request, *args, **kwargs):
        logger.info(f"Course list request - User: {request.user.email if request.user.is_authenticated else 'Anonymous'}, "
                   f"Params: {dict(request.query_params)}")
        
        queryset = self.filter_queryset(self.get_queryset())
        total_count = queryset.count()
        logger.info(f"Filtered queryset count: {total_count}")
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            logger.info(f"Returning paginated response: {len(serializer.data)} courses on page")
            response = self.get_paginated_response(serializer.data)
            logger.debug(f"Pagination response structure: status={response.data.get('status')}, "
                        f"has_data={bool(response.data.get('data'))}, "
                        f"data_length={len(response.data.get('data', [])) if isinstance(response.data.get('data'), list) else 'N/A'}, "
                        f"has_pagination={bool(response.data.get('pagination'))}")
            return response
        
        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"Returning non-paginated response: {len(serializer.data)} courses")
        return Response({'status': 'success', 'data': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        course_id = kwargs.get('pk')
        logger.info(f"Course retrieve request - ID: {course_id}, User: {request.user.email if request.user.is_authenticated else 'Anonymous'}")
        
        try:
            course = self.get_object()
            logger.info(f"Course found: {course.title} (ID: {course.id})")
            serializer = self.get_serializer(course, context={'request': request})
            return Response({'status': 'success', 'data': serializer.data})
        except Exception as e:
            logger.error(f"Error retrieving course {course_id}: {str(e)}", exc_info=True)
            raise

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        course = self.get_object()

        # Already enrolled check
        if Enrollment.objects.filter(user=request.user, course=course).exists():
            raise ValidationError("Already enrolled in this course")

        # Blockchain token unlock integration
        enrollment_status = 'enrolled'
        blockchain_unlock_tx_hash = None
        last_blockchain_status = ''
        if course.access_type == 'token':
            enrollment_status = 'pending_blockchain'
            # Invoke blockchain unlock callback with details (simulate webhook event)
            if course.blockchain_unlock_callback:
                payload = {
                    'event': 'unlock_requested',
                    'user': request.user.email,
                    'course_id': course.id,
                    'token_cost': course.token_cost
                }
                try:
                    resp = requests.post(course.blockchain_unlock_callback, json=payload, timeout=5)
                    last_blockchain_status = f"Unlock request sent: {resp.status_code} {resp.text}"
                    logger.info(f"Blockchain unlock callback sent for course {course.id}: {resp.status_code}")
                except Exception as e:
                    last_blockchain_status = f"Unlock callback failed: {str(e)}"
                    logger.error(f"Unlock callback error: {str(e)}")

        enrollment = Enrollment.objects.create(
            user=request.user,
            course=course,
            status=enrollment_status,
            blockchain_unlock_tx_hash=blockchain_unlock_tx_hash,
            last_blockchain_status=last_blockchain_status
        )
        course.total_enrollments += 1
        course.save()
        
        # Create CourseProgress record for tracking
        from src.services.progress_service.models import CourseProgress
        total_modules = course.modules.count()
        total_lessons = sum(module.lessons.count() for module in course.modules.all())
        total_quizzes = sum(1 for module in course.modules.all() for lesson in module.lessons.all() if hasattr(lesson, 'quiz') and lesson.quiz)
        
        CourseProgress.objects.get_or_create(
            user=request.user,
            course_id=course.id,
            defaults={
                'course_title': course.title,
                'status': 'enrolled',
                'total_modules': total_modules,
                'total_lessons': total_lessons,
                'total_quizzes': total_quizzes,
            }
        )
        
        logger.info(f"Enrolled: {request.user.email} - {course.title}")

        return Response({
            'status': 'success',
            'message': f'Successfully enrolled in {course.title}',
            'data': EnrollmentSerializer(enrollment).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_courses(self, request):
        """Get user's enrolled courses"""
        
        enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
        courses = [e.course for e in enrollments]
        
        serializer = CourseListSerializer(courses, many=True)
        return Response({'status': 'success', 'count': len(courses), 'data': serializer.data})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def rate(self, request, pk=None):
        """Submit course rating"""
        
        course = self.get_object()
        rating = request.data.get('rating')
        review = request.data.get('review', '')
        
        if not rating:
            raise ValidationError("rating is required")
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError()
        except ValueError:
            raise ValidationError("rating must be between 1 and 5")
        
        # Update or create rating
        course_rating, created = CourseRating.objects.update_or_create(
            user=request.user,
            course=course,
            defaults={'rating': rating, 'review': review}
        )
        
        # Recalculate course average rating
        avg_rating = course.ratings.aggregate(Avg('rating'))['rating__avg'] or 0
        course.average_rating = avg_rating
        course.total_ratings = course.ratings.count()
        course.save()
        
        logger.info(f"Course rated: {request.user.email} - {course.title} ({rating}⭐)")
        
        return Response({
            'status': 'success',
            'message': 'Rating submitted',
            'data': CourseRatingSerializer(course_rating).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def bookmark(self, request, pk=None):
        """Bookmark a course"""
        
        course = self.get_object()
        
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            course=course
        )
        
        if created:
            message = 'Course bookmarked'
        else:
            message = 'Already bookmarked'
        
        return Response({
            'status': 'success',
            'message': message,
            'data': BookmarkSerializer(bookmark).data
        })
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unbookmark(self, request, pk=None):
        """Remove course bookmark"""
        
        course = self.get_object()
        Bookmark.objects.filter(user=request.user, course=course).delete()
        
        return Response({'status': 'success', 'message': 'Bookmark removed'})
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending courses"""
        
        trending = Course.objects.filter(
            status='published'
        ).annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:10]
        
        serializer = CourseListSerializer(trending, many=True)
        return Response({'status': 'success', 'count': len(serializer.data), 'data': serializer.data})
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured courses"""
        
        featured = Course.objects.filter(
            status='published',
            is_featured=True
        )[:10]
        
        serializer = CourseListSerializer(featured, many=True)
        return Response({'status': 'success', 'count': len(serializer.data), 'data': serializer.data})


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    """Lesson endpoints"""
    
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter lessons based on enrollment"""
        user = self.request.user
        queryset = Lesson.objects.all()
        
        # If specific course context, check enrollment
        course_id = self.request.query_params.get('course_id')
        if course_id:
            from .models import Enrollment
            is_enrolled = Enrollment.objects.filter(
                user=user,
                course_id=course_id,
                status__in=['enrolled', 'completed']
            ).exists()
            
            # For non-enrolled users, only show free preview lessons
            if not is_enrolled:
                queryset = queryset.filter(is_free_preview=True)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_module(self, request):
        """Get lessons for a module"""
        
        module_id = request.query_params.get('module_id')
        if not module_id:
            raise ValidationError("module_id parameter required")
        
        lessons = self.get_queryset().filter(module_id=module_id).order_by('order')
        serializer = self.get_serializer(lessons, many=True)
        
        return Response({'status': 'success', 'data': serializer.data})
    
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        """Get all lessons for a course"""
        
        course_id = request.query_params.get('course_id')
        if not course_id:
            raise ValidationError("course_id parameter required")
        
        from .models import Module
        modules = Module.objects.filter(course_id=course_id).order_by('order')
        course_lessons = []
        
        for module in modules:
            lessons = self.get_queryset().filter(module=module).order_by('order')
            course_lessons.append({
                'module_id': module.id,
                'module_title': module.title,
                'module_order': module.order,
                'lessons': LessonSerializer(lessons, many=True).data
            })
        
        return Response({'status': 'success', 'data': course_lessons})


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    """Quiz endpoints"""
    
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter quizzes based on enrollment"""
        user = self.request.user
        queryset = Quiz.objects.all()
        
        # If specific course context, check enrollment
        course_id = self.request.query_params.get('course_id')
        if course_id:
            from .models import Enrollment
            is_enrolled = Enrollment.objects.filter(
                user=user,
                course_id=course_id,
                status__in=['enrolled', 'completed']
            ).exists()
            
            if not is_enrolled:
                # For non-enrolled users, only show quizzes for free preview lessons
                queryset = queryset.filter(lesson__is_free_preview=True)
        
        return queryset


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        enrollment = self.get_object()
        progress = request.data.get('progress_percentage')
        lessons_completed = request.data.get('lessons_completed')
        if progress is not None:
            enrollment.progress_percentage = min(progress, 100)
        if lessons_completed is not None:
            enrollment.lessons_completed = lessons_completed
        enrollment.save()
        return Response({
            'status': 'success',
            'message': 'Progress updated',
            'data': EnrollmentSerializer(enrollment).data
        })

    @action(detail=True, methods=['post'])
    def block_callback(self, request, pk=None):
        """
        Endpoint to be called by blockchain service/webhook after actual unlock/certificate mint.
        Receives tx_hash, event type ('unlock'/'certificate_mint'), and optionally logs message.
        """
        enrollment = self.get_object()
        tx_hash = request.data.get('tx_hash')
        event = request.data.get('event')
        message = request.data.get('message', '')
        if event == 'unlock':
            enrollment.status = 'enrolled'
            enrollment.blockchain_unlock_tx_hash = tx_hash
        elif event == 'certificate_mint':
            enrollment.certificate_issued = True
            enrollment.blockchain_certificate_tx_hash = tx_hash
        enrollment.last_blockchain_status = message
        enrollment.save()
        return Response({'status': 'success', 'updated': event})


class CourseRatingViewSet(viewsets.ModelViewSet):
    """Course ratings"""
    
    serializer_class = CourseRatingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CourseRating.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        """Get ratings for a course"""
        
        course_id = request.query_params.get('course_id')
        if not course_id:
            raise ValidationError("course_id parameter required")
        
        ratings = CourseRating.objects.filter(course_id=course_id).order_by('-created_at')
        serializer = self.get_serializer(ratings, many=True)
        
        return Response({'status': 'success', 'data': serializer.data})


class BookmarkViewSet(viewsets.ModelViewSet):
    """User bookmarks"""
    
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def my_bookmarks(self, request):
        """Get user's bookmarked courses"""
        
        bookmarks = self.get_queryset()
        page = self.paginate_queryset(bookmarks)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(bookmarks, many=True)
        return Response({'status': 'success', 'data': serializer.data})
