"""
Custom decorators for views and functions
"""

import functools
import logging
from django.core.cache import cache
from .exceptions import PermissionDeniedError, RateLimitError
from .constants import RATE_LIMITS

logger = logging.getLogger(__name__)


def cache_result(timeout=300):
    """
    Cache function result based on arguments
    
    Args:
        timeout: Cache timeout in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__module__}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache set: {cache_key}")
            return result
        
        return wrapper
    return decorator


def rate_limit(key_prefix, limit=10, period=3600):
    """
    Rate limit a function based on key and period
    
    Args:
        key_prefix: Prefix for rate limit key
        limit: Number of calls allowed
        period: Time period in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get user ID or IP from request
            request = args[0] if args else None
            if hasattr(request, 'user') and request.user.is_authenticated:
                identifier = f"{key_prefix}:user:{request.user.id}"
            elif hasattr(request, 'META'):
                identifier = f"{key_prefix}:ip:{request.META.get('REMOTE_ADDR')}"
            else:
                identifier = f"{key_prefix}:unknown"
            
            # Check rate limit
            current_count = cache.get(identifier, 0)
            if current_count >= limit:
                raise RateLimitError(
                    message=f"Rate limit exceeded. Max {limit} requests per {period} seconds"
                )
            
            # Increment counter
            cache.set(identifier, current_count + 1, period)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


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


def validate_input(**validators):
    """
    Validate input parameters
    
    Args:
        **validators: Field name -> validator function pairs
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for field, validator in validators.items():
                if field in kwargs:
                    try:
                        validator(kwargs[field])
                    except Exception as e:
                        logger.error(f"Validation failed for {field}: {str(e)}")
                        raise
            return func(*args, **kwargs)
        return wrapper
    return decorator
