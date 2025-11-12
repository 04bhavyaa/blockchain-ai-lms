import { WEB3_CONFIG } from '../config/web3_config.js';
import { showAlert } from '../utils/utils.js';

export const WalletService = {
    // Check if MetaMask is installed
    isMetaMaskInstalled() {
        return typeof window.ethereum !== 'undefined';
    },

    // Connect wallet
    async connect() {
        try {
            if (!this.isMetaMaskInstalled()) {
                showAlert('error', 'MetaMask not installed. Please install MetaMask to continue.');
                window.open('https://metamask.io/download/', '_blank');
                throw new Error('MetaMask not installed');
            }

            // Request account access
            const accounts = await window.ethereum.request({ 
                method: 'eth_requestAccounts' 
            });

            if (accounts.length === 0) {
                throw new Error('No accounts found');
            }

            const account = accounts[0];

            // Check network
            const chainId = await window.ethereum.request({ 
                method: 'eth_chainId' 
            });

            // Switch to correct network if needed
            if (chainId !== WEB3_CONFIG.NETWORK.CHAIN_ID) {
                await this.switchNetwork();
            }

            showAlert('success', `Wallet connected: ${this.formatAddress(account)}`);
            return account;
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
    disconnect() {
        // Note: MetaMask doesn't have a programmatic disconnect
        // We just clear local references
        showAlert('success', 'Wallet disconnected');
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
        try {
            if (!this.isMetaMaskInstalled()) {
                return null;
            }

            const accounts = await window.ethereum.request({ 
                method: 'eth_accounts' 
            });

            return accounts.length > 0 ? accounts[0] : null;
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

    // Listen to account changes
    onAccountsChanged(callback) {
        if (this.isMetaMaskInstalled()) {
            window.ethereum.on('accountsChanged', (accounts) => {
                callback(accounts[0] || null);
            });
        }
    },

    // Listen to chain changes
    onChainChanged(callback) {
        if (this.isMetaMaskInstalled()) {
            window.ethereum.on('chainChanged', (chainId) => {
                callback(chainId);
                // Reload the page on chain change (recommended by MetaMask)
                window.location.reload();
            });
        }
    },

    // Format address (0x1234...5678)
    formatAddress(address) {
        if (!address) return '';
        return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    },
};
