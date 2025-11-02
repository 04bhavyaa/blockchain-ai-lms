"""
Admin service URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminUserViewSet, AdminLogsViewSet, FraudDetectionViewSet,
    AdminSettingsViewSet, DashboardStatsViewSet
)

router = DefaultRouter()
router.register(r'users', AdminUserViewSet, basename='admin-users')
router.register(r'logs', AdminLogsViewSet, basename='admin-logs')
router.register(r'fraud', FraudDetectionViewSet, basename='fraud-detection')
router.register(r'settings', AdminSettingsViewSet, basename='admin-settings')
router.register(r'stats', DashboardStatsViewSet, basename='dashboard-stats')

urlpatterns = [
    path('', include(router.urls)),
]
