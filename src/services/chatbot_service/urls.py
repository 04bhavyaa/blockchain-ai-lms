from django.urls import path
from .views import FAQListView, ChatView, ConversationHistoryView

urlpatterns = [
    path('faqs/', FAQListView.as_view(), name='faq-list'),
    path('message/', ChatView.as_view(), name='chat-message'),  # Main endpoint
    path('chat/', ChatView.as_view(), name='chat'),  # Alternative
    path('history/', ConversationHistoryView.as_view(), name='chat-history'),
]
