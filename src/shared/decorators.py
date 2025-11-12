"""
Shared decorators for the platform
"""
from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def require_admin(view_func):
    """
    Decorator to require admin permissions
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'status': 'error', 'message': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'status': 'error', 'message': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def log_action(action_type):
    """
    Decorator to automatically log admin actions
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Execute the view
            response = view_func(self, request, *args, **kwargs)
            
            # Log successful actions (2xx status codes)
            if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                try:
                    from src.services.admin_service.models import AdminDashboardLog
                    
                    # Get target info from kwargs if available
                    target_id = kwargs.get('pk', 0)
                    target_type = getattr(self, 'queryset', None)
                    if target_type:
                        target_type = target_type.model.__name__.lower()
                    else:
                        target_type = 'unknown'
                    
                    # Get IP address
                    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                    if x_forwarded_for:
                        ip_address = x_forwarded_for.split(',')[0]
                    else:
                        ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
                    
                    AdminDashboardLog.objects.create(
                        admin_user=request.user if request.user.is_authenticated else None,
                        action_type=action_type,
                        target_type=target_type,
                        target_id=target_id,
                        description=f"{action_type} on {target_type} {target_id}",
                        ip_address=ip_address,
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        metadata={
                            'method': request.method,
                            'path': request.path
                        }
                    )
                except Exception as e:
                    # Don't fail the request if logging fails
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to log admin action: {str(e)}")
            
            return response
        
        return wrapper
    return decorator

def require_authenticated(view_func):
    """
    Decorator to require authenticated user
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'status': 'error', 'message': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper