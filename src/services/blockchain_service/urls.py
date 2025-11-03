from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OnChainPaymentViewSet, CertificateViewSet, BlockchainStatsViewSet

router = DefaultRouter()
router.register(r'certificates', CertificateViewSet, basename='certificates')
router.register(r'stats', BlockchainStatsViewSet, basename='blockchain-stats')

urlpatterns = [
    path('', include(router.urls)),
    path('payment/request-approval/', OnChainPaymentViewSet.as_view({'post': 'request_approval'}), name='request-approval'),
    path('payment/confirm-payment/', OnChainPaymentViewSet.as_view({'post': 'confirm_payment'}), name='confirm-payment'),
    path('payment/history/', OnChainPaymentViewSet.as_view({'get': 'payment_history'}), name='payment-history'),
]
