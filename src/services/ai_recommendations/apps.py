from django.apps import AppConfig


class AiRecommendationServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.ai_recommendations'
    verbose_name = 'AI Recommendation Service'
    
    def ready(self):
        """Import signals when app is ready"""
        import src.services.ai_recommendations.signals  # noqa
