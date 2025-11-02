"""
AI Recommendations service URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RecommendationViewSet, UserPreferenceViewSet,
    RecommendationFeedbackViewSet, LearningPathViewSet
)

router = DefaultRouter()
router.register(r'feedback', RecommendationFeedbackViewSet, basename='recommendation-feedback')
router.register(r'preferences', UserPreferenceViewSet, basename='user-preferences')
router.register(r'paths', LearningPathViewSet, basename='learning-paths')

urlpatterns = [
    path('', include(router.urls)),
    path('for-me/', RecommendationViewSet.as_view({'get': 'for_me'}), name='recommendations-for-me'),
    path('trending/', RecommendationViewSet.as_view({'get': 'trending'}), name='recommendations-trending'),
    path('similar/', RecommendationViewSet.as_view({'get': 'similar'}), name='recommendations-similar'),
]
