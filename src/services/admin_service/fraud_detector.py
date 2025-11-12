"""
Automated fraud detection utilities
"""
import logging
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import FraudDetectionLog

logger = logging.getLogger(__name__)


def detect_suspicious_activity(user, activity_type, metadata=None):
    """
    Check for suspicious patterns and create fraud log if needed
    
    Args:
        user: User object
        activity_type: Type of activity (login, enrollment, payment, etc.)
        metadata: Additional context data
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        severity = 'low'
        fraud_type = 'unknown'
        description = ''
        
        # Pattern 1: Multiple failed login attempts
        if activity_type == 'failed_login':
            from src.services.auth_service.models import LoginAttempt
            
            last_hour = timezone.now() - timedelta(hours=1)
            failed_attempts = LoginAttempt.objects.filter(
                user=user,
                status='failed',
                attempted_at__gte=last_hour
            ).count()
            
            if failed_attempts >= 5:
                severity = 'high'
                fraud_type = 'brute_force'
                description = f"Multiple failed login attempts ({failed_attempts}) in last hour"
        
        # Pattern 2: Rapid course enrollments
        elif activity_type == 'enrollment':
            from src.services.courses_service.models import Enrollment
            
            last_hour = timezone.now() - timedelta(hours=1)
            enrollments = Enrollment.objects.filter(
                user=user,
                enrolled_at__gte=last_hour
            ).count()
            
            if enrollments >= 10:
                severity = 'medium'
                fraud_type = 'abnormal_activity'
                description = f"Unusual enrollment pattern: {enrollments} courses in 1 hour"
        
        # Pattern 3: Multiple payment methods
        elif activity_type == 'payment':
            from src.services.payment_service.models import StripePurchase
            
            last_day = timezone.now() - timedelta(days=1)
            unique_payment_methods = StripePurchase.objects.filter(
                user=user,
                created_at__gte=last_day
            ).values('payment_method_id').distinct().count()
            
            if unique_payment_methods >= 3:
                severity = 'high'
                fraud_type = 'payment_fraud'
                description = f"Multiple payment methods ({unique_payment_methods}) used in 24h"
        
        # Pattern 4: Wallet switching
        elif activity_type == 'wallet_change':
            from src.services.auth_service.models import WalletConnection
            
            last_week = timezone.now() - timedelta(days=7)
            wallet_changes = WalletConnection.objects.filter(
                user=user,
                connected_at__gte=last_week
            ).count()
            
            if wallet_changes >= 3:
                severity = 'medium'
                fraud_type = 'wallet_manipulation'
                description = f"Multiple wallet connections ({wallet_changes}) in 7 days"
        
        # Pattern 5: Token farming (rapid completions)
        elif activity_type == 'course_completion':
            from src.services.progress_service.models import CourseProgress
            
            last_day = timezone.now() - timedelta(days=1)
            completions = CourseProgress.objects.filter(
                user=user,
                completion_date__gte=last_day,
                progress_percentage=100
            ).count()
            
            if completions >= 5:
                severity = 'high'
                fraud_type = 'token_farming'
                description = f"Suspicious completion rate: {completions} courses in 24h"
        
        # Create fraud log if suspicious
        if severity in ['medium', 'high']:
            FraudDetectionLog.objects.create(
                user=user,
                fraud_type=fraud_type,
                severity=severity,
                description=description,
                ip_address=metadata.get('ip_address', '') if metadata else '',
                user_agent=metadata.get('user_agent', '') if metadata else '',
                evidence=metadata or {},
                status='pending'
            )
            
            logger.warning(f"Fraud detected: {fraud_type} for user {user.id} - {description}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error in fraud detection: {str(e)}", exc_info=True)
        return False


def check_user_risk_score(user):
    """
    Calculate risk score for a user (0-100)
    Higher = more risky
    """
    try:
        score = 0
        
        # Factor 1: Account age (newer = riskier)
        account_age_days = (timezone.now() - user.created_at).days
        if account_age_days < 7:
            score += 20
        elif account_age_days < 30:
            score += 10
        
        # Factor 2: Email verification
        if not user.is_verified:
            score += 15
        
        # Factor 3: Wallet connection
        if not user.wallet_address:
            score += 10
        
        # Factor 4: Previous fraud cases
        high_severity_cases = FraudDetectionLog.objects.filter(
            user=user,
            severity='high',
            status__in=['pending', 'under_review']
        ).count()
        score += (high_severity_cases * 20)
        
        # Factor 5: Banned history
        if user.is_banned:
            score += 50
        
        return min(score, 100)  # Cap at 100
        
    except Exception as e:
        logger.error(f"Error calculating risk score: {str(e)}")
        return 0
