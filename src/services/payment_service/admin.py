"""
Django admin for payment service
"""

from django.contrib import admin
from .models import TokenPackage, StripePurchase, Invoice, Refund, WebhookLog


@admin.register(TokenPackage)
class TokenPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'tokens_amount', 'price_usd', 'discount_percentage', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']


@admin.register(StripePurchase)
class StripePurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'token_package', 'tokens_purchased', 'amount_usd', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'stripe_payment_intent_id']
    readonly_fields = ['stripe_payment_intent_id', 'stripe_charge_id', 'idempotency_key']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'billing_name', 'total', 'issued_at']
    list_filter = ['issued_at']
    search_fields = ['invoice_number', 'billing_email']
    readonly_fields = ['issued_at']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['stripe_purchase', 'amount_usd', 'status', 'requested_at']
    list_filter = ['status', 'requested_at']
    readonly_fields = ['requested_at']


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'event_id', 'processed', 'created_at']
    list_filter = ['event_type', 'processed']
    search_fields = ['event_id']
    readonly_fields = ['created_at', 'payload']
