"""
Logging middleware for request/response tracking
"""
import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger('api_requests')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests and responses
    """
    
    def process_request(self, request):
        """
        Log incoming request details
        """
        # Store request start time
        request._start_time = time.time()
        
        # Skip logging for certain paths
        if self._should_skip_logging(request.path):
            return None
        
        # Get request details
        user = getattr(request, 'user', None)
        user_email = getattr(user, 'email', 'anonymous') if user and hasattr(user, 'email') else 'anonymous'
        
        # Log request
        log_data = {
            'method': request.method,
            'path': request.path,
            'user': user_email,
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
        }
        
        # Log query parameters
        if request.GET:
            log_data['query_params'] = dict(request.GET)
        
        # Log request body for POST/PUT/PATCH (excluding sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
            try:
                body = json.loads(request.body.decode('utf-8'))
                # Remove sensitive fields
                safe_body = self._sanitize_data(body)
                log_data['body'] = safe_body
            except (json.JSONDecodeError, UnicodeDecodeError):
                log_data['body'] = '[Unable to parse body]'
        
        logger.info(f"Request: {json.dumps(log_data)}")
        
        return None
    
    def process_response(self, request, response):
        """
        Log response details
        """
        # Skip logging for certain paths
        if self._should_skip_logging(request.path):
            return response
        
        # Calculate request duration
        duration = None
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
        
        # Get user info
        user = getattr(request, 'user', None)
        user_email = getattr(user, 'email', 'anonymous') if user and hasattr(user, 'email') else 'anonymous'
        
        # Log response
        log_data = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'user': user_email,
            'duration_ms': round(duration * 1000, 2) if duration else None,
        }
        
        # Log response body for errors (sanitized)
        if response.status_code >= 400:
            try:
                if hasattr(response, 'data'):
                    log_data['response'] = self._sanitize_data(response.data)
                elif response.content:
                    response_body = json.loads(response.content.decode('utf-8'))
                    log_data['response'] = self._sanitize_data(response_body)
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                log_data['response'] = '[Unable to parse response]'
        
        # Use appropriate log level based on status code
        if response.status_code >= 500:
            logger.error(f"Response: {json.dumps(log_data)}")
        elif response.status_code >= 400:
            logger.warning(f"Response: {json.dumps(log_data)}")
        else:
            logger.info(f"Response: {json.dumps(log_data)}")
        
        return response
    
    def process_exception(self, request, exception):
        """
        Log unhandled exceptions
        """
        user = getattr(request, 'user', None)
        user_email = getattr(user, 'email', 'anonymous') if user and hasattr(user, 'email') else 'anonymous'
        
        log_data = {
            'method': request.method,
            'path': request.path,
            'user': user_email,
            'ip': self._get_client_ip(request),
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
        }
        
        logger.error(f"Unhandled Exception: {json.dumps(log_data)}", exc_info=True)
        
        return None
    
    def _should_skip_logging(self, path):
        """
        Determine if logging should be skipped for this path
        """
        skip_paths = [
            '/admin/jsi18n/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _get_client_ip(self, request):
        """
        Get client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _sanitize_data(self, data):
        """
        Remove sensitive data from logs
        """
        if not isinstance(data, dict):
            return data
        
        sensitive_fields = [
            'password', 'token', 'secret', 'api_key', 'private_key',
            'access_token', 'refresh_token', 'card_number', 'cvv',
            'ssn', 'credit_card'
        ]
        
        sanitized = {}
        for key, value in data.items():
            if any(field in key.lower() for field in sensitive_fields):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized


class PerformanceLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to track slow requests
    """
    
    def process_request(self, request):
        request._perf_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_perf_start_time'):
            duration = time.time() - request._perf_start_time
            
            # Log slow requests (> 2 seconds)
            if duration > 2.0:
                logger.warning(
                    f"Slow Request: {request.method} {request.path} "
                    f"took {duration:.2f}s | Status: {response.status_code}"
                )
        
        return response
