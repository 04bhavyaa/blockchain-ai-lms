/**
 * MetaMask Wallet Integration
 */

// Check if MetaMask is installed
function isMetaMaskInstalled() {
    return typeof window.ethereum !== 'undefined' && window.ethereum.isMetaMask;
}

// Request MetaMask account access
async function requestMetaMaskAccount() {
    if (!isMetaMaskInstalled()) {
        throw new Error('MetaMask is not installed. Please install MetaMask extension.');
    }
    
    try {
        // Request account access
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        
        if (accounts.length === 0) {
            throw new Error('No accounts found. Please unlock MetaMask.');
        }
        
        return accounts[0]; // Return first account
    } catch (error) {
        if (error.code === 4001) {
            // User rejected request
            throw new Error('Please approve the connection request in MetaMask.');
        }
        throw error;
    }
}

// Sign message with MetaMask
async function signMessageWithMetaMask(message, account) {
    if (!isMetaMaskInstalled()) {
        throw new Error('MetaMask is not installed.');
    }
    
    try {
        const signature = await window.ethereum.request({
            method: 'personal_sign',
            params: [message, account],
        });
        
        return signature;
    } catch (error) {
        if (error.code === 4001) {
            throw new Error('Signature request was rejected.');
        }
        throw error;
    }
}

// Connect wallet to account
async function connectWalletToAccount() {
    try {
        window.utils.setLoading(document.getElementById('connect-wallet-btn'), true);
        
        // Check MetaMask
        if (!isMetaMaskInstalled()) {
            window.utils.showAlert('error', 'MetaMask is not installed. Please install the MetaMask extension to connect your wallet.');
            window.open('https://metamask.io/download/', '_blank');
            return;
        }
        
        // Request account
        const account = await requestMetaMaskAccount();
        console.log('[Wallet] Connected account:', account);
        
        // Sign message for verification
        const message = `Connect wallet to Blockchain AI LMS: ${account}`;
        const signature = await signMessageWithMetaMask(message, account);
        console.log('[Wallet] Signature obtained');
        
        // Get network
        const chainId = await window.ethereum.request({ method: 'eth_chainId' });
        let network = 'sepolia';
        
        // Map chain ID to network
        const chainIdMap = {
            '0x1': 'ethereum',
            '0xaa36a7': 'sepolia', // Sepolia testnet
            '0x89': 'polygon',
        };
        network = chainIdMap[chainId] || 'sepolia';
        
        // Send to backend
        const response = await window.api.connectWallet({
            wallet_address: account,
            signature: signature,
            network: network
        });
        
        if (response.status === 'success') {
            window.utils.showAlert('success', 'Wallet connected successfully!');
            
            // Update user profile
            const user = window.utils.getUser();
            if (user) {
                user.wallet_address = account;
                window.utils.setUser(user);
            }
            
            // Reload profile page if on profile
            if (window.location.pathname.includes('profile')) {
                setTimeout(() => window.location.reload(), 1000);
            }
        }
    } catch (error) {
        console.error('[Wallet] Connection error:', error);
        window.utils.showAlert('error', error.message || 'Failed to connect wallet');
    } finally {
        const btn = document.getElementById('connect-wallet-btn');
        if (btn) {
            window.utils.setLoading(btn, false);
        }
    }
}

// Check wallet connection status
async function checkWalletConnection() {
    try {
        const user = window.utils.getUser();
        if (!user || !user.wallet_address) {
            return false;
        }
        
        // Optionally verify with MetaMask
        if (isMetaMaskInstalled()) {
            const accounts = await window.ethereum.request({ method: 'eth_accounts' });
            return accounts.some(acc => acc.toLowerCase() === user.wallet_address.toLowerCase());
        }
        
        return true; // User has wallet_address in profile
    } catch (error) {
        console.error('[Wallet] Check connection error:', error);
        return false;
    }
}

// Listen for account changes
function setupWalletListeners() {
    if (!isMetaMaskInstalled()) return;
    
    // Listen for account changes
    window.ethereum.on('accountsChanged', (accounts) => {
        console.log('[Wallet] Accounts changed:', accounts);
        if (accounts.length === 0) {
            window.utils.showAlert('info', 'MetaMask account disconnected');
        } else {
            window.utils.showAlert('info', `MetaMask account changed to: ${accounts[0].slice(0, 10)}...`);
        }
    });
    
    // Listen for chain changes
    window.ethereum.on('chainChanged', (chainId) => {
        console.log('[Wallet] Chain changed:', chainId);
        window.location.reload(); // Reload on network change
    });
}

// Initialize wallet listeners on page load
if (typeof window !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        setupWalletListeners();
    });
}

// Export functions
window.wallet = {
    connect: connectWalletToAccount,
    checkConnection: checkWalletConnection,
    isInstalled: isMetaMaskInstalled,
    requestAccount: requestMetaMaskAccount,
    signMessage: signMessageWithMetaMask
};

