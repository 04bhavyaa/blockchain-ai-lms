from django.apps import AppConfig


class AdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.admin_service'
    verbose_name = 'Admin Management'
