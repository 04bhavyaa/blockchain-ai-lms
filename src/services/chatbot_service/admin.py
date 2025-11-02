from django.contrib import admin
from .models import (
    Conversation, ChatMessage, ChatbotFeedback,
    FAQ, KnowledgeBase, ConversationContext
)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'session_id', 'title', 'is_active', 'is_archived', 'last_message_at',
        'blockchain_event_tx_hash'
    ]
    list_filter = ['is_active', 'is_archived', 'created_at']
    search_fields = ['user__email', 'title', 'session_id']
    readonly_fields = ['created_at', 'updated_at', 'blockchain_event_tx_hash', 'last_blockchain_status', 'session_id']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'role', 'tokens_used', 'is_flagged', 'created_at',
        'blockchain_event_tx_hash'
    ]
    list_filter = ['role', 'is_flagged', 'created_at']
    search_fields = ['user__email', 'content']
    readonly_fields = ['created_at', 'blockchain_event_tx_hash', 'last_blockchain_status']

@admin.register(ChatbotFeedback)
class ChatbotFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'get_rating_display', 'created_at', 'blockchain_event_tx_hash'
    ]
    list_filter = ['rating', 'created_at']
    search_fields = ['user__email', 'comment']
    readonly_fields = ['created_at', 'blockchain_event_tx_hash', 'last_blockchain_status']

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = [
        'category', 'question', 'is_active', 'helpful_count',
        'blockchain_event_tx_hash'
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    readonly_fields = ['blockchain_event_tx_hash', 'last_blockchain_status']

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'doc_type', 'source', 'is_active',
        'blockchain_event_tx_hash'
    ]
    list_filter = ['doc_type', 'is_active']
    search_fields = ['title', 'content']
    readonly_fields = ['blockchain_event_tx_hash', 'last_blockchain_status']

@admin.register(ConversationContext)
class ConversationContextAdmin(admin.ModelAdmin):
    list_display = [
        'conversation', 'last_topic', 'turn_count', 'updated_at',
        'blockchain_event_tx_hash'
    ]
    search_fields = ['conversation__title', 'last_topic']
    readonly_fields = ['updated_at', 'blockchain_event_tx_hash', 'last_blockchain_status']
