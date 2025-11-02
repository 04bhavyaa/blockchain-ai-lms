"""
Custom validators for the API
"""

import re
from django.core.exceptions import ValidationError as DjangoValidationError


def validate_email(email):
    """Validate email format"""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        raise DjangoValidationError('Invalid email format')


def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        raise DjangoValidationError('Password must be at least 8 characters')
    
    if not any(char.isupper() for char in password):
        raise DjangoValidationError('Password must contain uppercase letter')
    
    if not any(char.islower() for char in password):
        raise DjangoValidationError('Password must contain lowercase letter')
    
    if not any(char.isdigit() for char in password):
        raise DjangoValidationError('Password must contain digit')
    
    if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in password):
        raise DjangoValidationError('Password must contain special character')


def validate_wallet_address(address):
    """Validate Ethereum wallet address"""
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        raise DjangoValidationError('Invalid wallet address format')
