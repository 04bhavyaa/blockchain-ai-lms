"""
Stripe Manager - Centralized Stripe integration for token top-ups
"""

import stripe
import logging
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeManager:
    """Stripe operations for token top-ups"""
    
    @staticmethod
    def create_payment_intent(amount, currency='usd', metadata=None, idempotency_key=None):
        """Create PaymentIntent for token top-up purchase"""
        try:
            # Convert to cents
            amount_cents = int(float(amount) * 100)
            
            params = {
                'amount': amount_cents,
                'currency': currency,
                'metadata': metadata or {},
            }
            
            # Add idempotency key to prevent duplicate charges
            headers = {}
            if idempotency_key:
                headers['Idempotency-Key'] = idempotency_key
            
            intent = stripe.PaymentIntent.create(**params)
            
            logger.info(f"PaymentIntent created: {intent.id}")
            
            return {
                'success': True,
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'amount': amount,
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating PaymentIntent: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def retrieve_payment_intent(payment_intent_id):
        """Retrieve PaymentIntent details"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'success': True,
                'status': intent.status,
                'amount': Decimal(intent.amount) / 100,
                'charge_id': intent.charges.data[0].id if intent.charges.data else None,
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_refund(charge_id, amount=None, reason=None):
        """Create refund"""
        try:
            params = {'charge': charge_id}
            
            if amount:
                params['amount'] = int(float(amount) * 100)
            if reason:
                params['reason'] = reason
            
            refund = stripe.Refund.create(**params)
            
            logger.info(f"Refund created: {refund.id}")
            
            return {
                'success': True,
                'refund_id': refund.id,
                'status': refund.status,
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def verify_webhook_signature(payload, sig_header, webhook_secret):
        """Verify Stripe webhook signature"""
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            return {'success': True, 'event': event}
        
        except ValueError:
            logger.error("Invalid webhook payload")
            return {'success': False, 'error': 'Invalid payload'}
        
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return {'success': False, 'error': 'Invalid signature'}
