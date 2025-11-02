from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import OnChainPayment, Certificate, ApprovalRequest, SmartContractConfig
from django.urls import reverse

User = get_user_model()

class BlockchainServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="blocktest@example.com",
            username="blockuser",
            password="securetestpass"
        )

    def authenticate(self):
        # Simulate or actually log in, or force authentication as needed.
        self.client.force_authenticate(user=self.user)

    def test_certificate_issue_and_retrieve(self):
        self.authenticate()
        data = {
            "course_id": 1,
            "course_name": "Intro Blockchain",
            "completion_date": "2025-10-10",
            "metadata": {
                "issuer": "LMS",
                "score": 95
            }
        }
        response = self.client.post(
            reverse("certificates-issue-certificate"),
            data, format="json"
        )
        self.assertEqual(response.status_code, 201)
        cert_id = response.data["data"]["id"]
        # Now retrieve "my_certificates"
        response = self.client.get(reverse("certificates-my-certificates"))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_request_approval_and_confirm_payment_error(self):
        self.authenticate()
        # Should fail because Course with id=999 doesn't exist
        data = {"course_id": 999}
        response = self.client.post(reverse("request-approval"), data, format="json")
        self.assertIn(response.status_code, [400, 404])

    def test_smart_contract_config_model(self):
        # Simple model test for contract config
        SmartContractConfig.objects.create(
            contract_type="token",
            contract_address="0x" + "b"*40,
            contract_abi=[],
            deployment_hash="0x" + "a"*10,
            block_number=123,
            network="sepolia"
        )
        obj = SmartContractConfig.objects.get(contract_type="token")
        self.assertTrue(obj.is_active)

    def test_on_chain_payment_model(self):
        payment = OnChainPayment.objects.create(
            user=self.user,
            course_id=1,
            course_name="Test",
            tokens_amount=10,
            user_wallet_address="0x" + "b"*40,
            platform_treasury_address="0x" + "a"*40,
            transaction_hash="0x" + "c"*64,
            status="confirmed"
        )
        self.assertEqual(payment.status, "confirmed")

    def test_approval_request_model(self):
        approval = ApprovalRequest.objects.create(
            user=self.user,
            course_id=1,
            tokens_to_approve=5,
            status="pending",
            spender_address="0x" + "f"*40,
            metadata={"purpose": "testing"},
            expires_at="2030-01-01T00:00"
        )
        self.assertEqual(approval.status, "pending")
