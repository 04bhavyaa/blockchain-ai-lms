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

from .models import (
    Course, Module, Lesson, Quiz, Enrollment, CourseRating, Bookmark
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
    """Course management endpoints"""
    
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
        """List all published courses with filtering"""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({'status': 'success', 'data': serializer.data})
    
    def retrieve(self, request, *args, **kwargs):
        """Get detailed course info"""
        course = self.get_object()
        serializer = self.get_serializer(course, context={'request': request})
        return Response({'status': 'success', 'data': serializer.data})
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_courses(self, request):
        """Get user's enrolled courses"""
        
        enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
        courses = [e.course for e in enrollments]
        
        serializer = CourseListSerializer(courses, many=True)
        return Response({'status': 'success', 'count': len(courses), 'data': serializer.data})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll in a course"""
        
        course = self.get_object()
        
        # Check if already enrolled
        if Enrollment.objects.filter(user=request.user, course=course).exists():
            raise ValidationError("Already enrolled in this course")
        
        # Check access restrictions
        if course.access_type == 'token':
            if request.user.token_balance < course.token_cost:
                raise ValidationError(
                    f"Insufficient tokens. Required: {course.token_cost}, "
                    f"Available: {request.user.token_balance}"
                )
            request.user.token_balance -= course.token_cost
            request.user.save()
        
        # Create enrollment
        enrollment = Enrollment.objects.create(
            user=request.user,
            course=course
        )
        
        # Increment course enrollment count
        course.total_enrollments += 1
        course.save()
        
        logger.info(f"Enrolled: {request.user.email} - {course.title}")
        
        return Response({
            'status': 'success',
            'message': f'Successfully enrolled in {course.title}',
            'data': EnrollmentSerializer(enrollment).data
        }, status=status.HTTP_201_CREATED)
    
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
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def by_module(self, request):
        """Get lessons for a module"""
        
        module_id = request.query_params.get('module_id')
        if not module_id:
            raise ValidationError("module_id parameter required")
        
        lessons = Lesson.objects.filter(module_id=module_id).order_by('order')
        serializer = self.get_serializer(lessons, many=True)
        
        return Response({'status': 'success', 'data': serializer.data})


class EnrollmentViewSet(viewsets.ModelViewSet):
    """Enrollment management"""
    
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update course progress"""
        
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
