from django.apps import AppConfig


class PaymentServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.payment_service'
    verbose_name = 'Payment Service'
