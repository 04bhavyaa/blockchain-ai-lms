"""
Payment service serializers
"""

from rest_framework import serializers
from .models import TokenPackage, StripePurchase, Invoice, Refund


class TokenPackageSerializer(serializers.ModelSerializer):
    """Token package serializer"""
    
    effective_price = serializers.ReadOnlyField()
    tokens_per_dollar = serializers.ReadOnlyField()
    best_value = serializers.SerializerMethodField()
    
    class Meta:
        model = TokenPackage
        fields = [
            'id', 'name', 'tokens_amount', 'price_usd', 'discount_percentage',
            'effective_price', 'tokens_per_dollar', 'best_value', 'description'
        ]
    
    def get_best_value(self, obj):
        """Check if this is the best value package"""
        all_packages = TokenPackage.objects.filter(is_active=True)
        if all_packages:
            best = max(all_packages, key=lambda p: p.tokens_per_dollar)
            return obj.id == best.id
        return False


class StripePurchaseSerializer(serializers.ModelSerializer):
    """Stripe purchase serializer"""
    
    package_name = serializers.CharField(source='token_package.name', read_only=True)
    
    class Meta:
        model = StripePurchase
        fields = [
            'id', 'token_package', 'package_name', 'tokens_purchased',
            'amount_usd', 'status', 'created_at', 'paid_at'
        ]
        read_only_fields = [
            'id', 'tokens_purchased', 'amount_usd', 'status', 'created_at', 'paid_at'
        ]


class CreatePurchaseSerializer(serializers.Serializer):
    """Create token purchase request"""
    
    package_id = serializers.IntegerField()


class ConfirmPurchaseSerializer(serializers.Serializer):
    """Confirm purchase after Stripe payment"""
    
    payment_intent_id = serializers.CharField()


class InvoiceSerializer(serializers.ModelSerializer):
    """Invoice serializer"""
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'billing_name', 'subtotal',
            'tax_amount', 'total', 'issued_at', 'paid_at'
        ]
        read_only_fields = fields


class RefundRequestSerializer(serializers.Serializer):
    """Request refund"""
    
    purchase_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=500)


class RefundSerializer(serializers.ModelSerializer):
    """Refund serializer"""
    
    class Meta:
        model = Refund
        fields = [
            'id', 'amount_usd', 'tokens_refunded', 'reason',
            'status', 'requested_at', 'completed_at'
        ]
