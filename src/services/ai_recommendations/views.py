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
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .recommendation_engine import QdrantRecommendationEngine, HybridRecommendationEngine
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
        """Get personalized recommendations using Qdrant"""
        limit = int(request.query_params.get('limit', 10))
        use_qdrant = request.query_params.get('use_qdrant', 'true').lower() == 'true'
        
        try:
            if use_qdrant:
                # Use Qdrant-based recommendations
                engine = QdrantRecommendationEngine(request.user)
                recommendations = engine.get_recommendations(limit=limit)
            else:
                # Use original hybrid recommendations
                engine = HybridRecommendationEngine(request.user)
                recommendations = engine.get_recommendations(limit=limit)
                
                # Enrich with Course model data
                from src.services.courses_service.models import Course
                enriched_recs = []
                for rec in recommendations:
                    try:
                        course = Course.objects.get(id=rec['course_id'], status='published')
                        enriched_recs.append({
                            'id': course.id,
                            'course_id': course.id,
                            'title': course.title,
                            'description': course.description,
                            'thumbnail_url': course.thumbnail_url,
                            'category': course.category.name if course.category else '',
                            'difficulty_level': course.difficulty_level,
                            'access_type': course.access_type,
                            'token_cost': course.token_cost,
                            'price_usd': float(course.price_usd),
                            'score': rec['score'],
                            'average_rating': float(course.average_rating),
                            'total_enrollments': course.total_enrollments,
                            'is_featured': course.is_featured,
                            'match_percentage': round(float(rec['score']) * 100, 2),
                        })
                    except Course.DoesNotExist:
                        continue
                
                recommendations = enriched_recs
            
            # If no recommendations, fallback
            if len(recommendations) == 0:
                from src.services.courses_service.models import Course
                fallback_courses = Course.objects.filter(
                    status='published'
                ).order_by('-is_featured', '-total_enrollments')[:limit]
                
                recommendations = [{
                    'id': c.id,
                    'course_id': c.id,
                    'title': c.title,
                    'description': c.description,
                    'thumbnail_url': c.thumbnail_url,
                    'category': c.category.name if c.category else '',
                    'difficulty_level': c.difficulty_level,
                    'access_type': c.access_type,
                    'average_rating': float(c.average_rating),
                    'total_enrollments': c.total_enrollments,
                    'is_featured': c.is_featured,
                    'score': 0.5,
                    'match_percentage': 50.0
                } for c in fallback_courses]
            
            return Response({
                'status': 'success',
                'count': len(recommendations),
                'data': recommendations
            })
            
        except Exception as e:
            logger.error(f"Error in recommendations: {str(e)}", exc_info=True)
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def reindex_qdrant(self, request):
        """Admin endpoint to reindex all courses to Qdrant"""
        try:
            engine = QdrantRecommendationEngine(request.user)
            result = engine.bulk_index_courses()
            return Response(result)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# class RecommendationViewSet(viewsets.ViewSet):
#     """Personalized course recommendations"""
    
#     permission_classes = [IsAuthenticated]
    
#     @action(detail=False, methods=['get'])
#     def for_me(self, request):
#         """Get personalized recommendations for logged-in user"""
        
#         limit = int(request.query_params.get('limit', 10))
        
#         try:
#             engine = HybridRecommendationEngine(request.user)
#             recommendations = engine.get_recommendations(limit=limit)
            
#             # Use actual Course model to ensure valid courses
#             from src.services.courses_service.models import Course
            
#             # Enrich recommendations with course details from actual Course model
#             enriched_recs = []
#             for rec in recommendations:
#                 try:
#                     course = Course.objects.get(id=rec['course_id'], status='published')
#                     enriched_recs.append({
#                         'id': course.id,
#                         'course_id': course.id,
#                         'title': course.title,
#                         'course_name': course.title,
#                         'description': course.description,
#                         'thumbnail_url': course.thumbnail_url,
#                         'category': course.category.name if course.category else '',
#                         'difficulty_level': course.difficulty_level,
#                         'access_type': course.access_type,
#                         'token_cost': course.token_cost,
#                         'price_usd': float(course.price_usd),
#                         'score': rec['score'],
#                         'average_rating': float(course.average_rating),
#                         'avg_rating': float(course.average_rating),
#                         'total_enrollments': course.total_enrollments,
#                         'is_featured': course.is_featured,
#                         'match_percentage': round(float(rec['score']) * 100, 2),
#                     })
#                 except (Course.DoesNotExist, KeyError, ValueError):
#                     continue
            
#             # If no recommendations, fallback to popular/featured courses
#             if len(enriched_recs) == 0:
#                 logger.info("No recommendations found, falling back to popular courses")
#                 try:
#                     fallback_courses = Course.objects.filter(
#                         status='published'
#                     ).order_by('-is_featured', '-total_enrollments', '-average_rating')[:limit]
                    
#                     for course in fallback_courses:
#                         enriched_recs.append({
#                             'id': course.id,
#                             'course_id': course.id,
#                             'title': course.title,
#                             'course_name': course.title,
#                             'description': course.description,
#                             'thumbnail_url': course.thumbnail_url,
#                             'category': course.category.name if course.category else '',
#                             'difficulty_level': course.difficulty_level,
#                             'access_type': course.access_type,
#                             'token_cost': course.token_cost,
#                             'price_usd': float(course.price_usd),
#                             'score': 0.5,  # Default score for fallback
#                             'average_rating': float(course.average_rating),
#                             'avg_rating': float(course.average_rating),
#                             'total_enrollments': course.total_enrollments,
#                             'is_featured': course.is_featured,
#                             'match_percentage': 50.0,
#                         })
#                 except Exception as fallback_error:
#                     logger.error(f"Fallback recommendations failed: {str(fallback_error)}")
            
#             return Response({
#                 'status': 'success',
#                 'count': len(enriched_recs),
#                 'data': enriched_recs
#             })
        
#         except Exception as e:
#             logger.error(f"Error in recommendations: {str(e)}", exc_info=True)
#             # Try fallback before returning error
#             try:
#                 from src.services.courses_service.models import Course
#                 fallback_courses = Course.objects.filter(
#                     status='published'
#                 ).order_by('-is_featured', '-total_enrollments')[:limit]
                
#                 data = [{
#                     'id': c.id,
#                     'course_id': c.id,
#                     'title': c.title,
#                     'course_name': c.title,
#                     'description': c.description,
#                     'thumbnail_url': c.thumbnail_url,
#                     'category': c.category.name if c.category else '',
#                     'difficulty_level': c.difficulty_level,
#                     'access_type': c.access_type,
#                     'average_rating': float(c.average_rating),
#                     'total_enrollments': c.total_enrollments,
#                     'is_featured': c.is_featured,
#                 } for c in fallback_courses]
                
#                 return Response({
#                     'status': 'success',
#                     'count': len(data),
#                     'data': data
#                 })
#             except:
#                 return Response(
#                     {'status': 'error', 'message': str(e)},
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
    
#     @action(detail=False, methods=['get'])
#     def trending(self, request):
#         """Get trending courses - use actual Course model to ensure valid IDs"""
        
#         limit = int(request.query_params.get('limit', 10))
        
#         try:
#             # Use actual Course model instead of CourseVector to ensure valid IDs
#             from src.services.courses_service.models import Course
            
#             # Try to get trending from recent interactions
#             seven_days_ago = timezone.now() - timedelta(days=7)
#             from .models import UserCourseInteraction
            
#             # Get course IDs with recent interactions
#             recent_interactions = UserCourseInteraction.objects.filter(
#                 created_at__gte=seven_days_ago,
#                 interaction_type__in=['enroll', 'complete', 'rate']
#             ).values('course_id').annotate(
#                 interaction_count=Count('id')
#             ).order_by('-interaction_count')[:limit * 2]
            
#             trending_course_ids = [item['course_id'] for item in recent_interactions if item['course_id']]
            
#             # Filter to only existing courses
#             if trending_course_ids:
#                 existing_course_ids = Course.objects.filter(
#                     id__in=trending_course_ids,
#                     status='published'
#                 ).values_list('id', flat=True)
#                 trending_course_ids = list(existing_course_ids)
            
#             # Get trending courses from actual Course model
#             if trending_course_ids:
#                 trending_courses = Course.objects.filter(
#                     id__in=trending_course_ids,
#                     status='published'
#                 ).order_by('-total_enrollments', '-average_rating')[:limit]
                
#                 # If not enough, add popular courses
#                 if trending_courses.count() < limit:
#                     remaining = limit - trending_courses.count()
#                     additional = Course.objects.filter(
#                         status='published'
#                     ).exclude(
#                         id__in=trending_course_ids
#                     ).order_by('-total_enrollments', '-average_rating')[:remaining]
#                     trending_courses = list(trending_courses) + list(additional)
#             else:
#                 # No recent interactions, just get popular courses
#                 trending_courses = Course.objects.filter(
#                     status='published'
#                 ).order_by('-total_enrollments', '-average_rating')[:limit]
            
#             # Convert to serializer format
#             data = []
#             for course in trending_courses:
#                 data.append({
#                     'id': course.id,  # Use actual course ID
#                     'course_id': course.id,
#                     'title': course.title,
#                     'course_name': course.title,
#                     'description': course.description,
#                     'thumbnail_url': course.thumbnail_url,
#                     'category': course.category.name if course.category else '',
#                     'difficulty_level': course.difficulty_level,
#                     'access_type': course.access_type,
#                     'token_cost': course.token_cost,
#                     'price_usd': float(course.price_usd),
#                     'total_enrollments': course.total_enrollments,
#                     'average_rating': float(course.average_rating),
#                     'is_featured': course.is_featured,
#                     'trend_score': float(course.total_enrollments) / 10.0,  # Simple trend score
#                 })
            
#             return Response({
#                 'status': 'success',
#                 'count': len(data),
#                 'data': data
#             })
#         except Exception as e:
#             logger.error(f"Error getting trending courses: {str(e)}", exc_info=True)
#             # Fallback: get popular published courses
#             try:
#                 from src.services.courses_service.models import Course
#                 fallback_courses = Course.objects.filter(
#                     status='published'
#                 ).order_by('-total_enrollments', '-average_rating')[:limit]
                
#                 data = [{
#                     'id': c.id,
#                     'course_id': c.id,
#                     'title': c.title,
#                     'course_name': c.title,
#                     'description': c.description,
#                     'thumbnail_url': c.thumbnail_url,
#                     'category': c.category.name if c.category else '',
#                     'difficulty_level': c.difficulty_level,
#                     'access_type': c.access_type,
#                     'token_cost': c.token_cost,
#                     'price_usd': float(c.price_usd),
#                     'total_enrollments': c.total_enrollments,
#                     'average_rating': float(c.average_rating),
#                     'is_featured': c.is_featured,
#                     'trend_score': float(c.total_enrollments) / 10.0,
#                 } for c in fallback_courses]
                
#                 return Response({
#                     'status': 'success',
#                     'count': len(data),
#                     'data': data
#                 })
#             except Exception as fallback_error:
#                 logger.error(f"Fallback also failed: {str(fallback_error)}")
#                 return Response({
#                     'status': 'success',
#                     'count': 0,
#                     'data': []
#                 })
    
#     @action(detail=False, methods=['get'])
#     def similar(self, request):
#         """Get courses similar to a given course"""
        
#         course_id = request.query_params.get('course_id')
#         limit = int(request.query_params.get('limit', 5))
        
#         if not course_id:
#             return Response(
#                 {'status': 'error', 'message': 'course_id parameter required'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         try:
#             engine = HybridRecommendationEngine(request.user)
#             similar_courses = engine.get_similar_courses(int(course_id), limit=limit)
            
#             # Enrich with course details
#             enriched = []
#             for sim_course in similar_courses:
#                 try:
#                     course = CourseVector.objects.get(course_id=sim_course['course_id'])
#                     enriched.append({
#                         'course_id': course.course_id,
#                         'course_name': course.course_name,
#                         'similarity_score': round(sim_course['similarity'], 2),
#                         'category': course.category,
#                         'avg_rating': float(course.avg_rating),
#                     })
#                 except CourseVector.DoesNotExist:
#                     continue
            
#             return Response({
#                 'status': 'success',
#                 'count': len(enriched),
#                 'data': enriched
#             })
        
#         except Exception as e:
#             logger.error(f"Error finding similar courses: {str(e)}", exc_info=True)
#             return Response(
#                 {'status': 'error', 'message': str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


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
