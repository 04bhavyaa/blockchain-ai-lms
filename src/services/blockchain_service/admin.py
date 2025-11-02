from django.contrib import admin
from .models import SmartContractConfig, OnChainPayment, Certificate, ApprovalRequest, WebhookLog

@admin.register(SmartContractConfig)
class SmartContractConfigAdmin(admin.ModelAdmin):
    list_display = ['contract_type', 'contract_address', 'network', 'is_active', 'deployment_hash', 'deployed_at']
    list_filter = ['contract_type', 'network', 'is_active']
    readonly_fields = ['deployment_hash', 'deployed_at', 'block_number', 'contract_abi', 'contract_address']

@admin.register(OnChainPayment)
class OnChainPaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_name', 'tokens_amount', 'status', 'confirmation_count', 'created_at', 'transaction_hash']
    list_filter = ['status', 'created_at', 'confirmation_count']
    search_fields = ['user__email', 'transaction_hash', 'course_name', 'user_wallet_address']
    readonly_fields = ['transaction_hash', 'confirmed_at', 'block_number', 'metadata']

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_name', 'status', 'issued_at', 'minted_at', 'nft_token_id']
    list_filter = ['status', 'issued_at', 'minted_at']
    search_fields = ['user__email', 'course_name', 'nft_token_id', 'certificate_hash']
    readonly_fields = ['issued_at', 'minted_at', 'nft_token_id', 'transaction_hash', 'certificate_hash', 'zk_proof_hash', 'ipfs_metadata_hash']

@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'tokens_to_approve', 'status', 'course_id', 'created_at', 'transaction_hash']
    list_filter = ['status', 'created_at', 'expires_at']
    search_fields = ['user__email', 'transaction_hash', 'spender_address']
    readonly_fields = ['transaction_hash', 'approved_at', 'expires_at', 'created_at']

@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'transaction_hash', 'processed', 'block_number', 'created_at']
    list_filter = ['event_type', 'processed', 'block_number']
    search_fields = ['transaction_hash']
    readonly_fields = ['created_at', 'event_type', 'transaction_hash', 'payload', 'error_message']