from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import (
    Conversation, ChatMessage, FAQ
)
import uuid

User = get_user_model()

class ChatbotServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="chat@lms.com", username="chatter", password="pw123456", token_balance=10)
        self.client.force_authenticate(user=self.user)
        self.faq = FAQ.objects.create(
            category="General",
            question="How do I reset my password?",
            answer="Visit your profile and click 'Reset Password'.",
            is_active=True,
        )
        # self.kb = KnowledgeBase.objects.create(
        #     title="Intro to Blockchain",
        #     content="Blockchain is a decentralized ledger...",
        #     source="Course Material",
        #     doc_type="course",
        #     is_active=True,
        # )
        self.session_id = str(uuid.uuid4())
        self.convo = Conversation.objects.create(
            user=self.user, session_id=self.session_id, title="Test Chat", description="Test Desc"
        )
        # ConversationContext.objects.create(conversation=self.convo)

    def test_conversation_create_and_archive(self):
        url = reverse("conversations-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("data" in resp.data)
        # Archive endpoint (just for API existence)
        url2 = reverse("conversations-archive", args=[self.convo.id])
        resp2 = self.client.post(url2)
        self.assertEqual(resp2.status_code, 200)

    def test_send_message_token_and_faq(self):
        url = reverse("send-message")
        resp = self.client.post(url, {
            "message": "How do I reset my password?",
            "conversation_id": self.convo.id,
            "session_id": self.session_id,
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        result = resp.data["data"]
        self.assertIn("user_message", result)
        self.assertIn("assistant_message", result)
        self.assertIn("session_id", result)
        self.assertEqual(result["tokens_used"], 0) # FAQ is free

    def test_send_message_rag_costs_tokens(self):
        url = reverse("send-message")
        resp = self.client.post(url, {
            "message": "Tell me about blockchain.",
            "conversation_id": self.convo.id,
            "session_id": self.session_id,
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        result = resp.data["data"]
        self.assertEqual(result["tokens_used"], 2)
        self.user.refresh_from_db()
        self.assertEqual(self.user.token_balance, 8)

    def test_feedback_endpoint(self):
        msg = ChatMessage.objects.create(
            conversation=self.convo,
            user=self.user,
            role='assistant',
            content="This is a test answer.",
            tokens_used=0
        )
        url = reverse("feedback-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        url2 = reverse("feedback-list")
        resp2 = self.client.post(url2, {
            "message_id": msg.id,
            "rating": 5,
            "comment": "Great!"
        }, format="json")
        self.assertEqual(resp2.status_code, 201)
        self.assertIn("Feedback submitted successfully", resp2.data["message"])

    def test_faq_search(self):
        url = reverse("faqs-search")
        resp = self.client.get(url, {"q": "password"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["data"])

    def test_kb_search(self):
        url = reverse("knowledge-base-search")
        resp = self.client.get(url, {"q": "blockchain"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["data"])
