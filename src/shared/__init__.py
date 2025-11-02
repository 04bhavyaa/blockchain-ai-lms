"""
Shared utilities module for LMS platform
"""

from .exceptions import (
    ApplicationError,
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    AuthenticationError,
    ConflictError,
    BlockchainError,
    PaymentError,
    RateLimitError,
    InvalidTokenError,
)

from .decorators import (
    require_admin,
    require_authenticated,
    log_action,
)

from .validators import (
    validate_email,
    validate_password,
    validate_wallet_address
)

from .utils import (
    generate_random_token,
    calculate_completion_percentage,
    get_client_ip,
    send_email,
    format_duration
)

from .constants import (
    TOKEN_REWARDS,
    TOKEN_COSTS,
    RECOMMENDATION_WEIGHTS,
    COURSE_STATUSES,
    DIFFICULTY_LEVELS,
    ACCESS_TYPES
)

__all__ = [
    # Exceptions
    'ApplicationError',
    'ValidationError',
    'ResourceNotFoundError',
    'PermissionDeniedError',
    'AuthenticationError',
    'ConflictError',
    'BlockchainError',
    'PaymentError',
    'RateLimitError',
    'InvalidTokenError',
    # Decorators
    'require_admin',
    'require_authenticated',
    'log_action',
    # Validators
    'validate_email',
    'validate_password',
    'validate_wallet_address',
    # Utils
    'generate_random_token',
    'calculate_completion_percentage',
    'get_client_ip',
    'send_email',
    'format_duration',
    # Constants
    'TOKEN_REWARDS',
    'TOKEN_COSTS',
    'RECOMMENDATION_WEIGHTS',
    'COURSE_STATUSES',
    'DIFFICULTY_LEVELS',
    'ACCESS_TYPES'
]
