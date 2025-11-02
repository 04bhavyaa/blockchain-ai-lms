from django.apps import AppConfig


class ChatbotServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.chatbot_service'
    verbose_name = 'Chatbot Service'
