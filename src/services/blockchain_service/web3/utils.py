"""
Web3 Utility Functions
Helper functions for blockchain operations
"""
from web3 import Web3


def to_wei(value, unit='ether'):
    """
    Convert value to Wei
    
    Args:
        value (float/int/str): Value to convert
        unit (str): Unit (ether, gwei, wei)
        
    Returns:
        int: Value in Wei
    """
    return Web3.to_wei(value, unit)


def from_wei(value, unit='ether'):
    """
    Convert Wei to other unit
    
    Args:
        value (int): Value in Wei
        unit (str): Target unit (ether, gwei, wei)
        
    Returns:
        float: Converted value
    """
    return Web3.from_wei(value, unit)


def is_valid_address(address):
    """
    Check if address is valid Ethereum address
    
    Args:
        address (str): Address to validate
        
    Returns:
        bool: True if valid
    """
    return Web3.is_address(address)


def to_checksum_address(address):
    """
    Convert address to checksum format
    
    Args:
        address (str): Ethereum address
        
    Returns:
        str: Checksummed address
    """
    return Web3.to_checksum_address(address)


def keccak(text):
    """
    Get Keccak-256 hash of text
    
    Args:
        text (str): Text to hash
        
    Returns:
        bytes: Keccak hash
    """
    return Web3.keccak(text=text)
