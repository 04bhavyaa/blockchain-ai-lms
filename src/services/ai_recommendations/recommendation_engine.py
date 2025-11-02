"""
Hybrid recommendation engine combining collaborative and content-based filtering
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    UserPreference, CourseVector, UserCourseInteraction,
    RecommendationCache, RecommendationFeedback
)
from src.shared.constants import RECOMMENDATION_WEIGHTS

logger = logging.getLogger(__name__)


class HybridRecommendationEngine:
    """
    Hybrid recommendation engine combining:
    - Collaborative Filtering (60%): User-based similarity
    - Content-Based Filtering (40%): Item features similarity
    """
    
    COLLABORATIVE_WEIGHT = RECOMMENDATION_WEIGHTS['COLLABORATIVE_FILTERING']
    CONTENT_WEIGHT = RECOMMENDATION_WEIGHTS['CONTENT_BASED_FILTERING']
    CACHE_TIMEOUT = 900  # 15 minutes
    
    def __init__(self, user):
        self.user = user
        self.user_interactions = UserCourseInteraction.objects.filter(user=user)
    
    def get_recommendations(self, limit=10):
        """
        Get personalized course recommendations for user
        
        Args:
            limit: Number of recommendations to return
            
        Returns:
            List of recommended courses with scores
        """
        
        # Check cache first
        cache_key = f"recommendations:{self.user.id}"
        cached_recs = cache.get(cache_key)
        if cached_recs:
            logger.info(f"Cache hit for recommendations: {self.user.email}")
            return cached_recs[:limit]
        
        try:
            # Get collaborative filtering scores
            collab_scores = self._collaborative_filtering()
            
            # Get content-based filtering scores
            content_scores = self._content_based_filtering()
            
            # Combine scores using weighted average
            hybrid_scores = self._combine_scores(collab_scores, content_scores)
            
            # Filter out already taken courses
            recommendations = self._filter_recommendations(hybrid_scores)
            
            # Sort by score and limit results
            recommendations = sorted(
                recommendations,
                key=lambda x: x['score'],
                reverse=True
            )[:limit]
            
            # Cache recommendations
            cache.set(cache_key, recommendations, self.CACHE_TIMEOUT)
            
            logger.info(f"Generated {len(recommendations)} recommendations for {self.user.email}")
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
            return []
    
    def _collaborative_filtering(self):
        """
        User-based collaborative filtering using cosine similarity
        Find similar users and recommend courses they liked
        """
        
        try:
            # Get user's rated courses
            user_ratings = self.user_interactions.filter(
                interaction_type__in=['rate', 'complete']
            ).values('course_id', 'rating', 'interaction_strength')
            
            if not user_ratings:
                logger.warning(f"No interaction data for user {self.user.email}")
                return {}
            
            # Build user-course interaction matrix
            all_interactions = UserCourseInteraction.objects.filter(
                interaction_type__in=['rate', 'complete']
            )
            
            # Group by user
            users_data = {}
            for interaction in all_interactions:
                user_id = interaction.user_id
                course_id = interaction.course_id
                
                if user_id not in users_data:
                    users_data[user_id] = {}
                
                # Weight interaction by strength and type
                weight = interaction.interaction_strength * (5 if interaction.rating else 1)
                users_data[user_id][course_id] = weight
            
            # Build vectors for all users
            all_course_ids = set()
            for user_courses in users_data.values():
                all_course_ids.update(user_courses.keys())
            
            course_id_list = sorted(list(all_course_ids))
            
            # Create user vector
            user_vector = {}
            for course_id in course_id_list:
                user_vector[course_id] = users_data.get(self.user.id, {}).get(course_id, 0)
            
            user_vector_array = np.array([user_vector[cid] for cid in course_id_list])
            
            if np.sum(user_vector_array) == 0:
                return {}
            
            # Calculate similarity with other users
            similarities = {}
            for other_user_id, other_courses in users_data.items():
                if other_user_id == self.user.id:
                    continue
                
                other_vector = np.array([other_courses.get(cid, 0) for cid in course_id_list])
                
                # Compute cosine similarity
                sim = cosine_similarity(
                    user_vector_array.reshape(1, -1),
                    other_vector.reshape(1, -1)
                )[0][0]
                
                if sim > 0:
                    similarities[other_user_id] = sim
            
            # Get courses liked by similar users
            collab_scores = {}
            for other_user_id, similarity in sorted(
                similarities.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]:  # Top 10 similar users
                other_courses = users_data[other_user_id]
                for course_id, rating in other_courses.items():
                    # Skip courses user already interacted with
                    if course_id not in user_vector or user_vector[course_id] == 0:
                        if course_id not in collab_scores:
                            collab_scores[course_id] = 0
                        collab_scores[course_id] += rating * similarity
            
            return collab_scores
        
        except Exception as e:
            logger.error(f"Error in collaborative filtering: {str(e)}", exc_info=True)
            return {}
    
    def _content_based_filtering(self):
        """
        Content-based filtering using course feature vectors
        Recommend courses similar to ones user liked
        """
        
        try:
            # Get user's rated courses
            user_rated_courses = self.user_interactions.filter(
                interaction_type__in=['rate', 'complete'],
                rating__isnull=False
            ).values_list('course_id', 'rating')
            
            if not user_rated_courses:
                return {}
            
            user_liked_ids = [course_id for course_id, rating in user_rated_courses if rating >= 3]
            
            if not user_liked_ids:
                return {}
            
            # Get feature vectors for user's liked courses
            liked_courses = CourseVector.objects.filter(course_id__in=user_liked_ids)
            
            if not liked_courses:
                return {}
            
            # Calculate user profile as average of liked course vectors
            user_profile = {}
            for course in liked_courses:
                for feature, value in course.feature_vector.items():
                    user_profile[feature] = user_profile.get(feature, 0) + value
            
            # Normalize user profile
            num_courses = len(user_liked_ids)
            user_profile = {k: v / num_courses for k, v in user_profile.items()}
            
            # Calculate similarity with all courses
            all_courses = CourseVector.objects.all()
            content_scores = {}
            
            for course in all_courses:
                if course.course_id in user_liked_ids:
                    continue
                
                # Calculate cosine similarity between vectors
                user_vec = np.array(list(user_profile.values()))
                course_vec = np.array(list(course.feature_vector.values()))
                
                if len(user_vec) > 0 and len(course_vec) > 0:
                    similarity = cosine_similarity(
                        user_vec.reshape(1, -1),
                        course_vec.reshape(1, -1)
                    )[0][0]
                    
                    # Weight by course popularity
                    popularity_weight = min(course.avg_rating / 5.0, 1.0)
                    content_scores[course.course_id] = similarity * popularity_weight
            
            return content_scores
        
        except Exception as e:
            logger.error(f"Error in content-based filtering: {str(e)}", exc_info=True)
            return {}
    
    def _combine_scores(self, collab_scores, content_scores):
        """Combine collaborative and content-based scores"""
        
        combined_scores = {}
        all_course_ids = set(collab_scores.keys()) | set(content_scores.keys())
        
        for course_id in all_course_ids:
            collab_score = collab_scores.get(course_id, 0)
            content_score = content_scores.get(course_id, 0)
            
            # Weighted combination
            combined_score = (
                self.COLLABORATIVE_WEIGHT * collab_score +
                self.CONTENT_WEIGHT * content_score
            )
            
            combined_scores[course_id] = combined_score
        
        return combined_scores
    
    def _filter_recommendations(self, scores):
        """Filter out already enrolled/completed courses"""
        
        user_course_ids = self.user_interactions.values_list('course_id', flat=True)
        
        filtered = [
            {'course_id': course_id, 'score': score}
            for course_id, score in scores.items()
            if course_id not in user_course_ids
        ]
        
        return filtered
    
    def get_similar_courses(self, course_id, limit=5):
        """Get courses similar to a given course"""
        
        try:
            target_course = CourseVector.objects.get(course_id=course_id)
            all_courses = CourseVector.objects.exclude(course_id=course_id)
            
            similarities = {}
            target_vec = np.array(list(target_course.feature_vector.values()))
            
            for course in all_courses:
                course_vec = np.array(list(course.feature_vector.values()))
                
                if len(target_vec) > 0 and len(course_vec) > 0:
                    similarity = cosine_similarity(
                        target_vec.reshape(1, -1),
                        course_vec.reshape(1, -1)
                    )[0][0]
                    
                    similarities[course.course_id] = similarity
            
            similar = sorted(
                similarities.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return [{'course_id': cid, 'similarity': sim} for cid, sim in similar]
        
        except Exception as e:
            logger.error(f"Error finding similar courses: {str(e)}", exc_info=True)
            return []
    
    def update_interaction(self, course_id, interaction_type, rating=None, time_spent=0):
        """Record user-course interaction"""
        
        try:
            interaction_strength = self._calculate_strength(interaction_type, time_spent)
            
            interaction, created = UserCourseInteraction.objects.update_or_create(
                user=self.user,
                course_id=course_id,
                interaction_type=interaction_type,
                defaults={
                    'rating': rating,
                    'interaction_strength': interaction_strength,
                    'time_spent_minutes': time_spent,
                }
            )
            
            # Invalidate recommendation cache
            cache_key = f"recommendations:{self.user.id}"
            cache.delete(cache_key)
            
            logger.info(f"Interaction recorded: {self.user.email} - Course {course_id}")
            return interaction
        
        except Exception as e:
            logger.error(f"Error recording interaction: {str(e)}", exc_info=True)
            return None
    
    def _calculate_strength(self, interaction_type, time_spent=0):
        """Calculate interaction strength (0-1)"""
        
        base_strength = {
            'view': 0.3,
            'enroll': 0.5,
            'complete': 1.0,
            'rate': 0.6,
            'bookmark': 0.4,
        }.get(interaction_type, 0.5)
        
        # Boost by time spent
        time_bonus = min(time_spent / 100.0, 0.5)
        
        return min(base_strength + time_bonus, 1.0)
