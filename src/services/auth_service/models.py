"""
Authentication service models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import secrets

User = get_user_model()

class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'email_verification_tokens'

    def __str__(self):
        return f"Verification Token for {self.user.email}"

    def is_expired(self):
        expired = timezone.now() > self.expires_at
        if expired and not self.is_used:
            self.is_used = True
            self.used_at = timezone.now()
            self.save()
        return expired

    @classmethod
    def create_token(cls, user, expiration_hours=24):
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=expiration_hours)
        return cls.objects.create(user=user, token=token, expires_at=expires_at)

class PasswordResetToken(models.Model):
    """Password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"Password Reset Token for {self.user.email}"

    def is_expired(self):
        expired = timezone.now() > self.expires_at
        if expired and not self.is_used:
            self.is_used = True
            self.used_at = timezone.now()
            self.save()
        return expired

    @classmethod
    def create_token(cls, user, expiration_hours=1):
        """Create new password reset token"""
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=expiration_hours)
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )

class WalletConnection(models.Model):
    """Track wallet connections for blockchain integration"""
    NETWORK_CHOICES = [
        ('ethereum', 'Ethereum'),
        ('sepolia', 'Sepolia Testnet'),
        ('polygon', 'Polygon'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet_connection')
    wallet_address = models.CharField(max_length=42, unique=True)
    network = models.CharField(max_length=50, choices=NETWORK_CHOICES, default='sepolia')
    is_verified = models.BooleanField(default=False)
    verification_signature = models.TextField(null=True, blank=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'wallet_connections'

    def __str__(self):
        return f"Wallet {self.wallet_address[:10]}... for {self.user.email}"

class LoginAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_attempts', null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    status = models.CharField(max_length=32, default='failed')  # Use "success" or "failed"
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'login_attempts'
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['user', '-attempted_at']),
            models.Index(fields=['ip_address', '-attempted_at']),
        ]

    def __str__(self):
        status_label = "Success" if self.status == "success" else "Failed"
        return f"{self.email} - {status_label} ({self.attempted_at})"

class AuthSession(models.Model):
    """Track active user sessions (optional: for session audits)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth_sessions')
    token = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_info = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'auth_sessions'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', '-last_activity']),
            models.Index(fields=['token']),
        ]

    def __str__(self):
        return f"Session for {self.user.email}"
