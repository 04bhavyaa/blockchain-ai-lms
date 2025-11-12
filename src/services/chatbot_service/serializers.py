from rest_framework import serializers
from .models import (
    Conversation, ChatMessage, FAQ
)

class ChatMessageSerializer(serializers.ModelSerializer):
    """Chat message serializer"""
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'role', 'content', 'tokens_used',
            'metadata', 'is_flagged', 'blockchain_event_tx_hash', 'last_blockchain_status',
            'created_at'
        ]
        read_only_fields = [
            'id', 'tokens_used', 'created_at', 'blockchain_event_tx_hash', 'last_blockchain_status'
        ]

class ConversationSerializer(serializers.ModelSerializer):
    """Conversation serializer"""
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'session_id', 'title', 'description', 'is_active', 'is_archived',
            'message_count', 'last_message', 'blockchain_event_tx_hash', 'last_blockchain_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'session_id', 'created_at', 'updated_at', 'blockchain_event_tx_hash', 'last_blockchain_status'
        ]
    def get_message_count(self, obj):
        return obj.messages.count()
    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        return ChatMessageSerializer(last_msg).data if last_msg else None

class SendMessageSerializer(serializers.Serializer):
    """Send message request"""
    message = serializers.CharField(max_length=2000)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    session_id = serializers.CharField(max_length=128, required=False, allow_blank=True)

# class ChatbotFeedbackSerializer(serializers.ModelSerializer):
#     """Chatbot feedback serializer"""
#     class Meta:
#         model = ChatbotFeedback
#         fields = [
#             'id', 'message', 'rating', 'comment',
#             'blockchain_event_tx_hash', 'last_blockchain_status', 'created_at'
#         ]
#         read_only_fields = [
#             'id', 'created_at', 'blockchain_event_tx_hash', 'last_blockchain_status'
#         ]

class FeedbackRequestSerializer(serializers.Serializer):
    """Submit feedback request"""
    message_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=500, required=False, allow_blank=True)

class FAQSerializer(serializers.ModelSerializer):
    """FAQ serializer"""
    class Meta:
        model = FAQ
        fields = [
            'id', 'category', 'question', 'answer', 'keywords',
            'views', 'helpful_count', 'blockchain_event_tx_hash', 'last_blockchain_status'
        ]
        read_only_fields = [
            'id', 'views', 'helpful_count', 'blockchain_event_tx_hash', 'last_blockchain_status'
        ]

# class KnowledgeBaseSerializer(serializers.ModelSerializer):
#     """Knowledge base serializer"""
#     class Meta:
#         model = KnowledgeBase
#         fields = [
#             'id', 'title', 'content', 'source', 'doc_type',
#             'is_active', 'embedding_vector', 'blockchain_event_tx_hash', 'last_blockchain_status',
#             'created_at', 'updated_at'
#         ]
#         read_only_fields = [
#             'id', 'created_at', 'updated_at', 'blockchain_event_tx_hash', 'last_blockchain_status'
#         ]

# class ConversationContextSerializer(serializers.ModelSerializer):
#     """Conversation context serializer"""
#     class Meta:
#         model = ConversationContext
#         fields = [
#             'id', 'retrieved_docs', 'conversation_summary', 'user_intent', 'last_topic',
#             'turn_count', 'blockchain_event_tx_hash', 'last_blockchain_status', 'updated_at'
#         ]
#         read_only_fields = [
#             'id', 'updated_at', 'blockchain_event_tx_hash', 'last_blockchain_status'
#         ]
