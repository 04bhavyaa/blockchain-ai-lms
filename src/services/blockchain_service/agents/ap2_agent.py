"""
AP2 Agent - Monitors PurchaseInitiated events and executes purchases
This agent watches for PurchaseInitiated events on the AP2 contract 
and calls executePurchase when preconditions are met.
"""
import time
import logging
from web3 import Web3
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    geth_poa_middleware = None
from django.conf import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load from Django settings instead of .env
RPC = getattr(settings, 'WEB3_PROVIDER_URL', 'http://localhost:8545')
PRIVATE_KEY = getattr(settings, 'PLATFORM_PRIVATE_KEY', '')
CONTRACT_ADDRESS = getattr(settings, 'AP2_CONTRACT_ADDRESS', '')
POLL_INTERVAL = 6  # seconds between polls

if not PRIVATE_KEY or not CONTRACT_ADDRESS:
    logger.warning("PLATFORM_PRIVATE_KEY or AP2_CONTRACT_ADDRESS not set. Agent will not run.")


def load_abi():
    """Load AP2 contract ABI from Hardhat artifact"""
    import os
    import json
    
    abi_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 'hardhat', 'artifacts', 'contracts', 'AP2.sol', 'AP2.json'
    )
    
    if os.path.exists(abi_path):
        with open(abi_path) as f:
            data = json.load(f)
            return data.get('abi') or data
    
    # Fallback minimal ABI
    return [
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "internalType": "uint256", "name": "purchaseId", "type": "uint256"},
                {"indexed": True, "internalType": "address", "name": "buyer", "type": "address"},
                {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
                {"indexed": False, "internalType": "uint256", "name": "courseId", "type": "uint256"}
            ],
            "name": "PurchaseInitiated",
            "type": "event"
        },
        {
            "inputs": [{"internalType": "uint256", "name": "purchaseId", "type": "uint256"}],
            "name": "executePurchase",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]


def main():
    """Main AP2 agent loop"""
    w3 = Web3(Web3.HTTPProvider(RPC))
    
    # Inject PoA middleware for testnets
    try:
        if getattr(settings, 'BLOCKCHAIN_NETWORK', 'localhost') != 'localhost':
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    except Exception:
        pass
    
    if not w3.is_connected():
        logger.error(f"Web3 RPC not reachable: {RPC}")
        return
    
    abi = load_abi()
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS), 
        abi=abi
    )
    
    account = None
    if PRIVATE_KEY:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        logger.info(f"Agent will use account: {account.address}")
    
    last_checked = w3.eth.block_number
    logger.info(f"Starting AP2 agent loop, initial block: {last_checked}")
    
    while True:
        try:
            latest = w3.eth.block_number
            
            if latest > last_checked:
                # Poll for PurchaseInitiated events
                events = contract.events.PurchaseInitiated.get_logs(
                    fromBlock=last_checked + 1, 
                    toBlock=latest
                )
                
                for ev in events:
                    purchase_id = ev['args']['purchaseId']
                    buyer = ev['args']['buyer']
                    amount = ev['args']['amount']
                    course_id = ev['args']['courseId']
                    
                    logger.info(
                        f"Found PurchaseInitiated: ID={purchase_id}, "
                        f"Buyer={buyer}, Amount={amount}, Course={course_id}"
                    )
                    
                    if account:
                        # Execute purchase
                        nonce = w3.eth.get_transaction_count(account.address)
                        
                        tx = contract.functions.executePurchase(purchase_id).build_transaction({
                            'from': account.address,
                            'nonce': nonce,
                            'gas': 500000,
                            'gasPrice': w3.eth.gas_price
                        })
                        
                        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
                        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
                        
                        logger.info(f"executePurchase tx sent: {tx_hash.hex()}")
                    else:
                        logger.warning(f"No agent private key configured, skipping executePurchase for {purchase_id}")
                
                last_checked = latest
            
            time.sleep(POLL_INTERVAL)
            
        except Exception as e:
            logger.exception(f"Agent loop error: {e}")
            time.sleep(5)


if __name__ == '__main__':
    main()
