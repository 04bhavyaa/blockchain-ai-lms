"""
Smart contract interaction helpers and ABIs
"""

from .models import SmartContractConfig
import logging

logger = logging.getLogger(__name__)

# ERC20 Token Contract ABI (Standard)
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
        "stateMutability": "nonpayable"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
        "stateMutability": "nonpayable"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
        "stateMutability": "view"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
        "stateMutability": "view"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
        "stateMutability": "view"
    }
]

# ERC721 NFT Certificate Contract ABI (Standard)
ERC721_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "tokenURI", "type": "string"}
        ],
        "name": "safeMint",
        "outputs": [],
        "type": "function",
        "stateMutability": "nonpayable"
    },
    {
        "constant": True,
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"name": "owner", "type": "address"}],
        "type": "function",
        "stateMutability": "view"
    },
    {
        "constant": True,
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
        "stateMutability": "view"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": True, "name": "tokenId", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }
]

class SmartContractManager:
    """Manage smart contract deployments and configurations"""

    @staticmethod
    def get_token_contract():
        """Get ERC20 token contract config"""
        try:
            return SmartContractConfig.objects.get(contract_type='token', is_active=True)
        except SmartContractConfig.DoesNotExist:
            logger.error("Token contract not deployed")
            return None

    @staticmethod
    def get_certificate_contract():
        """Get ERC721 certificate contract config"""
        try:
            return SmartContractConfig.objects.get(contract_type='certificate', is_active=True)
        except SmartContractConfig.DoesNotExist:
            logger.error("Certificate contract not deployed")
            return None

    @staticmethod
    def save_contract_config(contract_type, contract_address, deployment_hash, block_number):
        """Save deployed contract configuration"""
        try:
            abi = ERC20_ABI if contract_type == 'token' else ERC721_ABI
            config, created = SmartContractConfig.objects.update_or_create(
                contract_type=contract_type,
                defaults={
                    'contract_address': contract_address,
                    'contract_abi': abi,
                    'deployment_hash': deployment_hash,
                    'block_number': block_number,
                    'is_active': True,
                }
            )
            logger.info(
                f"Contract config {'created' if created else 'updated'}: "
                f"{contract_type} - {contract_address}"
            )
            return config
        except Exception as e:
            logger.error(f"Error saving contract config: {str(e)}")
            return None

    @staticmethod
    def get_abi_for_type(contract_type):
        """Get ABI for contract type"""
        if contract_type == 'token':
            return ERC20_ABI
        elif contract_type == 'certificate':
            return ERC721_ABI
        return None
