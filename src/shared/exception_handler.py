"""
Custom exception handler for DRF to standardize error responses across the API
"""
import logging
import traceback
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.db import IntegrityError

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all errors consistently
    Returns standardized error response format:
    {
        'status': 'error',
        'message': 'Human readable error message',
        'errors': {...},  # Field-specific errors if applicable
        'error_code': 'ERROR_CODE',  # Machine-readable error code
        'timestamp': '2024-01-01T00:00:00Z',
        'path': '/api/v1/endpoint'
    }
    """
    # Get the standard error response first
    response = exception_handler(exc, context)
    
    # Get request info for logging
    request = context.get('request')
    view = context.get('view')
    
    request_info = {
        'method': getattr(request, 'method', 'UNKNOWN'),
        'path': getattr(request, 'path', 'unknown'),
        'user': getattr(getattr(request, 'user', None), 'email', 'anonymous'),
        'ip': get_client_ip(request) if request else 'unknown',
    }
    
    # Handle DRF exceptions (response is not None)
    if response is not None:
        error_data = format_error_response(
            exc=exc,
            status_code=response.status_code,
            response_data=response.data,
            request_info=request_info
        )
        
        # Log the error
        log_exception(exc, error_data, request_info)
        
        return Response(error_data, status=response.status_code)
    
    # Handle non-DRF exceptions (response is None)
    # These are typically Python exceptions that DRF doesn't handle
    
    if isinstance(exc, DjangoValidationError):
        error_data = format_error_response(
            exc=exc,
            status_code=status.HTTP_400_BAD_REQUEST,
            response_data={'detail': str(exc)},
            request_info=request_info,
            error_code='VALIDATION_ERROR'
        )
        log_exception(exc, error_data, request_info)
        return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
    
    if isinstance(exc, Http404):
        error_data = format_error_response(
            exc=exc,
            status_code=status.HTTP_404_NOT_FOUND,
            response_data={'detail': 'Not found'},
            request_info=request_info,
            error_code='NOT_FOUND'
        )
        log_exception(exc, error_data, request_info)
        return Response(error_data, status=status.HTTP_404_NOT_FOUND)
    
    if isinstance(exc, IntegrityError):
        error_data = format_error_response(
            exc=exc,
            status_code=status.HTTP_409_CONFLICT,
            response_data={'detail': 'Database integrity error. Resource may already exist.'},
            request_info=request_info,
            error_code='INTEGRITY_ERROR'
        )
        log_exception(exc, error_data, request_info)
        return Response(error_data, status=status.HTTP_409_CONFLICT)
    
    # Unhandled exception - return 500
    error_data = format_error_response(
        exc=exc,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        response_data={'detail': 'Internal server error'},
        request_info=request_info,
        error_code='INTERNAL_ERROR'
    )
    
    # Log with full traceback for 500 errors
    log_exception(exc, error_data, request_info, include_traceback=True)
    
    return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def format_error_response(exc, status_code, response_data, request_info, error_code=None):
    """
    Format error response in a consistent structure
    """
    from django.utils import timezone
    
    # Extract message from various error formats
    message = extract_error_message(response_data)
    
    # Extract field-specific errors
    errors = extract_field_errors(response_data)
    
    # Determine error code
    if not error_code:
        error_code = determine_error_code(exc, status_code)
    
    error_response = {
        'status': 'error',
        'message': message,
        'error_code': error_code,
        'timestamp': timezone.now().isoformat(),
        'path': request_info.get('path', 'unknown'),
    }
    
    # Add field errors if they exist
    if errors:
        error_response['errors'] = errors
    
    # Add debugging info in development
    from django.conf import settings
    if settings.DEBUG:
        error_response['debug'] = {
            'exception_type': type(exc).__name__,
            'exception_message': str(exc),
        }
    
    return error_response


def extract_error_message(response_data):
    """
    Extract a human-readable error message from various response formats
    """
    if isinstance(response_data, str):
        return response_data
    
    if isinstance(response_data, dict):
        # Check for common message keys
        for key in ['message', 'detail', 'error', 'non_field_errors']:
            if key in response_data:
                value = response_data[key]
                if isinstance(value, list):
                    return ', '.join(str(v) for v in value)
                return str(value)
        
        # If it's field errors, create a summary message
        if any(key not in ['message', 'detail', 'error'] for key in response_data.keys()):
            return 'Validation error occurred'
    
    if isinstance(response_data, list):
        return ', '.join(str(item) for item in response_data)
    
    return 'An error occurred'


def extract_field_errors(response_data):
    """
    Extract field-specific errors from response data
    """
    if not isinstance(response_data, dict):
        return None
    
    # Filter out message keys to get field errors
    message_keys = ['message', 'detail', 'error', 'non_field_errors']
    field_errors = {
        key: value for key, value in response_data.items()
        if key not in message_keys
    }
    
    return field_errors if field_errors else None


def determine_error_code(exc, status_code):
    """
    Determine a machine-readable error code based on exception type and status
    """
    exc_name = type(exc).__name__
    
    # Map exception types to error codes
    error_code_map = {
        'ValidationError': 'VALIDATION_ERROR',
        'AuthenticationError': 'AUTHENTICATION_ERROR',
        'PermissionDeniedError': 'PERMISSION_DENIED',
        'ResourceNotFoundError': 'RESOURCE_NOT_FOUND',
        'ConflictError': 'CONFLICT_ERROR',
        'PaymentError': 'PAYMENT_ERROR',
        'BlockchainError': 'BLOCKCHAIN_ERROR',
        'RateLimitError': 'RATE_LIMIT_ERROR',
        'NotAuthenticated': 'NOT_AUTHENTICATED',
        'PermissionDenied': 'PERMISSION_DENIED',
        'NotFound': 'NOT_FOUND',
        'MethodNotAllowed': 'METHOD_NOT_ALLOWED',
        'Throttled': 'THROTTLED',
    }
    
    if exc_name in error_code_map:
        return error_code_map[exc_name]
    
    # Fallback to status code based error codes
    status_code_map = {
        400: 'BAD_REQUEST',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        409: 'CONFLICT',
        429: 'TOO_MANY_REQUESTS',
        500: 'INTERNAL_SERVER_ERROR',
        502: 'BAD_GATEWAY',
        503: 'SERVICE_UNAVAILABLE',
    }
    
    return status_code_map.get(status_code, 'UNKNOWN_ERROR')


def log_exception(exc, error_data, request_info, include_traceback=False):
    """
    Log exception with appropriate level and context
    """
    status_code = error_data.get('error_code', 'UNKNOWN')
    
    log_message = (
        f"API Error - {status_code} | "
        f"{request_info['method']} {request_info['path']} | "
        f"User: {request_info['user']} | "
        f"IP: {request_info['ip']} | "
        f"Message: {error_data['message']}"
    )
    
    # Determine log level based on status code
    if error_data.get('error_code') in ['INTERNAL_ERROR', 'BLOCKCHAIN_ERROR', 'PAYMENT_ERROR']:
        logger.error(log_message)
        if include_traceback:
            logger.error(f"Traceback: {traceback.format_exc()}")
    elif error_data.get('error_code') in ['VALIDATION_ERROR', 'NOT_FOUND']:
        logger.warning(log_message)
    else:
        logger.info(log_message)


def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
