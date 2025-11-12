"""
Fraud detection signals
"""
from django.dispatch import receiver
from django.db.models.signals import post_save
from src.services.auth_service.models import LoginAttempt, WalletConnection
from src.services.courses_service.models import Enrollment
from src.services.progress_service.models import CourseProgress
from src.services.payment_service.models import StripePurchase
from .fraud_detector import detect_suspicious_activity


@receiver(post_save, sender=LoginAttempt)
def check_failed_login_fraud(sender, instance, created, **kwargs):
    """Detect fraud after login attempt"""
    if created and instance.status == 'failed':
        detect_suspicious_activity(
            user=instance.user,
            activity_type='failed_login',
            metadata={
                'ip_address': instance.ip_address,
                'user_agent': instance.user_agent or ''
            }
        )


@receiver(post_save, sender=Enrollment)
def check_enrollment_fraud(sender, instance, created, **kwargs):
    """Detect fraud after course enrollment"""
    if created:
        detect_suspicious_activity(
            user=instance.user,
            activity_type='enrollment',
            metadata={
                'course_id': instance.course.id,
                'course_title': instance.course.title
            }
        )


@receiver(post_save, sender=StripePurchase)
def check_payment_fraud(sender, instance, created, **kwargs):
    """Detect fraud after payment"""
    if created:
        detect_suspicious_activity(
            user=instance.user,
            activity_type='payment',
            metadata={
                'amount': str(instance.amount_usd),
                'payment_method_id': instance.payment_method_id
            }
        )


@receiver(post_save, sender=WalletConnection)
def check_wallet_fraud(sender, instance, created, **kwargs):
    """Detect fraud after wallet connection"""
    if created:
        detect_suspicious_activity(
            user=instance.user,
            activity_type='wallet_change',
            metadata={
                'wallet_address': instance.wallet_address,
                'network': instance.network
            }
        )


@receiver(post_save, sender=CourseProgress)
def check_completion_fraud(sender, instance, created, **kwargs):
    """Detect fraud after course completion"""
    if not created and instance.progress_percentage == 100 and instance.completion_date:
        # Only check when progress changes to 100%
        detect_suspicious_activity(
            user=instance.user,
            activity_type='course_completion',
            metadata={
                'course_id': instance.course.id,
                'completion_date': instance.completion_date.isoformat()
            }
        )
