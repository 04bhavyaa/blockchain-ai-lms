"""
Signals for auto-indexing courses to Qdrant
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from src.services.courses_service.models import Course
from .recommendation_engine import QdrantRecommendationEngine
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=Course)
def index_course_to_qdrant(sender, instance, created, **kwargs):
    """
    Automatically index course to Qdrant when created or updated
    """
    if instance.status == 'published':
        try:
            # Get any admin user for indexing
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                engine = QdrantRecommendationEngine(admin_user)
                engine.index_course_to_qdrant(instance)
                logger.info(f"Auto-indexed course {instance.id} to Qdrant")
        except Exception as e:
            logger.error(f"Failed to auto-index course {instance.id}: {str(e)}")
