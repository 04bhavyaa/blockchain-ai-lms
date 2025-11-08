"""
AP2 Agent skeleton

This agent watches for PurchaseInitiated events on the AP2 contract and calls executePurchase
when preconditions are met. It uses environment variables for configuration:

AP2_RPC_URL - JSON-RPC URL (e.g., http://127.0.0.1:8545)
AP2_PRIVATE_KEY - agent private key for signing transactions
AP2_CONTRACT_ADDRESS - deployed AP2 contract address
AP2_POLL_INTERVAL - seconds between polls (default 6)

This is a minimal educational skeleton. Add robust error handling and agent authorization in production.
"""

import os
import time
import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

RPC = os.getenv('AP2_RPC_URL', 'http://127.0.0.1:8545')
PRIVATE_KEY = os.getenv('AP2_PRIVATE_KEY')
CONTRACT_ADDRESS = os.getenv('AP2_CONTRACT_ADDRESS')
POLL_INTERVAL = int(os.getenv('AP2_POLL_INTERVAL', '6'))

if not PRIVATE_KEY or not CONTRACT_ADDRESS:
    logger.warning('AP2_PRIVATE_KEY or AP2_CONTRACT_ADDRESS not set. Agent will not run until configured.')


def load_abi():
    # Attempt to load ABI from hardhat artifact if present
    abi_path = os.path.join(os.path.dirname(__file__), '..', 'hardhat', 'artifacts', 'contracts', 'AP2.sol', 'AP2.json')
    if os.path.exists(abi_path):
        import json
        with open(abi_path) as f:
            data = json.load(f)
            return data.get('abi') or data
    # Fallback: minimal ABI for events and executePurchase function
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
            "inputs": [{"internalType": "uint256","name":"purchaseId","type":"uint256"}],
            "name": "executePurchase",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]


def main():
    w3 = Web3(Web3.HTTPProvider(RPC))
    # if using local networks with POA
    try:
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    except Exception:
        pass

    if not w3.is_connected():
        logger.error('Web3 RPC not reachable: %s', RPC)
        return

    abi = load_abi()
    contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)

    account = None
    if PRIVATE_KEY:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        logger.info('Agent will use account: %s', account.address)

    # Poll for PurchaseInitiated events
    last_checked = w3.eth.block_number
    logger.info('Starting AP2 agent loop, initial block: %d', last_checked)

    while True:
        try:
            latest = w3.eth.block_number
            if latest > last_checked:
                # fetch events in range
                events = contract.events.PurchaseInitiated().get_logs(fromBlock=last_checked+1, toBlock=latest)
                for ev in events:
                    purchase_id = ev['args']['purchaseId']
                    buyer = ev['args']['buyer']
                    amount = ev['args']['amount']
                    course_id = ev['args']['courseId']
                    logger.info('Found PurchaseInitiated id=%s buyer=%s amount=%s course=%s', purchase_id, buyer, amount, course_id)

                    # Agent decision logic placeholder: here we simply execute immediately
                    if account:
                        nonce = w3.eth.get_transaction_count(account.address)
                        tx = contract.functions.executePurchase(purchase_id).build_transaction({
                            'from': account.address,
                            'nonce': nonce,
                            'gas': 500000,
                            'gasPrice': w3.eth.gas_price
                        })
                        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
                        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
                        logger.info('executePurchase tx sent: %s', tx_hash.hex())
                    else:
                        logger.warning('No agent private key configured; skipping executePurchase for %s', purchase_id)

                last_checked = latest

            time.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.exception('Agent loop error: %s', e)
            time.sleep(5)


if __name__ == '__main__':
    main()
