from django.apps import AppConfig


class BlockchainServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.blockchain_service'
    verbose_name = 'Blockchain Service'
