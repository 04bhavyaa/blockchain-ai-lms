from django.apps import AppConfig


class AuthServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.auth_service'
    verbose_name = 'Authentication Service'
