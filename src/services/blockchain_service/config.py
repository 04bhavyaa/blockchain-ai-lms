"""
Blockchain Service Configuration
Loads blockchain-related environment variables for localhost/testnet deployment
"""
import os
from django.conf import settings

# Web3 Provider Configuration
WEB3_PROVIDER_URL = getattr(settings, 'WEB3_PROVIDER_URL', 'http://localhost:8545')
BLOCKCHAIN_NETWORK = getattr(settings, 'BLOCKCHAIN_NETWORK', 'localhost')
BLOCKCHAIN_ENABLED = getattr(settings, 'BLOCKCHAIN_ENABLED', False)

# Contract Addresses (from deploy.js output)
TOKEN_CONTRACT_ADDRESS = getattr(settings, 'TOKEN_CONTRACT_ADDRESS', '')
CERTIFICATE_CONTRACT_ADDRESS = getattr(settings, 'CERTIFICATE_CONTRACT_ADDRESS', '')
AP2_CONTRACT_ADDRESS = getattr(settings, 'AP2_CONTRACT_ADDRESS', '')

# Platform Wallet Credentials
PLATFORM_PRIVATE_KEY = getattr(settings, 'PLATFORM_PRIVATE_KEY', '')
TREASURY_ADDRESS = getattr(settings, 'TREASURY_ADDRESS', '')

# Validation
if BLOCKCHAIN_ENABLED:
    if not TOKEN_CONTRACT_ADDRESS:
        raise ValueError("TOKEN_CONTRACT_ADDRESS not set in settings")
    if not CERTIFICATE_CONTRACT_ADDRESS:
        raise ValueError("CERTIFICATE_CONTRACT_ADDRESS not set in settings")
    if not AP2_CONTRACT_ADDRESS:
        raise ValueError("AP2_CONTRACT_ADDRESS not set in settings")
    if not PLATFORM_PRIVATE_KEY:
        raise ValueError("PLATFORM_PRIVATE_KEY not set in settings")
    if not TREASURY_ADDRESS:
        raise ValueError("TREASURY_ADDRESS not set in settings")

# Export for backward compatibility
ERC20_CONTRACT_ADDRESS = TOKEN_CONTRACT_ADDRESS
ERC721_CONTRACT_ADDRESS = CERTIFICATE_CONTRACT_ADDRESS
PLATFORM_TREASURY_ADDRESS = TREASURY_ADDRESS