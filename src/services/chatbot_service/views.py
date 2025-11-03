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

# Initialize RAG Engine - uses KnowledgeBase from database
try:
    from .models import KnowledgeBase
    
    chroma_db_dir = getattr(settings, "CHROMA_DB_DIR", "chroma_db")
    redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379")
    google_api_key = getattr(settings, "GOOGLE_API_KEY", None)
    
    # Get all active knowledge base items
    knowledge_base_queryset = KnowledgeBase.objects.all()
    
    rag_engine = RAGEngine(
        knowledge_base_queryset=knowledge_base_queryset,
        chroma_db_dir=chroma_db_dir,
        redis_url=redis_url,
        google_api_key=google_api_key
    )
    logger.info("RAG Engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RAG Engine: {str(e)}")
    rag_engine = None

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user
        ).prefetch_related('messages')
    def create(self, request, *args, **kwargs):
        title = request.data.get('title', 'New Conversation')
        description = request.data.get('description', '')
        session_id = request.data.get('session_id', None)
        if not session_id:
            # If not provided, create a unique id
            import uuid
            session_id = str(uuid.uuid4())
        try:
            conversation = Conversation.objects.create(
                user=request.user,
                session_id=session_id,
                title=title,
                description=description
            )
            ConversationContext.objects.create(conversation=conversation)
            logger.info(f"Conversation created: {request.user.email} - {title} [{session_id}]")
            return Response({
                'status': 'success',
                'data': ConversationSerializer(conversation).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise ValidationError(str(e))
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        try:
            conversation = self.get_object()
        except Conversation.DoesNotExist:
            raise ResourceNotFoundError("Conversation not found")
        messages = conversation.messages.order_by('created_at')
        serializer = ChatMessageSerializer(messages, many=True)
        return Response({'status': 'success', 'data': serializer.data})
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
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
    permission_classes = [IsAuthenticated]
    @action(detail=False, methods=['post'])
    def send_message(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.validated_data['message'].strip()
        conversation_id = serializer.validated_data.get('conversation_id')
        session_id = serializer.validated_data.get('session_id')
        import uuid
        if not session_id and conversation_id:
            try:
                # Use attached conversation's session_id
                conversation = Conversation.objects.get(
                    id=conversation_id,
                    user=request.user
                )
                session_id = conversation.session_id
            except Conversation.DoesNotExist:
                session_id = str(uuid.uuid4())
        elif not session_id:
            session_id = str(uuid.uuid4())
        try:
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
                    session_id=session_id,
                    title=user_message[:50] + ("..." if len(user_message) > 50 else "")
                )
                ConversationContext.objects.create(conversation=conversation)
            # Token restriction commented out for future use
            # Check token balance (2 tokens per non-FAQ query)
            # if request.user.token_balance < 2:
            #     raise ValidationError(
            #         f"Insufficient tokens. You need 2 tokens, you have {request.user.token_balance}"
            #     )
            chat_history = ChatMessage.objects.filter(
                conversation=conversation
            ).order_by('-created_at')[:10]
            history_data = [
                {'role': msg.role, 'content': msg.content}
                for msg in reversed(chat_history)
            ]
            faqs = FAQ.objects.filter(is_active=True).values('question', 'answer')
            faq_answer = None
            # Simple FAQ matching by keyword
            user_message_lower = user_message.lower()
            for faq in faqs:
                if any(word in user_message_lower for word in faq['question'].lower().split()[:3]):
                    faq_answer = faq['answer']
                    break
            
            if faq_answer:
                response_text = faq_answer
                tokens_for_query = 0
            else:
                # Use RAG pipeline or simple fallback
                if rag_engine:
                    response_text = rag_engine.get_chat_response(
                        user_message, session_id=session_id
                    )
                    tokens_for_query = 2
                else:
                    # Simple fallback response
                    response_text = "I'm here to help! This is a Blockchain + AI-powered Learning Management System. I can help you with questions about courses, tokens, certificates, wallets, and more. What would you like to know?"
                    tokens_for_query = 1
            user_msg = ChatMessage.objects.create(
                conversation=conversation,
                user=request.user,
                role='user',
                content=user_message,
                tokens_used=tokens_for_query
            )
            assistant_msg = ChatMessage.objects.create(
                conversation=conversation,
                user=request.user,
                role='assistant',
                content=response_text,
                tokens_used=0
            )
            # Token deduction commented out for future use
            # if tokens_for_query > 0:
            #     request.user.token_balance -= tokens_for_query
            #     request.user.save()
            conversation.last_message_at = timezone.now()
            conversation.save()
            context_obj = conversation.context
            context_obj.turn_count += 1
            context_obj.save()
            logger.info(
                f"Message processed: {request.user.email} - "
                f"Session: {session_id} - "
                f"Tokens used: {tokens_for_query} - Message: {user_message[:30]}..."
            )
            return Response({
                'status': 'success',
                'data': {
                    'conversation_id': conversation.id,
                    'session_id': conversation.session_id,
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
        conversations = Conversation.objects.filter(
            user=request.user,
            is_archived=False
        ).order_by('-last_message_at')
        page_size = request.query_params.get('page_size', 10)
        conversations = conversations[:int(page_size)]
        serializer = ConversationSerializer(conversations, many=True)
        return Response({'status': 'success', 'data': serializer.data})

class ChatbotFeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = ChatbotFeedbackSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return ChatbotFeedback.objects.filter(user=self.request.user)
    def create(self, request, *args, **kwargs):
        serializer = FeedbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            message_id = serializer.validated_data['message_id']
            try:
                message = ChatMessage.objects.get(
                    id=message_id,
                    user=request.user,
                    role='assistant'
                )
            except ChatMessage.DoesNotExist:
                raise ResourceNotFoundError("Message not found")
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
    serializer_class = FAQSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return FAQ.objects.filter(is_active=True)
    @action(detail=False, methods=['get'])
    def search(self, request):
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
        try:
            faq = self.get_object()
            faq.helpful_count += 1
            faq.save()
            return Response({'status': 'success', 'message': 'Thank you for your feedback'})
        except FAQ.DoesNotExist:
            raise ResourceNotFoundError("FAQ not found")

class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return KnowledgeBase.objects.filter(is_active=True)
    @action(detail=False, methods=['get'])
    def search(self, request):
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
