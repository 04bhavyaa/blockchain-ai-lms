"""
Shared utility functions
"""

import logging
import random
import string
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_email(to_email, subject, message, html_message=None):
    """Send email with error handling"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return False


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_random_token(length=32):
    """Generate random token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def calculate_completion_percentage(completed, total):
    """Calculate percentage completion"""
    if total == 0:
        return 0
    return round((completed / total) * 100, 2)


def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"
