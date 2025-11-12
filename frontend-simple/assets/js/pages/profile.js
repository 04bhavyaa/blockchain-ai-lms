import { AuthService } from '../services/auth.js';
import { WalletService } from '../web3/wallet.js';
import { ContractsService } from '../web3/contracts.js';
import { showAlert, showLoading, hideLoading, formatDate } from '../utils/utils.js';

let currentUser = null;

// Initialize profile page
async function initProfile() {
    if (!AuthService.requireAuth()) return;

    try {
        showLoading(document.getElementById('profileContent'));

        // Load user profile
        currentUser = await AuthService.getProfile();

        // Render profile
        renderProfile(currentUser);

        // Setup event listeners
        setupEventListeners();

        // Load wallet info if connected
        if (currentUser.wallet_address) {
            await loadWalletInfo();
        }

        hideLoading();
    } catch (error) {
        console.error('Profile initialization error:', error);
        showAlert('error', 'Failed to load profile');
        hideLoading();
    }
}

// Render profile
function renderProfile(user) {
    document.getElementById('userEmail').textContent = user.email;
    document.getElementById('userFirstName').value = user.first_name || '';
    document.getElementById('userLastName').value = user.last_name || '';
    document.getElementById('userPhone').value = user.phone || '';
    document.getElementById('userBio').value = user.bio || '';

    // Display token balance
    document.getElementById('tokenBalance').textContent = user.token_balance?.toFixed(2) || '0.00';

    // Display wallet info
    if (user.wallet_address) {
        document.getElementById('walletAddress').textContent = WalletService.formatAddress(user.wallet_address);
        document.getElementById('walletConnected').classList.remove('hidden');
        document.getElementById('walletNotConnected').classList.add('hidden');
    } else {
        document.getElementById('walletConnected').classList.add('hidden');
        document.getElementById('walletNotConnected').classList.remove('hidden');
    }

    // Display member since
    if (user.date_joined) {
        document.getElementById('memberSince').textContent = formatDate(user.date_joined);
    }
}

// Load wallet info
async function loadWalletInfo() {
    try {
        const balance = await AuthService.getWalletBalance();
        
        document.getElementById('ethBalance').textContent = balance.eth_balance?.toFixed(4) || '0.00';
        document.getElementById('lmsTokenBalance').textContent = balance.lms_token_balance?.toFixed(2) || '0.00';
    } catch (error) {
        console.error('Load wallet info error:', error);
    }
}

// Update profile
async function updateProfile(e) {
    e.preventDefault();

    const formData = {
        first_name: document.getElementById('userFirstName').value,
        last_name: document.getElementById('userLastName').value,
        phone: document.getElementById('userPhone').value,
        bio: document.getElementById('userBio').value,
    };

    try {
        const updatedUser = await AuthService.updateProfile(formData);
        currentUser = updatedUser;
        renderProfile(updatedUser);
    } catch (error) {
        console.error('Update profile error:', error);
    }
}

// Change password
async function changePassword(e) {
    e.preventDefault();

    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (newPassword !== confirmPassword) {
        showAlert('error', 'New passwords do not match');
        return;
    }

    try {
        await AuthService.changePassword(oldPassword, newPassword, confirmPassword);
        
        // Clear form
        e.target.reset();
    } catch (error) {
        console.error('Change password error:', error);
    }
}

// Connect wallet
async function connectWallet() {
    try {
        // Connect to MetaMask
        const account = await WalletService.connect();

        // Sign message for verification
        const message = `Connect wallet to Blockchain LMS\nAddress: ${account}\nTimestamp: ${Date.now()}`;
        const signature = await WalletService.signMessage(message);

        // Send to backend
        await AuthService.connectWallet(account, signature, 'localhost');

        // Reload profile
        currentUser = await AuthService.getProfile();
        renderProfile(currentUser);
        await loadWalletInfo();

    } catch (error) {
        console.error('Connect wallet error:', error);
    }
}

// Disconnect wallet
async function disconnectWallet() {
    try {
        await AuthService.disconnectWallet();
        
        WalletService.disconnect();
        
        currentUser = await AuthService.getProfile();
        renderProfile(currentUser);
    } catch (error) {
        console.error('Disconnect wallet error:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('profileForm')?.addEventListener('submit', updateProfile);
    document.getElementById('passwordForm')?.addEventListener('submit', changePassword);
    document.getElementById('connectWalletBtn')?.addEventListener('click', connectWallet);
    document.getElementById('disconnectWalletBtn')?.addEventListener('click', disconnectWallet);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initProfile);
