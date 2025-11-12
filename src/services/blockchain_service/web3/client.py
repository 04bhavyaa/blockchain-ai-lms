"""
Web3 Client for Ethereum Blockchain Interaction
Supports localhost (Hardhat) and testnets (Sepolia, etc.)
"""
from web3 import Web3
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    # Fallback for newer web3.py versions
    from web3.middleware import construct_sign_and_send_raw_middleware
    geth_poa_middleware = None
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Web3Client:
    """
    Web3 client for interacting with Ethereum blockchain
    Automatically connects to provider from settings
    """
    
    def __init__(self, network=None):
        """
        Initialize Web3 client
        
        Args:
            network (str): Network name (localhost, sepolia, etc.)
                          If None, uses settings.BLOCKCHAIN_NETWORK
        """
        self.network = network or getattr(settings, 'BLOCKCHAIN_NETWORK', 'localhost')
        
        # Get provider URL from settings
        provider_url = getattr(settings, 'WEB3_PROVIDER_URL', 'http://localhost:8545')
        
        try:
            self.w3 = Web3(Web3.HTTPProvider(provider_url))
            
            # Inject PoA middleware for testnets (not needed for localhost)
            if self.network != 'localhost' and geth_poa_middleware:
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if self.is_connected():
                logger.info(f"Web3 client connected to {self.network} at {provider_url}")
            else:
                logger.warning(f"Web3 client created but not connected to {provider_url}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Web3 client: {e}")
            raise
    
    def is_connected(self):
        """Check if Web3 is connected to provider"""
        try:
            return self.w3.is_connected()
        except Exception as e:
            logger.error(f"Error checking Web3 connection: {e}")
            return False
    
    def get_wallet_balance(self, wallet_address):
        """
        Get ETH balance of wallet address
        
        Args:
            wallet_address (str): Ethereum address
            
        Returns:
            float: Balance in ETH
        """
        try:
            balance_wei = self.w3.eth.get_balance(wallet_address)
            return self.w3.from_wei(balance_wei, 'ether')
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
            return 0
    
    def get_transaction_receipt(self, tx_hash):
        """
        Get transaction receipt
        
        Args:
            tx_hash (str): Transaction hash
            
        Returns:
            dict: Transaction receipt or None
        """
        try:
            return self.w3.eth.get_transaction_receipt(tx_hash)
        except Exception as e:
            logger.error(f"Error getting transaction receipt for {tx_hash}: {e}")
            return None
    
    def get_block_number(self):
        """Get current block number"""
        try:
            return self.w3.eth.block_number
        except Exception as e:
            logger.error(f"Error getting block number: {e}")
            return 0
    
    def get_transaction(self, tx_hash):
        """Get transaction details"""
        try:
            return self.w3.eth.get_transaction(tx_hash)
        except Exception as e:
            logger.error(f"Error getting transaction {tx_hash}: {e}")
            return None
    
    def get_gas_price(self):
        """Get current gas price in Gwei"""
        try:
            gas_price_wei = self.w3.eth.gas_price
            return self.w3.from_wei(gas_price_wei, 'gwei')
        except Exception as e:
            logger.error(f"Error getting gas price: {e}")
            return 0
    
    def get_token_balance(self, token_contract_address, wallet_address):
        """
        Get ERC20 token balance
        
        Args:
            token_contract_address (str): Token contract address
            wallet_address (str): Wallet to check
            
        Returns:
            int: Token balance (in token's smallest unit)
        """
        try:
            # Minimal ERC20 ABI for balanceOf
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }
            ]
            
            contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(token_contract_address),
                abi=erc20_abi
            )
            
            balance = contract.functions.balanceOf(
                self.w3.to_checksum_address(wallet_address)
            ).call()
            
            return balance
            
        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            return 0
