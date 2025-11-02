"""
Custom exception classes for the API
"""

from rest_framework import status
from rest_framework.exceptions import APIException


class BaseAPIException(APIException):
    """Base exception for all custom API exceptions"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'An error occurred'


class ValidationError(BaseAPIException):
    """Validation error"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid input'


class AuthenticationError(BaseAPIException):
    """Authentication failed"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentication failed'


class PermissionDeniedError(BaseAPIException):
    """Permission denied"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Permission denied'


class ResourceNotFoundError(BaseAPIException):
    """Resource not found"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found'


class ConflictError(BaseAPIException):
    """Resource conflict (duplicate, etc.)"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Conflict'


class PaymentError(BaseAPIException):
    """Payment processing error"""
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = 'Payment failed'


class BlockchainError(BaseAPIException):
    """Blockchain operation error"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Blockchain service unavailable'


class RateLimitError(BaseAPIException):
    """Rate limit exceeded"""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Rate limit exceeded'

class ApplicationError(BaseAPIException):
    """Generic application-level exception"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Application error'

    def __init__(self, message=None, details=None, errors=None):
        self.message = message or self.default_detail
        self.details = details or {}
        self.errors = errors or []
        super().__init__(detail=self.message)


class InvalidTokenError(BaseAPIException):
    """Invalid or expired token"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Invalid or expired token'
