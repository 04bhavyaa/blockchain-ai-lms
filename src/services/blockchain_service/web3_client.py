"""
Web3.py client for blockchain interactions
"""

from web3 import Web3
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Web3Client:
    """Web3 client for Ethereum/Polygon interactions"""
    
    def __init__(self, network='sepolia'):
        self.network = network
        
        # Get RPC URL from settings
        rpc_urls = {
            'sepolia': settings.WEB3_SEPOLIA_RPC if hasattr(settings, 'WEB3_SEPOLIA_RPC') else None,
            'polygon': settings.WEB3_POLYGON_RPC if hasattr(settings, 'WEB3_POLYGON_RPC') else None,
        }
        
        self.provider_url = rpc_urls.get(network)
        if not self.provider_url:
            raise ValueError(f"RPC URL not configured for {network}")
        
        self.w3 = Web3(Web3.HTTPProvider(self.provider_url))
        
        if not self.w3.is_connected():
            logger.error(f"Failed to connect to {network} RPC")
            raise ConnectionError(f"Cannot connect to {network} provider")
    
    def is_connected(self):
        """Check if connected to blockchain"""
        return self.w3.is_connected()
    
    def get_wallet_balance(self, wallet_address):
        """Get ETH balance of wallet"""
        try:
            address = Web3.to_checksum_address(wallet_address)
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return 0
    
    def get_token_balance(self, token_contract_address, wallet_address, contract_abi):
        """Get ERC20 token balance on-chain"""
        try:
            contract_address = Web3.to_checksum_address(token_contract_address)
            wallet_address = Web3.to_checksum_address(wallet_address)
            
            contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
            balance = contract.functions.balanceOf(wallet_address).call()
            
            logger.info(f"Token balance for {wallet_address[:10]}...: {balance}")
            return balance
        
        except Exception as e:
            logger.error(f"Error getting token balance: {str(e)}")
            return 0
    
    def get_token_allowance(self, token_contract_address, owner_address, spender_address, contract_abi):
        """Get ERC20 token allowance (how much spender can spend)"""
        try:
            contract_address = Web3.to_checksum_address(token_contract_address)
            owner_address = Web3.to_checksum_address(owner_address)
            spender_address = Web3.to_checksum_address(spender_address)
            
            contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
            allowance = contract.functions.allowance(owner_address, spender_address).call()
            
            logger.info(f"Allowance: {allowance}")
            return allowance
        
        except Exception as e:
            logger.error(f"Error getting allowance: {str(e)}")
            return 0
    
    def get_transaction_receipt(self, tx_hash):
        """Get transaction receipt from blockchain"""
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            if not receipt:
                return None
            
            return {
                'status': receipt['status'],
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'transaction_hash': receipt['transactionHash'].hex(),
                'contract_address': receipt['contractAddress'],
                'from': receipt['from'],
                'to': receipt['to'],
                'logs': receipt['logs'],
            }
        
        except Exception as e:
            logger.error(f"Error getting transaction receipt: {str(e)}")
            return None
    
    def get_transaction_confirmation_count(self, tx_hash):
        """Get number of confirmations for transaction"""
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            if not receipt:
                return 0
            
            latest_block = self.w3.eth.block_number
            confirmations = latest_block - receipt['blockNumber']
            
            return confirmations
        
        except Exception as e:
            logger.error(f"Error getting confirmation count: {str(e)}")
            return 0
    
    def verify_signature(self, message, signature, wallet_address):
        """Verify signature from wallet"""
        try:
            recovered_address = self.w3.eth.account.recover_message(
                Web3.to_bytes(text=message),
                signature=signature
            )
            return recovered_address.lower() == wallet_address.lower()
        
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            return False
    
    def get_latest_block(self):
        """Get latest block number"""
        try:
            return self.w3.eth.block_number
        except Exception as e:
            logger.error(f"Error getting block number: {str(e)}")
            return None
    
    def estimate_gas_price(self):
        """Get current gas price"""
        try:
            gas_price_wei = self.w3.eth.gas_price
            gas_price_gwei = self.w3.from_wei(gas_price_wei, 'gwei')
            return float(gas_price_gwei)
        except Exception as e:
            logger.error(f"Error getting gas price: {str(e)}")
            return 0
