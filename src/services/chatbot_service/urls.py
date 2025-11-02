"""
Chatbot service URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationViewSet, ChatbotViewSet,
    ChatbotFeedbackViewSet, FAQViewSet, KnowledgeBaseViewSet
)

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversations')
router.register(r'feedback', ChatbotFeedbackViewSet, basename='feedback')
router.register(r'faqs', FAQViewSet, basename='faqs')
router.register(r'knowledge-base', KnowledgeBaseViewSet, basename='knowledge-base')

urlpatterns = [
    path('', include(router.urls)),
    path('send/', ChatbotViewSet.as_view({'post': 'send_message'}), name='send-message'),
    path('conversations-list/', ChatbotViewSet.as_view({'get': 'conversations'}), name='conversations-list'),
]
