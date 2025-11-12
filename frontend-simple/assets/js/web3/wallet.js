import { WEB3_CONFIG } from '../config/web3_config.js';
import { showAlert } from '../utils/utils.js';
import { AuthService } from '../services/auth.js';

// Wallet state management
let walletState = {
    isConnected: false,
    address: null,
    chainId: null,
    balance: null,
};

// Event listeners for wallet changes
const walletListeners = [];

export const WalletService = {
    // Get current wallet state
    getState() {
        return { ...walletState };
    },

    // Subscribe to wallet state changes
    subscribe(listener) {
        walletListeners.push(listener);
        // Return unsubscribe function
        return () => {
            const index = walletListeners.indexOf(listener);
            if (index > -1) {
                walletListeners.splice(index, 1);
            }
        };
    },

    // Notify all listeners of state change
    notifyListeners() {
        walletListeners.forEach(listener => listener(walletState));
    },

    // Check if MetaMask is installed
    isMetaMaskInstalled() {
        return typeof window.ethereum !== 'undefined' && window.ethereum.isMetaMask;
    },

    // Initialize wallet connection (check if already connected)
    async initialize() {
        try {
            if (!this.isMetaMaskInstalled()) {
                console.log('MetaMask not installed');
                return false;
            }

            // Check if already connected
            const accounts = await window.ethereum.request({ 
                method: 'eth_accounts' 
            });

            if (accounts.length > 0) {
                await this.handleAccountsChanged(accounts);
                this.setupEventListeners();
                return true;
            }

            return false;
        } catch (error) {
            console.error('Wallet initialization error:', error);
            return false;
        }
    },

    // Setup MetaMask event listeners
    setupEventListeners() {
        if (!window.ethereum) return;

        // Account changed
        window.ethereum.on('accountsChanged', (accounts) => {
            this.handleAccountsChanged(accounts);
        });

        // Chain changed
        window.ethereum.on('chainChanged', (chainId) => {
            walletState.chainId = chainId;
            this.notifyListeners();
            // Reload page on chain change (recommended by MetaMask)
            window.location.reload();
        });

        // Disconnect
        window.ethereum.on('disconnect', () => {
            this.handleDisconnect();
        });
    },

    // Handle account changes
    async handleAccountsChanged(accounts) {
        if (accounts.length === 0) {
            this.handleDisconnect();
        } else {
            const address = accounts[0];
            walletState.isConnected = true;
            walletState.address = address;
            
            // Get chain ID
            const chainId = await window.ethereum.request({ 
                method: 'eth_chainId' 
            });
            walletState.chainId = chainId;

            // Get balance
            try {
                const balance = await window.ethereum.request({
                    method: 'eth_getBalance',
                    params: [address, 'latest'],
                });
                // Convert to ETH
                walletState.balance = parseInt(balance, 16) / 1e18;
            } catch (error) {
                console.error('Failed to get balance:', error);
            }

            // Update backend with wallet address
            try {
                if (AuthService.isAuthenticated()) {
                    await AuthService.updateProfile({ wallet_address: address });
                }
            } catch (error) {
                console.error('Failed to update wallet address on backend:', error);
            }

            this.notifyListeners();
        }
    },

    // Handle disconnect
    handleDisconnect() {
        walletState.isConnected = false;
        walletState.address = null;
        walletState.chainId = null;
        walletState.balance = null;
        this.notifyListeners();
    },

    // Connect wallet (request account access)
    async connect() {
        try {
            if (!this.isMetaMaskInstalled()) {
                const install = confirm('MetaMask not installed. Would you like to install it?');
                if (install) {
                    window.open('https://metamask.io/download/', '_blank');
                }
                throw new Error('MetaMask not installed');
            }

            // Request account access
            const accounts = await window.ethereum.request({ 
                method: 'eth_requestAccounts' 
            });

            if (accounts.length === 0) {
                throw new Error('No accounts found');
            }

            // Setup listeners if not already setup
            this.setupEventListeners();

            // Handle accounts
            await this.handleAccountsChanged(accounts);

            // Check network
            const chainId = await window.ethereum.request({ 
                method: 'eth_chainId' 
            });

            // Switch to correct network if needed
            if (chainId !== WEB3_CONFIG.NETWORK.CHAIN_ID) {
                await this.switchNetwork();
            }

            showAlert('success', `Wallet connected: ${this.formatAddress(walletState.address)}`);
            return walletState.address;
        } catch (error) {
            console.error('Wallet connection error:', error);
            if (error.code === 4001) {
                showAlert('error', 'Wallet connection rejected');
            } else {
                showAlert('error', error.message);
            }
            throw error;
        }
    },

    // Disconnect wallet
    async disconnect() {
        try {
            // Note: MetaMask doesn't have a programmatic disconnect
            // We just clear local state and notify backend
            walletState.isConnected = false;
            walletState.address = null;
            walletState.chainId = null;
            walletState.balance = null;

            // Update backend to remove wallet address
            if (AuthService.isAuthenticated()) {
                try {
                    await AuthService.updateProfile({ wallet_address: null });
                } catch (error) {
                    console.error('Failed to update backend:', error);
                }
            }

            this.notifyListeners();
            showAlert('success', 'Wallet disconnected');
        } catch (error) {
            console.error('Disconnect error:', error);
            showAlert('error', 'Failed to disconnect wallet');
        }
    },

    // Switch to correct network
    async switchNetwork() {
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: WEB3_CONFIG.NETWORK.CHAIN_ID }],
            });
        } catch (error) {
            // Network doesn't exist, add it
            if (error.code === 4902) {
                await this.addNetwork();
            } else {
                throw error;
            }
        }
    },

    // Add network to MetaMask
    async addNetwork() {
        try {
            await window.ethereum.request({
                method: 'wallet_addEthereumChain',
                params: [{
                    chainId: WEB3_CONFIG.NETWORK.CHAIN_ID,
                    chainName: WEB3_CONFIG.NETWORK.NETWORK_NAME,
                    rpcUrls: [WEB3_CONFIG.NETWORK.RPC_URL],
                    nativeCurrency: {
                        name: WEB3_CONFIG.NETWORK.CURRENCY_SYMBOL,
                        symbol: WEB3_CONFIG.NETWORK.CURRENCY_SYMBOL,
                        decimals: WEB3_CONFIG.NETWORK.CURRENCY_DECIMALS,
                    },
                }],
            });
        } catch (error) {
            console.error('Add network error:', error);
            throw error;
        }
    },

    // Get current account
    async getCurrentAccount() {
        if (walletState.isConnected && walletState.address) {
            return walletState.address;
        }

        try {
            const accounts = await window.ethereum.request({ 
                method: 'eth_accounts' 
            });
            return accounts[0] || null;
        } catch (error) {
            console.error('Get current account error:', error);
            return null;
        }
    },

    // Get ETH balance
    async getBalance(address) {
        try {
            const balance = await window.ethereum.request({
                method: 'eth_getBalance',
                params: [address, 'latest'],
            });

            // Convert from wei to ETH
            const balanceInEth = parseInt(balance, 16) / Math.pow(10, 18);
            return balanceInEth;
        } catch (error) {
            console.error('Get balance error:', error);
            throw error;
        }
    },

    // Sign message
    async signMessage(message) {
        try {
            const account = await this.getCurrentAccount();
            if (!account) {
                throw new Error('No account connected');
            }

            const signature = await window.ethereum.request({
                method: 'personal_sign',
                params: [message, account],
            });

            return signature;
        } catch (error) {
            console.error('Sign message error:', error);
            throw error;
        }
    },

    // Format address (0x1234...5678)
    formatAddress(address) {
        if (!address) return '';
        return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    },
};

// Initialize wallet on page load
if (typeof window !== 'undefined') {
    window.addEventListener('load', () => {
        WalletService.initialize();
    });
}
