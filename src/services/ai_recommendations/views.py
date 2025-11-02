"""
AI Recommendations service views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .recommendation_engine import HybridRecommendationEngine
from .models import (
    UserPreference, RecommendationFeedback, LearningPath,
    UserCourseInteraction, CourseVector, RecommendationCache
)
from .serializers import (
    UserPreferenceSerializer, RecommendationFeedbackSerializer,
    LearningPathSerializer, UserCourseInteractionSerializer,
    RecommendationResponseSerializer, SimilarCourseSerializer,
    TrendingCourseSerializer
)

import logging

logger = logging.getLogger(__name__)


class RecommendationViewSet(viewsets.ViewSet):
    """Personalized course recommendations"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def for_me(self, request):
        """Get personalized recommendations for logged-in user"""
        
        limit = int(request.query_params.get('limit', 10))
        
        try:
            engine = HybridRecommendationEngine(request.user)
            recommendations = engine.get_recommendations(limit=limit)
            
            # Enrich recommendations with course details
            enriched_recs = []
            for rec in recommendations:
                try:
                    course = CourseVector.objects.get(course_id=rec['course_id'])
                    enriched_recs.append({
                        'course_id': course.course_id,
                        'course_name': course.course_name,
                        'category': course.category,
                        'difficulty_level': course.difficulty_level,
                        'score': rec['score'],
                        'avg_rating': float(course.avg_rating),
                        'total_enrollments': course.total_enrollments,
                        'match_percentage': round(float(rec['score']) * 100, 2),
                    })
                except CourseVector.DoesNotExist:
                    continue
            
            return Response({
                'status': 'success',
                'count': len(enriched_recs),
                'data': enriched_recs
            })
        
        except Exception as e:
            logger.error(f"Error in recommendations: {str(e)}", exc_info=True)
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending courses"""
        
        limit = int(request.query_params.get('limit', 10))
        
        # Courses trending in last 7 days
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        trending = CourseVector.objects.filter(
            updated_at__gte=seven_days_ago
        ).annotate(
            recent_enrollments=Count(
                'usercoursinteraction',
                filter=Q(usercoursinteraction__created_at__gte=seven_days_ago)
            )
        ).order_by('-recent_enrollments')[:limit]
        
        serializer = TrendingCourseSerializer(
            [{
                'course_id': course.course_id,
                'course_name': course.course_name,
                'total_enrollments': course.total_enrollments,
                'avg_rating': float(course.avg_rating),
                'trend_score': course.completion_rate,
            } for course in trending],
            many=True
        )
        
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def similar(self, request):
        """Get courses similar to a given course"""
        
        course_id = request.query_params.get('course_id')
        limit = int(request.query_params.get('limit', 5))
        
        if not course_id:
            return Response(
                {'status': 'error', 'message': 'course_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            engine = HybridRecommendationEngine(request.user)
            similar_courses = engine.get_similar_courses(int(course_id), limit=limit)
            
            # Enrich with course details
            enriched = []
            for sim_course in similar_courses:
                try:
                    course = CourseVector.objects.get(course_id=sim_course['course_id'])
                    enriched.append({
                        'course_id': course.course_id,
                        'course_name': course.course_name,
                        'similarity_score': round(sim_course['similarity'], 2),
                        'category': course.category,
                        'avg_rating': float(course.avg_rating),
                    })
                except CourseVector.DoesNotExist:
                    continue
            
            return Response({
                'status': 'success',
                'count': len(enriched),
                'data': enriched
            })
        
        except Exception as e:
            logger.error(f"Error finding similar courses: {str(e)}", exc_info=True)
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserPreferenceViewSet(viewsets.ModelViewSet):
    """User preference management"""
    
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        preference, _ = UserPreference.objects.get_or_create(user=self.request.user)
        return preference
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Get current user's preferences"""
        
        preference = self.get_object()
        serializer = self.get_serializer(preference)
        return Response({'status': 'success', 'data': serializer.data})
    
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """Update user preferences"""
        
        preference = self.get_object()
        serializer = self.get_serializer(preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({'status': 'success', 'data': serializer.data})


class RecommendationFeedbackViewSet(viewsets.ModelViewSet):
    """Feedback on recommendations for system improvement"""
    
    serializer_class = RecommendationFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RecommendationFeedback.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def submit_feedback(self, request):
        """Submit feedback on recommendation"""
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        
        return Response(
            {'status': 'success', 'message': 'Feedback recorded'},
            status=status.HTTP_201_CREATED
        )


class LearningPathViewSet(viewsets.ModelViewSet):
    """Personalized learning paths"""
    
    serializer_class = LearningPathSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        path, _ = LearningPath.objects.get_or_create(user=self.request.user)
        return path
    
    @action(detail=False, methods=['get'])
    def my_path(self, request):
        """Get current user's learning path"""
        
        path = self.get_object()
        serializer = self.get_serializer(path)
        return Response({'status': 'success', 'data': serializer.data})
    
    @action(detail=False, methods=['post'])
    def generate_path(self, request):
        """Generate personalized learning path"""
        
        try:
            engine = HybridRecommendationEngine(request.user)
            recommendations = engine.get_recommendations(limit=20)
            
            course_ids = [rec['course_id'] for rec in recommendations]
            
            path = self.get_object()
            path.courses_in_path = course_ids
            path.estimated_completion_days = len(course_ids) * 7  # Assume 7 days per course
            path.save()
            
            serializer = self.get_serializer(path)
            return Response({
                'status': 'success',
                'message': 'Learning path generated',
                'data': serializer.data
            })
        
        except Exception as e:
            logger.error(f"Error generating learning path: {str(e)}", exc_info=True)
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
