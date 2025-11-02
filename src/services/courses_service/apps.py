from django.apps import AppConfig


class CoursesServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.courses_service'
    verbose_name = 'Courses Service'
