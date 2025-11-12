import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from django.conf import settings
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging
from src.shared.constants import RECOMMENDATION_WEIGHTS

from .models import (
    UserPreference, CourseVector, UserCourseInteraction,
    RecommendationCache, RecommendationFeedback
)

logger = logging.getLogger(__name__)


"""
Hybrid recommendation engine with Qdrant vector search
"""
class QdrantRecommendationEngine:
    """
    Enhanced recommendation engine using Qdrant vector database
    """
    
    def __init__(self, user):
        self.user = user
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions
        self.qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.collection_name = "course_embeddings"
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # Dimension of all-MiniLM-L6-v2
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {str(e)}")
    
    def generate_user_profile_embedding(self):
        """
        Generate user profile embedding from interests and education
        """
        try:
            # Get user profile data
            profile_text = []
            
            # Add interests from user model
            if hasattr(self.user, 'learning_goals') and self.user.learning_goals:
                profile_text.append(f"Interests: {self.user.learning_goals}")
            
            # Add education level
            if hasattr(self.user, 'education_level') and self.user.education_level:
                profile_text.append(f"Education: {self.user.education_level}")
            
            # Get user preferences
            try:
                preference = UserPreference.objects.get(user=self.user)
                if preference.preferred_categories:
                    categories = ", ".join(preference.preferred_categories)
                    profile_text.append(f"Preferred categories: {categories}")
                
                if preference.preferred_difficulty:
                    profile_text.append(f"Skill level: {preference.preferred_difficulty}")
                
                if preference.learning_style:
                    profile_text.append(f"Learning style: {preference.learning_style}")
            except UserPreference.DoesNotExist:
                pass
            
            # Combine all profile information
            if not profile_text:
                profile_text = ["General learner seeking knowledge"]
            
            combined_profile = " | ".join(profile_text)
            logger.info(f"User profile text: {combined_profile}")
            
            # Generate embedding
            embedding = self.embedding_model.encode(combined_profile)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating user profile embedding: {str(e)}", exc_info=True)
            return None
    
    def index_course_to_qdrant(self, course):
        """
        Index a single course to Qdrant
        Args:
            course: Course model instance from courses_service
        """
        try:
            # Create course text for embedding
            course_text = self._create_course_text(course)
            
            # Generate embedding
            embedding = self.embedding_model.encode(course_text)
            
            # Create point for Qdrant
            point = PointStruct(
                id=course.id,
                vector=embedding.tolist(),
                payload={
                    "course_id": course.id,
                    "title": course.title,
                    "description": course.description[:500],  # Truncate
                    "category": course.category.name if course.category else "",
                    "difficulty_level": course.difficulty_level,
                    "access_type": course.access_type,
                    "token_cost": int(course.token_cost),
                    "price_usd": float(course.price_usd),
                    "average_rating": float(course.average_rating),
                    "total_enrollments": course.total_enrollments,
                    "is_featured": course.is_featured,
                }
            )
            
            # Upsert to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Indexed course {course.id} to Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing course {course.id}: {str(e)}", exc_info=True)
            return False
    
    def _create_course_text(self, course):
        """Create searchable text representation of course"""
        parts = [
            f"Title: {course.title}",
            f"Description: {course.description}",
            f"Category: {course.category.name if course.category else 'Uncategorized'}",
            f"Level: {course.difficulty_level}",
        ]
        
        if hasattr(course, 'tags') and course.tags:
            parts.append(f"Tags: {', '.join(course.tags)}")
        
        return " | ".join(parts)
    
    def get_recommendations(self, limit=10):
        """
        Get personalized recommendations using Qdrant vector search
        """
        cache_key = f"qdrant_recs:{self.user.id}"
        cached_recs = cache.get(cache_key)
        
        if cached_recs:
            logger.info(f"Cache hit for Qdrant recommendations: {self.user.email}")
            return cached_recs[:limit]
        
        try:
            # Generate user profile embedding
            user_embedding = self.generate_user_profile_embedding()
            
            if not user_embedding:
                logger.warning("Could not generate user embedding, using fallback")
                return self._fallback_recommendations(limit)
            
            # Get already enrolled course IDs to filter out
            enrolled_course_ids = list(
                UserCourseInteraction.objects.filter(
                    user=self.user,
                    interaction_type__in=['enroll', 'complete']
                ).values_list('course_id', flat=True)
            )
            
            # Search Qdrant for similar courses
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=user_embedding,
                limit=limit * 3,  # Get more to filter
                with_payload=True
            )
            
            # Filter and format results
            recommendations = []
            for scored_point in search_result:
                course_id = scored_point.payload['course_id']
                
                # Skip enrolled courses
                if course_id in enrolled_course_ids:
                    continue
                
                recommendations.append({
                    'course_id': course_id,
                    'title': scored_point.payload['title'],
                    'description': scored_point.payload['description'],
                    'category': scored_point.payload['category'],
                    'difficulty_level': scored_point.payload['difficulty_level'],
                    'access_type': scored_point.payload['access_type'],
                    'token_cost': scored_point.payload['token_cost'],
                    'price_usd': scored_point.payload['price_usd'],
                    'average_rating': scored_point.payload['average_rating'],
                    'total_enrollments': scored_point.payload['total_enrollments'],
                    'is_featured': scored_point.payload['is_featured'],
                    'score': float(scored_point.score),
                    'match_percentage': round(float(scored_point.score) * 100, 2)
                })
                
                if len(recommendations) >= limit:
                    break
            
            # Cache results
            cache.set(cache_key, recommendations, 900)  # 15 minutes
            
            logger.info(f"Generated {len(recommendations)} Qdrant recommendations for {self.user.email}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in Qdrant recommendations: {str(e)}", exc_info=True)
            return self._fallback_recommendations(limit)
    
    def _fallback_recommendations(self, limit):
        """Fallback to popular courses if Qdrant fails"""
        try:
            from src.services.courses_service.models import Course
            
            courses = Course.objects.filter(
                status='published'
            ).order_by('-is_featured', '-total_enrollments', '-average_rating')[:limit]
            
            recommendations = []
            for course in courses:
                recommendations.append({
                    'course_id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'category': course.category.name if course.category else '',
                    'difficulty_level': course.difficulty_level,
                    'access_type': course.access_type,
                    'token_cost': course.token_cost,
                    'price_usd': float(course.price_usd),
                    'average_rating': float(course.average_rating),
                    'total_enrollments': course.total_enrollments,
                    'is_featured': course.is_featured,
                    'score': 0.5,
                    'match_percentage': 50.0
                })
            
            return recommendations
        except Exception as e:
            logger.error(f"Fallback also failed: {str(e)}")
            return []
    
    def bulk_index_courses(self):
        """Index all published courses to Qdrant"""
        try:
            from src.services.courses_service.models import Course
            
            courses = Course.objects.filter(status='published')
            total = courses.count()
            
            logger.info(f"Starting bulk indexing of {total} courses to Qdrant...")
            
            points = []
            for course in courses:
                course_text = self._create_course_text(course)
                embedding = self.embedding_model.encode(course_text)
                
                point = PointStruct(
                    id=course.id,
                    vector=embedding.tolist(),
                    payload={
                        "course_id": course.id,
                        "title": course.title,
                        "description": course.description[:500],
                        "category": course.category.name if course.category else "",
                        "difficulty_level": course.difficulty_level,
                        "access_type": course.access_type,
                        "token_cost": int(course.token_cost),
                        "price_usd": float(course.price_usd),
                        "average_rating": float(course.average_rating),
                        "total_enrollments": course.total_enrollments,
                        "is_featured": course.is_featured,
                    }
                )
                points.append(point)
                
                # Batch upsert every 100 courses
                if len(points) >= 100:
                    self.qdrant_client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    logger.info(f"Indexed batch of {len(points)} courses")
                    points = []
            
            # Upsert remaining
            if points:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
            
            logger.info(f"Successfully indexed {total} courses to Qdrant")
            return {"status": "success", "indexed": total}
            
        except Exception as e:
            logger.error(f"Error bulk indexing courses: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

# """
# Hybrid recommendation engine combining collaborative and content-based filtering
# """
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