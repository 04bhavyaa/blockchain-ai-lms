"""
Django admin configuration for blockchain service
"""

from django.contrib import admin
from .models import SmartContractConfig, OnChainPayment, Certificate, ApprovalRequest, WebhookLog


@admin.register(SmartContractConfig)
class SmartContractConfigAdmin(admin.ModelAdmin):
    list_display = ['contract_type', 'contract_address', 'network', 'is_active']
    list_filter = ['contract_type', 'network', 'is_active']
    readonly_fields = ['deployment_hash', 'deployed_at']


@admin.register(OnChainPayment)
class OnChainPaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_name', 'tokens_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'transaction_hash', 'course_name']
    readonly_fields = ['transaction_hash', 'confirmed_at']


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_name', 'status', 'issued_at']
    list_filter = ['status', 'issued_at']
    search_fields = ['user__email', 'course_name']
    readonly_fields = ['issued_at', 'minted_at']


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'tokens_to_approve', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email']


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'transaction_hash', 'processed', 'created_at']
    list_filter = ['event_type', 'processed']
    readonly_fields = ['created_at']
