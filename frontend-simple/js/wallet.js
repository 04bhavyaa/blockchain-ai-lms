/**
 * MetaMask Wallet Integration
 * Handles wallet connection, network switching, and account management
 */

/**
 * Check if MetaMask is installed
 */
function isMetaMaskInstalled() {
    return typeof window.ethereum !== 'undefined' && window.ethereum.isMetaMask;
}

/**
 * Request MetaMask account access
 */
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

/**
 * Connect wallet and save to backend
 */
async function connectWalletToAccount() {
    const connectBtn = document.getElementById('connect-wallet-btn');
    
    try {
        if (connectBtn) window.utils.setLoading(connectBtn, true);
        
        // Check MetaMask
        if (!isMetaMaskInstalled()) {
            window.utils.showAlert('error', 'MetaMask is not installed. Please install the MetaMask extension to connect your wallet.');
            window.open('https://metamask.io/download', '_blank');
            return;
        }
        
        // Request account
        const account = await requestMetaMaskAccount();
        console.log('Wallet Connected:', account);
        
        // Check if on correct network
        try {
            await window.contracts.checkNetwork();
        } catch (networkError) {
            // Wrong network, try to switch
            const shouldSwitch = confirm(`${networkError.message}\n\nWould you like to switch to Hardhat Localhost network?`);
            
            if (shouldSwitch) {
                try {
                    await window.contracts.switchToHardhatNetwork();
                    window.utils.showAlert('success', 'Network switched successfully!');
                } catch (switchError) {
                    throw new Error('Failed to switch network. Please switch manually in MetaMask.');
                }
            } else {
                throw new Error('Please switch to Hardhat Localhost network to continue.');
            }
        }
        
        // Get token balance
        const tokenBalance = await window.contracts.getTokenBalance(account);
        console.log('Token Balance:', tokenBalance, window.WEB3_CONFIG.CONTRACTS.TOKEN.symbol);
        
        // Send to backend (optional - for linking wallet to user account)
        try {
            const response = await window.api.connectWallet({
                wallet_address: account,
                network: 'localhost'
            });
            
            if (response.status === 'success') {
                window.utils.showAlert('success', `Wallet connected successfully!\nAddress: ${account.slice(0, 6)}...${account.slice(-4)}\nBalance: ${parseFloat(tokenBalance).toFixed(2)} ${window.WEB3_CONFIG.CONTRACTS.TOKEN.symbol}`);
                
                // Update user profile
                const user = window.utils.getUser();
                if (user) {
                    user.wallet_address = account;
                    window.utils.setUser(user);
                }
                
                // Reload if on profile page
                if (window.location.pathname.includes('profile') || window.location.pathname.includes('dashboard')) {
                    setTimeout(() => window.location.reload(), 2000);
                }
            }
        } catch (backendError) {
            console.warn('Backend wallet link failed (continuing anyway):', backendError);
            // Still show success since MetaMask connection worked
            window.utils.showAlert('success', `MetaMask connected!\nAddress: ${account.slice(0, 6)}...${account.slice(-4)}`);
        }
        
    } catch (error) {
        console.error('Wallet Connection error:', error);
        window.utils.showAlert('error', error.message || 'Failed to connect wallet');
    } finally {
        if (connectBtn) window.utils.setLoading(connectBtn, false);
    }
}

/**
 * Get connected account
 */
async function getConnectedAccount() {
    if (!isMetaMaskInstalled()) {
        return null;
    }
    
    try {
        const accounts = await window.ethereum.request({ method: 'eth_accounts' });
        return accounts.length > 0 ? accounts[0] : null;
    } catch (error) {
        console.error('Error getting connected account:', error);
        return null;
    }
}

/**
 * Check wallet connection status
 */
async function checkWalletConnection() {
    try {
        const account = await getConnectedAccount();
        return account !== null;
    } catch (error) {
        console.error('Wallet Check connection error:', error);
        return false;
    }
}

/**
 * Display wallet info in UI
 */
async function displayWalletInfo(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const account = await getConnectedAccount();
    
    if (account) {
        const tokenBalance = await window.contracts.getTokenBalance(account);
        element.innerHTML = `
            <div class="wallet-info">
                <div class="wallet-address">
                    <strong>Address:</strong> ${account.slice(0, 6)}...${account.slice(-4)}
                </div>
                <div class="wallet-balance">
                    <strong>Balance:</strong> ${parseFloat(tokenBalance).toFixed(2)} ${window.WEB3_CONFIG.CONTRACTS.TOKEN.symbol}
                </div>
            </div>
        `;
    } else {
        element.innerHTML = `
            <button onclick="window.wallet.connect()" class="btn btn-primary">
                Connect Wallet
            </button>
        `;
    }
}

/**
 * Setup wallet event listeners
 */
function setupWalletListeners() {
    if (!isMetaMaskInstalled()) return;
    
    // Listen for account changes
    window.ethereum.on('accountsChanged', (accounts) => {
        console.log('Wallet: Accounts changed:', accounts);
        
        if (accounts.length === 0) {
            window.utils.showAlert('info', 'MetaMask account disconnected');
        } else {
            window.utils.showAlert('info', `MetaMask account changed to ${accounts[0].slice(0, 10)}...`);
            // Reload page to update wallet info
            setTimeout(() => window.location.reload(), 1000);
        }
    });
    
    // Listen for chain changes
    window.ethereum.on('chainChanged', (chainId) => {
        console.log('Wallet: Chain changed:', chainId);
        // Reload on network change
        window.location.reload();
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
    getAccount: getConnectedAccount,
    isInstalled: isMetaMaskInstalled,
    displayInfo: displayWalletInfo
};

console.log('✅ Wallet module loaded');
