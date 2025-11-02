"""
Chatbot Service Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
import logging

from .models import Conversation, ChatMessage, ChatbotFeedback, FAQ, KnowledgeBase, ConversationContext
from .serializers import (
    ChatMessageSerializer, ConversationSerializer,
    SendMessageSerializer, ChatbotFeedbackSerializer,
    FeedbackRequestSerializer, FAQSerializer, KnowledgeBaseSerializer
)
from .rag_engine import RAGEngine
from src.shared.exceptions import ValidationError, BlockchainError, ResourceNotFoundError
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize RAG Engine
try:
    google_api_key = settings.GOOGLE_API_KEY
    rag_engine = RAGEngine(google_api_key)
    logger.info("RAG Engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RAG Engine: {str(e)}")
    rag_engine = None


class ConversationViewSet(viewsets.ModelViewSet):
    """Manage conversations"""
    
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user
        ).prefetch_related('messages')
    
    def create(self, request, *args, **kwargs):
        """Create new conversation"""
        title = request.data.get('title', 'New Conversation')
        description = request.data.get('description', '')
        
        try:
            conversation = Conversation.objects.create(
                user=request.user,
                title=title,
                description=description
            )
            
            # Create context
            ConversationContext.objects.create(conversation=conversation)
            
            logger.info(f"Conversation created: {request.user.email} - {title}")
            
            return Response({
                'status': 'success',
                'data': ConversationSerializer(conversation).data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise ValidationError(str(e))
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get conversation messages"""
        try:
            conversation = self.get_object()
        except Conversation.DoesNotExist:
            raise ResourceNotFoundError("Conversation not found")
        
        messages = conversation.messages.order_by('created_at')
        serializer = ChatMessageSerializer(messages, many=True)
        
        return Response({'status': 'success', 'data': serializer.data})
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive conversation"""
        try:
            conversation = self.get_object()
            conversation.is_archived = True
            conversation.save()
            
            return Response({
                'status': 'success',
                'message': 'Conversation archived'
            })
        except Conversation.DoesNotExist:
            raise ResourceNotFoundError("Conversation not found")


class ChatbotViewSet(viewsets.ViewSet):
    """Chatbot interaction endpoint"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """Send message to chatbot"""
        
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_message = serializer.validated_data['message'].strip()
        conversation_id = serializer.validated_data.get('conversation_id')
        
        try:
            # Validate message
            if not user_message or len(user_message) < 1:
                raise ValidationError("Message cannot be empty")
            
            if len(user_message) > 2000:
                raise ValidationError("Message is too long (max 2000 characters)")
            
            # Get or create conversation
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(
                        id=conversation_id,
                        user=request.user
                    )
                except Conversation.DoesNotExist:
                    raise ResourceNotFoundError("Conversation not found")
            else:
                conversation = Conversation.objects.create(
                    user=request.user,
                    title=user_message[:50] + ("..." if len(user_message) > 50 else "")
                )
                ConversationContext.objects.create(conversation=conversation)
            
            # Check token balance (2 tokens per query)
            if request.user.token_balance < 2:
                raise ValidationError(
                    f"Insufficient tokens. You need 2 tokens, you have {request.user.token_balance}"
                )
            
            # Get conversation history (last 10 messages)
            chat_history = ChatMessage.objects.filter(
                conversation=conversation
            ).order_by('-created_at')[:10]
            
            history_data = [
                {'role': msg.role, 'content': msg.content}
                for msg in reversed(chat_history)
            ]
            
            # Try FAQ first
            faqs = FAQ.objects.filter(is_active=True).values('question', 'answer')
            faq_answer = rag_engine.answer_faq(user_message, list(faqs)) if rag_engine else None
            
            if faq_answer:
                response_text = faq_answer
                tokens_for_query = 0  # FAQ queries are free
            else:
                # Retrieve context from knowledge base
                context = []
                if rag_engine:
                    context = rag_engine.retrieve_context(user_message, k=3)
                
                # Generate response using LLM
                if rag_engine:
                    response_text = rag_engine.generate_response(
                        user_message,
                        context=context,
                        chat_history=history_data
                    )
                else:
                    response_text = "Chatbot service is temporarily unavailable. Please try again later."
                
                tokens_for_query = 2
            
            # Save user message
            user_msg = ChatMessage.objects.create(
                conversation=conversation,
                user=request.user,
                role='user',
                content=user_message,
                tokens_used=tokens_for_query
            )
            
            # Save assistant message
            assistant_msg = ChatMessage.objects.create(
                conversation=conversation,
                user=request.user,
                role='assistant',
                content=response_text,
                tokens_used=0
            )
            
            # Deduct tokens
            if tokens_for_query > 0:
                request.user.token_balance -= tokens_for_query
                request.user.save()
            
            # Update conversation
            conversation.last_message_at = timezone.now()
            conversation.save()
            
            # Update context
            context_obj = conversation.context
            context_obj.turn_count += 1
            context_obj.save()
            
            logger.info(
                f"Message processed: {request.user.email} - "
                f"Tokens used: {tokens_for_query} - Message: {user_message[:30]}..."
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'conversation_id': conversation.id,
                    'user_message': ChatMessageSerializer(user_msg).data,
                    'assistant_message': ChatMessageSerializer(assistant_msg).data,
                    'tokens_remaining': request.user.token_balance,
                    'tokens_used': tokens_for_query,
                }
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise BlockchainError(str(e))
    
    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """Get user's conversations"""
        
        conversations = Conversation.objects.filter(
            user=request.user,
            is_archived=False
        ).order_by('-last_message_at')
        
        page_size = request.query_params.get('page_size', 10)
        conversations = conversations[:int(page_size)]
        
        serializer = ConversationSerializer(conversations, many=True)
        return Response({'status': 'success', 'data': serializer.data})


class ChatbotFeedbackViewSet(viewsets.ModelViewSet):
    """Chatbot feedback"""
    
    serializer_class = ChatbotFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatbotFeedback.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Submit feedback"""
        
        serializer = FeedbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            message_id = serializer.validated_data['message_id']
            
            # Get message
            try:
                message = ChatMessage.objects.get(
                    id=message_id,
                    user=request.user,
                    role='assistant'
                )
            except ChatMessage.DoesNotExist:
                raise ResourceNotFoundError("Message not found")
            
            # Create feedback
            feedback = ChatbotFeedback.objects.create(
                user=request.user,
                message=message,
                rating=serializer.validated_data['rating'],
                comment=serializer.validated_data.get('comment', '')
            )
            
            logger.info(
                f"Feedback submitted: {request.user.email} - "
                f"Rating: {feedback.rating}/5"
            )
            
            return Response({
                'status': 'success',
                'message': 'Feedback submitted successfully',
                'data': ChatbotFeedbackSerializer(feedback).data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            raise ValidationError(str(e))


class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    """FAQ management"""
    
    serializer_class = FAQSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FAQ.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search FAQs"""
        
        query = request.query_params.get('q', '')
        category = request.query_params.get('category')
        
        faqs = FAQ.objects.filter(is_active=True)
        
        if query:
            faqs = faqs.filter(
                Q(question__icontains=query) |
                Q(answer__icontains=query)
            )
        
        if category:
            faqs = faqs.filter(category=category)
        
        serializer = self.get_serializer(faqs, many=True)
        return Response({'status': 'success', 'data': serializer.data})
    
    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark FAQ as helpful"""
        try:
            faq = self.get_object()
            faq.helpful_count += 1
            faq.save()
            
            return Response({'status': 'success', 'message': 'Thank you for your feedback'})
        except FAQ.DoesNotExist:
            raise ResourceNotFoundError("FAQ not found")


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """Knowledge base management"""
    
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return KnowledgeBase.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search knowledge base"""
        
        query = request.query_params.get('q', '')
        doc_type = request.query_params.get('type')
        
        docs = KnowledgeBase.objects.filter(is_active=True)
        
        if query:
            docs = docs.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )
        
        if doc_type:
            docs = docs.filter(doc_type=doc_type)
        
        serializer = self.get_serializer(docs, many=True)
        return Response({'status': 'success', 'data': serializer.data})
