from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .models import Conversation, ChatMessage, FAQ
from .rag_engine import SimpleRAGEngine
import uuid

# Initialize RAG engine
rag_engine = SimpleRAGEngine(
    qdrant_url=settings.QDRANT_URL,
    redis_url=settings.REDIS_URL,
    document_path=settings.PROJECT_DOC_PATH
)

class FAQListView(APIView):
    """Get 5 FAQ bubbles for chat interface"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        faqs = FAQ.objects.filter(is_active=True)[:5]
        data = [{"id": faq.id, "question": faq.question} for faq in faqs]
        return Response(data)

class ChatView(APIView):
    """Handle chat messages (FAQ or custom query)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user_message = request.data.get('message', '').strip()
        faq_id = request.data.get('faq_id')  # Optional: if user clicked FAQ bubble
        
        if not user_message and not faq_id:
            return Response({"error": "Message or FAQ ID required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create conversation
        conversation, created = Conversation.objects.get_or_create(
            user=request.user,
            defaults={'session_id': str(uuid.uuid4())}
        )
        
        # If FAQ bubble clicked, get predefined answer
        if faq_id:
            try:
                faq = FAQ.objects.get(id=faq_id, is_active=True)
                user_message = faq.question
                assistant_response = faq.answer
            except FAQ.DoesNotExist:
                return Response({"error": "FAQ not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Use RAG engine for custom query
            assistant_response = rag_engine.chat(
                session_id=conversation.session_id,
                user_message=user_message
            )
        
        # Save messages
        ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content=user_message
        )
        
        ChatMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=assistant_response
        )
        
        return Response({
            "message": assistant_response,
            "session_id": conversation.session_id
        })

class ConversationHistoryView(APIView):
    """Get chat history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            conversation = Conversation.objects.get(user=request.user)
            messages = conversation.messages.all()
            data = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
                for msg in messages
            ]
            return Response(data)
        except Conversation.DoesNotExist:
            return Response([])
