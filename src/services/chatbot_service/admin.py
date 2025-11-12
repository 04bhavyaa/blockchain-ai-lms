from django.contrib import admin
from .models import (
    Conversation, ChatMessage, FAQ
)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'session_id', 'created_at', 'updated_at'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'session_id']
    readonly_fields = ['created_at', 'updated_at', 'session_id']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = [
        'conversation', 'role', 'timestamp'
    ]
    list_filter = ['role', 'timestamp']
    search_fields = ['content']
    readonly_fields = ['timestamp']

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = [
        'question', 'is_active', 'order'
    ]
    list_filter = ['is_active']
    search_fields = ['question', 'answer']
    ordering = ['order']

# @admin.register(KnowledgeBase)
# class KnowledgeBaseAdmin(admin.ModelAdmin):
#     list_display = [
#         'title', 'doc_type', 'source', 'is_active',
#         'blockchain_event_tx_hash'
#     ]
#     list_filter = ['doc_type', 'is_active']
#     search_fields = ['title', 'content']
#     readonly_fields = ['blockchain_event_tx_hash', 'last_blockchain_status']

# @admin.register(ConversationContext)
# class ConversationContextAdmin(admin.ModelAdmin):
#     list_display = [
#         'conversation', 'last_topic', 'turn_count', 'updated_at',
#         'blockchain_event_tx_hash'
#     ]
#     search_fields = ['conversation__title', 'last_topic']
#     readonly_fields = ['updated_at', 'blockchain_event_tx_hash', 'last_blockchain_status']
