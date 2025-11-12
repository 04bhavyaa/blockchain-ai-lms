from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Conversation(models.Model):
    """Single chat session per user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    session_id = models.CharField(max_length=128, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'conversations'
        ordering = ['-updated_at']

class ChatMessage(models.Model):
    """Messages in conversation"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['timestamp']

class FAQ(models.Model):
    """Quick FAQ bubbles for chat interface"""
    question = models.CharField(max_length=255, unique=True)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)  # For bubble ordering
    
    class Meta:
        db_table = 'faqs'
        ordering = ['order']