# src/services/blockchain_service/web3/client.py

import logging
from typing import Optional, Dict, Any
from decimal import Decimal

from web3 import Web3
from web3.types import TxParams, Wei
from eth_account import Account
from eth_account.signers.local import LocalAccount

# Updated imports for web3.py v6.x+
try:
    # For web3.py v7.x
    from web3.middleware import ExtraDataToPOAMiddleware
except ImportError:
    try:
        # For web3.py v6.x
        from web3.middleware import geth_poa_middleware as ExtraDataToPOAMiddleware
    except ImportError:
        # Fallback for older versions
        ExtraDataToPOAMiddleware = None

from django.conf import settings

logger = logging.getLogger(__name__)


class Web3Client:
    """
    Web3 client for interacting with Ethereum blockchain.
    Compatible with web3.py v6.x and v7.x
    """
    
    def __init__(self, rpc_url: Optional[str] = None, private_key: Optional[str] = None):
        """
        Initialize Web3 client.
        
        Args:
            rpc_url: Ethereum RPC endpoint URL
            private_key: Private key for signing transactions
        """
        self.rpc_url = rpc_url or settings.ETHEREUM_RPC_URL
        self.private_key = private_key or settings.PLATFORM_PRIVATE_KEY
        
        # Initialize Web3 instance
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Inject POA middleware if needed (for testnets like Sepolia, Mumbai)
        if ExtraDataToPOAMiddleware:
            try:
                self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            except Exception as e:
                logger.warning(f"Could not inject POA middleware: {e}")
        
        # Set up account
        self.account: Optional[LocalAccount] = None
        if self.private_key:
            try:
                self.account = Account.from_key(self.private_key)
                self.w3.eth.default_account = self.account.address
            except Exception as e:
                logger.error(f"Failed to load account from private key: {e}")
        
        # Check connection
        if not self.is_connected():
            logger.error(f"Failed to connect to Ethereum node at {self.rpc_url}")
    
    def is_connected(self) -> bool:
        """Check if connected to Ethereum node."""
        try:
            return self.w3.is_connected()
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False
    
    def get_balance(self, address: str) -> Wei:
        """Get ETH balance of an address."""
        try:
            return self.w3.eth.get_balance(Web3.to_checksum_address(address))
        except Exception as e:
            logger.error(f"Failed to get balance for {address}: {e}")
            return Wei(0)
    
    def get_balance_in_ether(self, address: str) -> Decimal:
        """Get ETH balance in ether (not wei)."""
        balance_wei = self.get_balance(address)
        return Decimal(str(self.w3.from_wei(balance_wei, 'ether')))
    
    def get_transaction_count(self, address: str) -> int:
        """Get transaction count (nonce) for an address."""
        try:
            return self.w3.eth.get_transaction_count(
                Web3.to_checksum_address(address)
            )
        except Exception as e:
            logger.error(f"Failed to get transaction count: {e}")
            return 0
    
    def get_gas_price(self) -> Wei:
        """Get current gas price."""
        try:
            return self.w3.eth.gas_price
        except Exception as e:
            logger.error(f"Failed to get gas price: {e}")
            return Wei(0)
    
    def estimate_gas(self, transaction: TxParams) -> int:
        """Estimate gas for a transaction."""
        try:
            return self.w3.eth.estimate_gas(transaction)
        except Exception as e:
            logger.error(f"Failed to estimate gas: {e}")
            return 21000  # Default gas limit
    
    def build_transaction(
        self,
        to: str,
        value: Wei = Wei(0),
        data: bytes = b'',
        gas_limit: Optional[int] = None,
        gas_price: Optional[Wei] = None,
    ) -> TxParams:
        """Build a transaction dictionary."""
        if not self.account:
            raise ValueError("No account configured for signing transactions")
        
        tx: TxParams = {
            'from': self.account.address,
            'to': Web3.to_checksum_address(to),
            'value': value,
            'data': data,
            'nonce': self.get_transaction_count(self.account.address),
            'chainId': self.w3.eth.chain_id,
        }
        
        # Add gas parameters
        if gas_price:
            tx['gasPrice'] = gas_price
        else:
            tx['gasPrice'] = self.get_gas_price()
        
        if gas_limit:
            tx['gas'] = gas_limit
        else:
            try:
                tx['gas'] = self.estimate_gas(tx)
            except:
                tx['gas'] = 21000
        
        return tx
    
    def sign_transaction(self, transaction: TxParams) -> bytes:
        """Sign a transaction."""
        if not self.account:
            raise ValueError("No account configured for signing")
        
        try:
            signed = self.w3.eth.account.sign_transaction(
                transaction, 
                private_key=self.private_key
            )
            return signed.rawTransaction
        except Exception as e:
            logger.error(f"Failed to sign transaction: {e}")
            raise
    
    def send_raw_transaction(self, signed_tx: bytes) -> str:
        """Send a signed transaction and return transaction hash."""
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx)
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Failed to send transaction: {e}")
            raise
    
    def send_transaction(self, transaction: TxParams) -> str:
        """Sign and send a transaction."""
        signed_tx = self.sign_transaction(transaction)
        return self.send_raw_transaction(signed_tx)
    
    def wait_for_transaction_receipt(
        self, 
        tx_hash: str, 
        timeout: int = 120
    ) -> Dict[str, Any]:
        """Wait for transaction to be mined."""
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=timeout
            )
            return dict(receipt)
        except Exception as e:
            logger.error(f"Failed to get transaction receipt: {e}")
            raise
    
    def get_contract(self, address: str, abi: list):
        """Get a contract instance."""
        try:
            return self.w3.eth.contract(
                address=Web3.to_checksum_address(address),
                abi=abi
            )
        except Exception as e:
            logger.error(f"Failed to load contract: {e}")
            raise
    
    def call_contract_function(
        self,
        contract_address: str,
        abi: list,
        function_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Call a contract function (read-only)."""
        try:
            contract = self.get_contract(contract_address, abi)
            function = getattr(contract.functions, function_name)
            return function(*args, **kwargs).call()
        except Exception as e:
            logger.error(f"Failed to call contract function {function_name}: {e}")
            raise
    
    def send_contract_transaction(
        self,
        contract_address: str,
        abi: list,
        function_name: str,
        *args,
        gas_limit: Optional[int] = None,
        value: Wei = Wei(0),
        **kwargs
    ) -> str:
        """Execute a contract function (write transaction)."""
        try:
            contract = self.get_contract(contract_address, abi)
            function = getattr(contract.functions, function_name)
            
            # Build transaction
            tx = function(*args, **kwargs).build_transaction({
                'from': self.account.address,
                'value': value,
                'nonce': self.get_transaction_count(self.account.address),
                'gasPrice': self.get_gas_price(),
                'chainId': self.w3.eth.chain_id,
            })
            
            if gas_limit:
                tx['gas'] = gas_limit
            else:
                tx['gas'] = self.estimate_gas(tx)
            
            # Sign and send
            return self.send_transaction(tx)
        except Exception as e:
            logger.error(f"Failed to send contract transaction {function_name}: {e}")
            raise
    
    def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction details."""
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            return dict(tx)
        except Exception as e:
            logger.error(f"Failed to get transaction: {e}")
            return {}
    
    def get_block(self, block_identifier: int | str = 'latest') -> Dict[str, Any]:
        """Get block details."""
        try:
            block = self.w3.eth.get_block(block_identifier)
            return dict(block)
        except Exception as e:
            logger.error(f"Failed to get block: {e}")
            return {}


# Singleton instance
_web3_client: Optional[Web3Client] = None


def get_web3_client() -> Web3Client:
    """Get or create Web3 client singleton."""
    global _web3_client
    if _web3_client is None:
        _web3_client = Web3Client()
    return _web3_client
