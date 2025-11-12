# src/services/ai_recommendations/apps.py

from django.apps import AppConfig


class AiRecommendationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.ai_recommendations'
    verbose_name = "AI Recommendations Service"
    
    def ready(self):
        """Import signals - with error handling for missing dependencies"""
        try:
            import src.services.ai_recommendations.signals  # noqa
        except (ImportError, OSError) as e:
            # Log the error but don't crash the application
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"AI Recommendations signals not loaded: {e}. "
                "AI features will be disabled."
            )
