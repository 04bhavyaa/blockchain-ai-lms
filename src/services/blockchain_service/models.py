from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()

class SmartContractConfig(models.Model):
    CONTRACT_TYPES = [
        ('token', 'ERC20 Token'),
        ('certificate', 'ERC721 Certificate NFT'),
    ]
    contract_type = models.CharField(max_length=50, choices=CONTRACT_TYPES, unique=True)
    contract_address = models.CharField(max_length=42, unique=True)
    contract_abi = models.JSONField(help_text="Contract ABI")
    deployment_hash = models.CharField(max_length=255)
    block_number = models.BigIntegerField()
    network = models.CharField(max_length=50, default='sepolia')
    is_active = models.BooleanField(default=True)
    deployed_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'smart_contract_configs'
    def __str__(self):
        return f"{self.get_contract_type_display()} - {self.contract_address[:10]}..."

class OnChainPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='on_chain_payments')
    course_id = models.IntegerField()
    course_name = models.CharField(max_length=255)
    tokens_amount = models.IntegerField(validators=[MinValueValidator(1)])
    user_wallet_address = models.CharField(max_length=42)
    platform_treasury_address = models.CharField(max_length=42)
    transaction_hash = models.CharField(max_length=255, unique=True, null=True, blank=True)
    block_number = models.BigIntegerField(null=True, blank=True)
    gas_used = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    gas_price = models.DecimalField(max_digits=18, decimal_places=0, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confirmation_count = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = 'on_chain_payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_hash']),
            models.Index(fields=['status']),
        ]
    def __str__(self):
        return f"{self.user.email} - {self.tokens_amount} tokens - {self.course_name}"

class Certificate(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Mint'),
        ('minting', 'Minting in Progress'),
        ('minted', 'Minted'),
        ('failed', 'Minting Failed'),
        ('verified', 'ZKP Verified'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course_id = models.IntegerField()
    course_name = models.CharField(max_length=255)
    completion_date = models.DateField()
    certificate_hash = models.CharField(max_length=255, unique=True)
    nft_token_id = models.BigIntegerField(null=True, blank=True, unique=True)
    nft_contract_address = models.CharField(max_length=42, null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    transaction_hash = models.CharField(max_length=255, unique=True, null=True, blank=True)
    zk_proof_hash = models.TextField(null=True, blank=True)
    ipfs_metadata_hash = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(default=dict)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_certificates'
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    minted_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = 'certificates'
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['user', '-issued_at']),
            models.Index(fields=['status']),
            models.Index(fields=['nft_token_id']),
        ]
    def __str__(self):
        return f"{self.course_name} - {self.user.email}"

class ApprovalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Signature'),
        ('signed', 'Signed - Awaiting Transaction'),
        ('approved', 'Approved on Blockchain'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_requests')
    course_id = models.IntegerField()
    tokens_to_approve = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_hash = models.CharField(max_length=255, unique=True, null=True, blank=True)
    spender_address = models.CharField(max_length=42)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    approved_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = 'approval_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
    def __str__(self):
        return f"{self.user.email} - {self.tokens_to_approve} tokens - {self.status}"

class WebhookLog(models.Model):
    EVENT_TYPES = [
        ('payment_confirmed', 'Payment Confirmed'),
        ('payment_failed', 'Payment Failed'),
        ('certificate_minted', 'Certificate Minted'),
        ('certificate_burned', 'Certificate Burned'),
    ]
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    transaction_hash = models.CharField(max_length=255, unique=True)
    block_number = models.BigIntegerField()
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'blockchain_webhook_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_hash']),
            models.Index(fields=['event_type']),
        ]
    def __str__(self):
        return f"{self.event_type} - {self.transaction_hash[:10]}..."