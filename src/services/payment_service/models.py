"""
Payment Service Models - Stripe for token top-ups only
On-chain payments are handled by blockchain_service
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()


class TokenPackage(models.Model):
    """Pre-defined token purchase packages (USD → tokens)"""
    
    name = models.CharField(max_length=100)  # "Starter", "Professional", etc.
    tokens_amount = models.IntegerField(validators=[MinValueValidator(1)])
    price_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    discount_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    stripe_price_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'token_packages'
        ordering = ['price_usd']
    
    def __str__(self):
        return f"{self.name} - {self.tokens_amount} tokens (${self.price_usd})"
    
    @property
    def effective_price(self):
        """Calculate price after discount"""
        discount = (self.price_usd * self.discount_percentage) / 100
        return self.price_usd - discount
    
    @property
    def tokens_per_dollar(self):
        """Calculate tokens per dollar value"""
        if self.price_usd > 0:
            return round(self.tokens_amount / float(self.price_usd), 2)
        return 0


class StripePurchase(models.Model):
    """Stripe payment for token top-ups (USD → tokens)"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stripe_purchases')
    token_package = models.ForeignKey(TokenPackage, on_delete=models.SET_NULL, null=True)
    
    # What user gets
    tokens_purchased = models.IntegerField(validators=[MinValueValidator(1)])
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Stripe IDs
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    stripe_charge_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    
    # Idempotency key to prevent duplicate charges
    idempotency_key = models.CharField(max_length=255, unique=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'stripe_purchases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['stripe_payment_intent_id']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.tokens_purchased} tokens (${self.amount_usd})"


class Invoice(models.Model):
    """Invoices for Stripe token purchases"""
    
    stripe_purchase = models.OneToOneField(
        StripePurchase,
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    invoice_number = models.CharField(max_length=100, unique=True)
    stripe_invoice_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    
    # Billing details
    billing_name = models.CharField(max_length=255)
    billing_email = models.EmailField()
    billing_address = models.TextField()
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    issued_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"


class Refund(models.Model):
    """Refund records for Stripe purchases"""
    
    REFUND_STATUS = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
    ]
    
    stripe_purchase = models.OneToOneField(
        StripePurchase,
        on_delete=models.CASCADE,
        related_name='refund'
    )
    stripe_refund_id = models.CharField(max_length=255, unique=True)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    tokens_refunded = models.IntegerField()
    reason = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=REFUND_STATUS, default='pending')
    
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'refunds'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Refund - {self.tokens_refunded} tokens"


class WebhookLog(models.Model):
    """Log of Stripe webhooks for debugging and idempotency"""
    
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    
    processed = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stripe_webhook_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_id']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.event_id}"
