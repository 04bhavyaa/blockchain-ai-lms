from django.urls import path
from .views import FAQListView, ChatView, ConversationHistoryView

urlpatterns = [
    path('faqs/', FAQListView.as_view(), name='faq-list'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('history/', ConversationHistoryView.as_view(), name='chat-history'),
]
