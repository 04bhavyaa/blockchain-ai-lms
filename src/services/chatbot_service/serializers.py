"""
Chatbot service serializers
"""

from rest_framework import serializers
from .models import Conversation, ChatMessage, ChatbotFeedback, FAQ, KnowledgeBase


class ChatMessageSerializer(serializers.ModelSerializer):
    """Chat message serializer"""
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'role', 'content', 'tokens_used',
            'metadata', 'created_at'
        ]
        read_only_fields = [
            'id', 'tokens_used', 'created_at'
        ]


class ConversationSerializer(serializers.ModelSerializer):
    """Conversation serializer"""
    
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'description', 'is_active', 'is_archived',
            'message_count', 'last_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        return ChatMessageSerializer(last_msg).data if last_msg else None


class SendMessageSerializer(serializers.Serializer):
    """Send message request"""
    
    message = serializers.CharField(max_length=2000)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)


class ChatbotFeedbackSerializer(serializers.ModelSerializer):
    """Chatbot feedback serializer"""
    
    class Meta:
        model = ChatbotFeedback
        fields = [
            'id', 'message', 'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


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
            'views', 'helpful_count'
        ]
        read_only_fields = ['id', 'views', 'helpful_count']


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    """Knowledge base serializer"""
    
    class Meta:
        model = KnowledgeBase
        fields = [
            'id', 'title', 'content', 'source', 'doc_type',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
