from django.apps import AppConfig


class ProgressServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.progress_service'
    verbose_name = 'Progress Service'
