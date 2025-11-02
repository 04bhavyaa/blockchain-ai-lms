"""
Django admin for chatbot service
"""

from django.contrib import admin
from .models import Conversation, ChatMessage, ChatbotFeedback, FAQ, KnowledgeBase, ConversationContext


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_active', 'is_archived', 'last_message_at']
    list_filter = ['is_active', 'is_archived', 'created_at']
    search_fields = ['user__email', 'title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'tokens_used', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__email', 'content']
    readonly_fields = ['created_at']


@admin.register(ChatbotFeedback)
class ChatbotFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_rating_display', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__email', 'comment']
    readonly_fields = ['created_at']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['category', 'question', 'is_active', 'helpful_count']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'doc_type', 'source', 'is_active']
    list_filter = ['doc_type', 'is_active']
    search_fields = ['title', 'content']
