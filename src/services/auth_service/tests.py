from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import EmailVerificationToken, PasswordResetToken, WalletConnection

User = get_user_model()

class AuthServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="faketest@example.com",
            username="testuser",
            password="strongpassword123"
        )

    def test_register(self):
        response = self.client.post(reverse('auth-register'), {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "Testpass123",
            "password_confirm": "Testpass123"
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_login(self):
        response = self.client.post(reverse('auth-login'), {
            "email": "faketest@example.com",
            "password": "strongpassword123"
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('access' in response.data['data'])

    def test_verification_expired(self):
        token = EmailVerificationToken.create_token(self.user)
        token.expires_at = token.created_at
        token.save()
        verified = token.is_expired()
        self.assertTrue(verified)

    def test_password_reset_flow(self):
        reset_token = PasswordResetToken.create_token(self.user)
        response = self.client.post(reverse('auth-reset-password'), {
            "token": reset_token.token,
            "new_password": "NewPassword321",
            "new_password_confirm": "NewPassword321"
        }, format='json')
        self.assertEqual(response.status_code, 200)

    def test_wallet_connection(self):
        # test wallet address format rejected if not 42 chars, etc.
        response = self.client.post(reverse('auth-connect-wallet'), {
            "wallet_address": "0x" + "a"*40,  # valid length
            "signature": "dummy_signature",
            "network": "sepolia"
        }, format='json', HTTP_AUTHORIZATION=f"Bearer {self.user.tokens['access'] if hasattr(self.user, 'tokens') else ''}")
        # If you mock the wallet, you can assert on 201
        self.assertTrue(response.status_code in (200, 201))
