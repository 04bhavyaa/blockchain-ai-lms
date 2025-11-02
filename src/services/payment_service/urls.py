"""
Payment service URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TokenPackageViewSet, StripePurchaseViewSet,
    RefundViewSet, WebhookViewSet
)

router = DefaultRouter()
router.register(r'packages', TokenPackageViewSet, basename='token-packages')
router.register(r'purchases', StripePurchaseViewSet, basename='stripe-purchases')
router.register(r'refunds', RefundViewSet, basename='refunds')
router.register(r'webhooks', WebhookViewSet, basename='webhooks')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/stripe/', WebhookViewSet.as_view({'post': 'stripe_webhook'}), name='stripe-webhook'),
]
