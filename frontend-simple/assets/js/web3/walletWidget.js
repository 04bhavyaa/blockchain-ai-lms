/**
 * Wallet Connection Widget
 * Similar to Wagmi's useAccount/useConnect/useDisconnect pattern
 * Can be embedded in any page for wallet connection UI
 */

import { WalletService } from '../web3/wallet.js';
import { showAlert } from '../utils/utils.js';

export class WalletWidget {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container #${containerId} not found`);
            return;
        }

        this.render();
        this.attachEventListeners();
        
        // Subscribe to wallet state changes
        this.unsubscribe = WalletService.subscribe((state) => {
            this.render();
        });
    }

    render() {
        const state = WalletService.getState();
        
        if (state.isConnected && state.address) {
            this.renderConnected(state);
        } else {
            this.renderDisconnected();
        }
    }

    renderConnected(state) {
        const networkName = WalletService.getNetworkName(state.chainId);
        
        this.container.innerHTML = `
            <div class="wallet-connected">
                <div class="wallet-info">
                    <div class="wallet-address" title="${state.address}">
                        <span class="wallet-icon">🔗</span>
                        <span class="address-text">${WalletService.formatAddress(state.address)}</span>
                    </div>
                    ${state.balance !== null ? `
                        <div class="wallet-balance">
                            <span>${state.balance.toFixed(4)} ETH</span>
                        </div>
                    ` : ''}
                    <div class="wallet-network">
                        <span class="network-indicator ${state.chainId === '0x7a69' ? 'network-correct' : 'network-wrong'}"></span>
                        <span class="network-name">${networkName}</span>
                    </div>
                </div>
                <button class="btn btn-outline btn-sm wallet-disconnect-btn" id="disconnectWalletBtn">
                    Disconnect
                </button>
            </div>
        `;
    }

    renderDisconnected() {
        this.container.innerHTML = `
            <div class="wallet-disconnected">
                <button class="btn btn-primary wallet-connect-btn" id="connectWalletBtn">
                    <span class="wallet-icon">🦊</span>
                    Connect Wallet
                </button>
            </div>
        `;
    }

    attachEventListeners() {
        // Use event delegation since buttons are re-rendered
        this.container.addEventListener('click', async (e) => {
            if (e.target.id === 'connectWalletBtn' || e.target.closest('#connectWalletBtn')) {
                await this.handleConnect();
            } else if (e.target.id === 'disconnectWalletBtn' || e.target.closest('#disconnectWalletBtn')) {
                await this.handleDisconnect();
            }
        });
    }

    async handleConnect() {
        try {
            await WalletService.connect();
        } catch (error) {
            console.error('Connection error:', error);
        }
    }

    async handleDisconnect() {
        try {
            await WalletService.disconnect();
        } catch (error) {
            console.error('Disconnect error:', error);
        }
    }

    destroy() {
        if (this.unsubscribe) {
            this.unsubscribe();
        }
    }
}

// Global function to initialize wallet widget on any page
window.initWalletWidget = function(containerId = 'walletWidget') {
    return new WalletWidget(containerId);
};

// Export for use in modules
export default WalletWidget;
