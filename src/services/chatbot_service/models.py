"""
Chatbot Service Models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Conversation(models.Model):
    """Chat conversation/thread"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'conversations'
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['user', '-last_message_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


class ChatMessage(models.Model):
    """Individual chat messages"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # Token tracking
    tokens_used = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.role} - {self.created_at}"


class ChatbotFeedback(models.Model):
    """Feedback on chatbot responses"""
    
    RATING_CHOICES = [
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Neutral'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_feedbacks')
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chatbot_feedbacks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_rating_display()}"


class FAQ(models.Model):
    """FAQ database for quick answers"""
    
    category = models.CharField(max_length=100)
    question = models.TextField()
    answer = models.TextField()
    keywords = models.JSONField(default=list, help_text="Keywords for matching")
    
    is_active = models.BooleanField(default=True)
    views = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'faqs'
        ordering = ['category', 'question']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.category} - {self.question[:50]}"


class KnowledgeBase(models.Model):
    """Knowledge base documents for RAG"""
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    source = models.CharField(max_length=255)
    
    # Type
    doc_type = models.CharField(
        max_length=50,
        choices=[
            ('course', 'Course Material'),
            ('policy', 'Policy'),
            ('faq', 'FAQ'),
            ('guide', 'Guide'),
            ('other', 'Other'),
        ]
    )
    
    is_active = models.BooleanField(default=True)
    embedding_vector = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'knowledge_bases'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['doc_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.doc_type})"


class ConversationContext(models.Model):
    """Store context for multi-turn conversations"""
    
    conversation = models.OneToOneField(
        Conversation,
        on_delete=models.CASCADE,
        related_name='context'
    )
    
    # Context data
    retrieved_docs = models.JSONField(default=list)
    conversation_summary = models.TextField(blank=True)
    user_intent = models.CharField(max_length=255, blank=True)
    
    # State
    last_topic = models.CharField(max_length=255, blank=True)
    turn_count = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'conversation_contexts'
    
    def __str__(self):
        return f"Context for {self.conversation.title}"
