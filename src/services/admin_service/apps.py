"""
Admin service app configuration
"""
from django.apps import AppConfig


class AdminServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.admin_service'
    verbose_name = 'Admin Service'
    
    def ready(self):
        """Import signals when app is ready"""
        import src.services.admin_service.signals  # noqa