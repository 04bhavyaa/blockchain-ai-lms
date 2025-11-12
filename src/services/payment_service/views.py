from django.shortcuts import render

# Create your views here.
"""
Payment Service Views - Stripe token top-ups only
On-chain payments handled by blockchain_service
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import uuid
import logging

from .models import TokenPackage, StripePurchase, Invoice, Refund, WebhookLog
from .serializers import (
    TokenPackageSerializer, StripePurchaseSerializer, CreatePurchaseSerializer,
    ConfirmPurchaseSerializer, InvoiceSerializer, RefundSerializer, RefundRequestSerializer
)
from .stripe_manager import StripeManager
from src.shared.exceptions import ValidationError, PaymentError, ResourceNotFoundError
from django.conf import settings

logger = logging.getLogger(__name__)


class TokenPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """Available token packages for purchase with USD"""
    
    queryset = TokenPackage.objects.filter(is_active=True)
    serializer_class = TokenPackageSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def best_value(self, request):
        """Get best value package (highest tokens per dollar)"""
        
        packages = self.get_queryset()
        if not packages:
            raise ResourceNotFoundError("No token packages available")
        
        best = max(packages, key=lambda p: p.tokens_per_dollar)
        serializer = self.get_serializer(best)
        
        return Response({'status': 'success', 'data': serializer.data})


class StripePurchaseViewSet(viewsets.ModelViewSet):
    """Stripe token top-up purchases (USD → tokens)"""
    
    serializer_class = StripePurchaseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return StripePurchase.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_payment_intent(self, request):
        """
        Step 1: Create Stripe PaymentIntent for token top-up
        
        Flow:
        1. User selects token package
        2. Backend creates PaymentIntent
        3. Frontend shows payment form
        4. User completes payment
        5. Call confirm_purchase endpoint
        """
        
        serializer = CreatePurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        package_id = serializer.validated_data['package_id']
        
        try:
            package = TokenPackage.objects.get(id=package_id, is_active=True)
        except TokenPackage.DoesNotExist:
            raise ResourceNotFoundError("Token package not found")
        
        try:
            # Generate idempotency key
            idempotency_key = str(uuid.uuid4())
            
            # Calculate effective price (with discount)
            effective_price = package.effective_price
            
            # Create purchase record
            purchase = StripePurchase.objects.create(
                user=request.user,
                token_package=package,
                tokens_purchased=package.tokens_amount,
                amount_usd=effective_price,
                idempotency_key=idempotency_key,
                status='pending',
                metadata={
                    'package_id': package_id,
                    'package_name': package.name,
                    'user_id': request.user.id,
                    'user_email': request.user.email,
                }
            )
            
            # Create Stripe PaymentIntent
            result = StripeManager.create_payment_intent(
                amount=float(effective_price),
                metadata={
                    'purchase_id': purchase.id,
                    'user_email': request.user.email,
                    'tokens': package.tokens_amount,
                },
                idempotency_key=idempotency_key
            )
            
            if not result['success']:
                purchase.status = 'failed'
                purchase.save()
                raise PaymentError(result['error'])
            
            purchase.stripe_payment_intent_id = result['payment_intent_id']
            purchase.status = 'processing'
            purchase.save()
            
            logger.info(f"PaymentIntent created: {purchase.id}")
            
            return Response({
                'status': 'success',
                'message': 'Stripe PaymentIntent created. Complete payment to proceed.',
                'data': {
                    'client_secret': result['client_secret'],
                    'payment_intent_id': result['payment_intent_id'],
                    'purchase_id': purchase.id,
                    'tokens': package.tokens_amount,
                    'amount_usd': str(effective_price),
                    'package_name': package.name,
                }
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error creating PaymentIntent: {str(e)}")
            raise PaymentError(str(e))
    
    @action(detail=False, methods=['post'])
    def confirm_purchase(self, request):
        """
        Step 2: Confirm purchase after Stripe payment succeeded
        
        Backend verifies PaymentIntent and adds tokens to user balance
        """
        
        serializer = ConfirmPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment_intent_id = serializer.validated_data['payment_intent_id']
        
        try:
            purchase = StripePurchase.objects.get(
                stripe_payment_intent_id=payment_intent_id,
                user=request.user
            )
        except StripePurchase.DoesNotExist:
            raise ResourceNotFoundError("Purchase not found")
        
        try:
            # Retrieve PaymentIntent from Stripe
            result = StripeManager.retrieve_payment_intent(payment_intent_id)
            
            if not result['success']:
                raise PaymentError(result['error'])
            
            if result['status'] != 'succeeded':
                purchase.status = 'failed'
                purchase.save()
                raise ValidationError(f"Payment not completed. Status: {result['status']}")
            
            # Update purchase
            purchase.status = 'succeeded'
            purchase.stripe_charge_id = result.get('charge_id')
            purchase.paid_at = timezone.now()
            purchase.save()
            
            # Add tokens to user balance (in-app, not on-chain)
            request.user.token_balance += purchase.tokens_purchased
            request.user.save()
            
            # Create invoice
            Invoice.objects.create(
                stripe_purchase=purchase,
                invoice_number=f"INV-{purchase.id}-{int(timezone.now().timestamp())}",
                billing_name=request.user.get_full_name() or request.user.username,
                billing_email=request.user.email,
                billing_address='',
                subtotal=purchase.amount_usd,
                tax_amount=0,
                total=purchase.amount_usd,
                paid_at=timezone.now(),
            )
            
            logger.info(
                f"Token top-up completed: {request.user.email} - "
                f"{purchase.tokens_purchased} tokens (${purchase.amount_usd})"
            )
            
            return Response({
                'status': 'success',
                'message': f'Successfully added {purchase.tokens_purchased} tokens to your balance!',
                'data': {
                    'tokens_purchased': purchase.tokens_purchased,
                    'new_balance': request.user.token_balance,
                    'amount_paid': str(purchase.amount_usd),
                    'purchase_id': purchase.id,
                }
            })
        
        except Exception as e:
            logger.error(f"Error confirming purchase: {str(e)}", exc_info=True)
            raise PaymentError(str(e))
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get token purchase history"""
        
        purchases = self.get_queryset().order_by('-created_at')
        page = self.paginate_queryset(purchases)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(purchases, many=True)
        return Response({'status': 'success', 'data': serializer.data})


class RefundViewSet(viewsets.ModelViewSet):
    """Refund management for token purchases"""
    
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Refund.objects.filter(stripe_purchase__user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def request_refund(self, request):
        """Request refund for token purchase"""
        
        serializer = RefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        purchase_id = serializer.validated_data['purchase_id']
        reason = serializer.validated_data['reason']
        
        try:
            purchase = StripePurchase.objects.get(
                id=purchase_id,
                user=request.user
            )
        except StripePurchase.DoesNotExist:
            raise ResourceNotFoundError("Purchase not found")
        
        if purchase.status != 'succeeded':
            raise ValidationError("Only succeeded purchases can be refunded")
        
        if not purchase.stripe_charge_id:
            raise ValidationError("Cannot refund this purchase")
        
        try:
            # Request refund from Stripe
            result = StripeManager.create_refund(
                charge_id=purchase.stripe_charge_id,
                reason=reason
            )
            
            if not result['success']:
                raise PaymentError(result['error'])
            
            # Create refund record
            refund = Refund.objects.create(
                stripe_purchase=purchase,
                stripe_refund_id=result['refund_id'],
                amount_usd=purchase.amount_usd,
                tokens_refunded=purchase.tokens_purchased,
                reason=reason,
                status=result['status']
            )
            
            # Update purchase status if refund succeeded
            if result['status'] == 'succeeded':
                purchase.status = 'refunded'
                purchase.save()
                
                # Deduct tokens from user
                request.user.token_balance -= purchase.tokens_purchased
                request.user.save()
            
            logger.info(f"Refund initiated: {refund.id}")
            
            return Response({
                'status': 'success',
                'message': 'Refund processed successfully',
                'data': RefundSerializer(refund).data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error requesting refund: {str(e)}")
            raise PaymentError(str(e))


class WebhookViewSet(viewsets.ViewSet):
    """Stripe webhook handler"""
    
    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['post'], permission_classes=[])
    def stripe_webhook(self, request):
        """
        Handle Stripe webhooks
        Webhooks are idempotent (checked by event_id)
        """
        
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            return Response(
                {'error': 'Missing signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify webhook signature
        result = StripeManager.verify_webhook_signature(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event = result['event']
        
        # Check for duplicate events (idempotency)
        try:
            WebhookLog.objects.get(event_id=event['id'])
            logger.info(f"Duplicate webhook ignored: {event['id']}")
            return Response({'status': 'ok'})
        except WebhookLog.DoesNotExist:
            pass
        
        # Create webhook log
        webhook_log = WebhookLog.objects.create(
            event_id=event['id'],
            event_type=event['type'],
            payload=event
        )
        
        try:
            # Handle different event types
            if event['type'] == 'payment_intent.succeeded':
                self._handle_payment_succeeded(event['data']['object'])
            
            elif event['type'] == 'payment_intent.payment_failed':
                self._handle_payment_failed(event['data']['object'])
            
            elif event['type'] == 'charge.refunded':
                self._handle_charge_refunded(event['data']['object'])
            
            webhook_log.processed = True
            webhook_log.save()
            
            logger.info(f"Webhook processed: {event['type']}")
        
        except Exception as e:
            webhook_log.error_message = str(e)
            webhook_log.save()
            logger.error(f"Error processing webhook: {str(e)}")
        
        return Response({'status': 'ok'})
    
    def _handle_payment_succeeded(self, payment_intent):
        """Handle payment_intent.succeeded event"""
        try:
            purchase = StripePurchase.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            purchase.status = 'succeeded'
            purchase.paid_at = timezone.now()
            purchase.save()
            
            # Add tokens to user (async would be better)
            purchase.user.token_balance += purchase.tokens_purchased
            purchase.user.save()
            
            logger.info(f"Tokens added to {purchase.user.email}")
        
        except StripePurchase.DoesNotExist:
            logger.warning(f"Purchase not found: {payment_intent['id']}")
    
    def _handle_payment_failed(self, payment_intent):
        """Handle payment_intent.payment_failed event"""
        try:
            purchase = StripePurchase.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            purchase.status = 'failed'
            purchase.save()
            
            logger.info(f"Payment failed for {purchase.user.email}")
        
        except StripePurchase.DoesNotExist:
            logger.warning(f"Purchase not found: {payment_intent['id']}")
    
    def _handle_charge_refunded(self, charge):
        """Handle charge.refunded event"""
        try:
            purchase = StripePurchase.objects.get(
                stripe_charge_id=charge['id']
            )
            purchase.status = 'refunded'
            purchase.save()
            
            # Remove tokens from user
            purchase.user.token_balance -= purchase.tokens_purchased
            purchase.user.save()
            
            logger.info(f"Tokens refunded for {purchase.user.email}")
        
        except StripePurchase.DoesNotExist:
            logger.warning(f"Purchase not found: {charge['id']}")
