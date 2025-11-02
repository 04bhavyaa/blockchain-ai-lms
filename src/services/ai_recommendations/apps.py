from django.apps import AppConfig


class AiRecommendationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.ai_recommendations'
    verbose_name = 'AI Recommendations Engine'
