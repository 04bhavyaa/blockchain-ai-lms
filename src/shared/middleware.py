"""
Custom middleware for request/response handling and error management
"""

import logging
import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .exceptions import ApplicationError

logger = logging.getLogger(__name__)


class ExceptionMiddleware(MiddlewareMixin):
    """
    Centralized exception handling for API requests
    Converts exceptions to consistent JSON responses
    """
    
    def process_exception(self, request, exception):
        """Handle exceptions and return appropriate JSON response"""
        
        # Skip if not API request
        if not request.path.startswith('/api/'):
            return None
        
        # Log exception
        logger.error(
            f"Exception: {type(exception).__name__}",
            exc_info=True,
            extra={'request_path': request.path}
        )
        
        # Handle custom application exceptions
        if isinstance(exception, ApplicationError):
            return JsonResponse(
                {
                    'status': 'error',
                    'message': exception.message,
                    'details': exception.details,
                    **({"errors": exception.errors} if hasattr(exception, 'errors') else {})
                },
                status=exception.status_code
            )
        
        # Handle validation errors from DRF
        if hasattr(exception, 'detail'):
            return JsonResponse(
                {
                    'status': 'error',
                    'message': str(exception.detail),
                    'details': {}
                },
                status=400
            )
        
        # Handle unexpected exceptions
        return JsonResponse(
            {
                'status': 'error',
                'message': 'Internal server error',
                'details': {}
            },
            status=500
        )


class RequestLoggingMiddleware(MiddlewareMixin):
    """Log all API requests with method, path, and status code"""
    
    def process_request(self, request):
        request.request_start_time = __import__('time').time()
        return None
    
    def process_response(self, request, response):
        if request.path.startswith('/api/'):
            duration = __import__('time').time() - getattr(request, 'request_start_time', 0)
            logger.info(
                f"{request.method} {request.path} {response.status_code} ({duration:.2f}s)"
            )
        return response


class CORSMiddleware(MiddlewareMixin):
    """Handle CORS headers for API requests"""
    
    def process_response(self, request, response):
        if request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
