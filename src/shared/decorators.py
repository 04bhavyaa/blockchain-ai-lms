"""
Custom decorators for views and functions
"""

import functools
import logging
from .exceptions import PermissionDeniedError

logger = logging.getLogger(__name__)


def require_admin(func):
    """Decorator to require admin/staff privileges"""
    @functools.wraps(func)
    def wrapper(self, request, *args, **kwargs):
        if not (request.user and request.user.is_staff):
            raise PermissionDeniedError(message="Admin privileges required")
        return func(self, request, *args, **kwargs)
    return wrapper


def require_authenticated(func):
    """Decorator to require authenticated user"""
    @functools.wraps(func)
    def wrapper(self, request, *args, **kwargs):
        if not (request.user and request.user.is_authenticated):
            raise PermissionDeniedError(message="Authentication required")
        return func(self, request, *args, **kwargs)
    return wrapper


def log_action(action_type):
    """Log user actions for audit trail"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            user = request.user if hasattr(request, 'user') else None
            logger.info(
                f"Action: {action_type}",
                extra={
                    'user_id': user.id if user else None,
                    'path': request.path if hasattr(request, 'path') else None,
                }
            )
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator
