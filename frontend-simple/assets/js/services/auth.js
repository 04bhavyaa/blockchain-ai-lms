import { API_ENDPOINTS } from '../config/api.js';
import { showAlert } from '../utils/utils.js';
import { ErrorHandler } from '../utils/errorHandler.js';

// Token Management
const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user_data';

export const AuthService = {
    // Register new user
    async register(userData) {
        try {
            const response = await fetch(API_ENDPOINTS.AUTH.REGISTER, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData),
            });

            const data = await response.json();

            if (!response.ok) {
                const error = new Error(data.message || 'Registration failed');
                error.response = data;
                throw error;
            }

            showAlert('success', data.message || 'Registration successful! Please verify your email.');
            return data;
        } catch (error) {
            await ErrorHandler.handleApiError(error);
            throw error;
        }
    },

    // Login user
    async login(email, password, rememberMe = false) {
        try {
            const response = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password, remember_me: rememberMe }),
            });

            const data = await response.json();

            if (!response.ok) {
                const error = new Error(data.message || 'Login failed');
                error.response = data;
                throw error;
            }

            // Store tokens and user data
            if (data.data) {
                localStorage.setItem(TOKEN_KEY, data.data.access);
                localStorage.setItem(REFRESH_TOKEN_KEY, data.data.refresh);
                localStorage.setItem(USER_KEY, JSON.stringify(data.data.user));
            }

            showAlert('success', 'Login successful!');
            return data.data;
        } catch (error) {
            await ErrorHandler.handleApiError(error);
            throw error;
        }
    },

    // Logout user
    async logout() {
        try {
            const token = this.getToken();
            if (token) {
                await fetch(API_ENDPOINTS.AUTH.LOGOUT, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local storage
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
            window.location.href = '/pages/auth/login.html';
        }
    },

    // Get current user profile
    async getProfile() {
        try {
            const token = this.getToken();
            const response = await fetch(API_ENDPOINTS.AUTH.PROFILE, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch profile');
            }

            // Update stored user data
            if (data.data) {
                localStorage.setItem(USER_KEY, JSON.stringify(data.data));
            }

            return data.data;
        } catch (error) {
            console.error('Get profile error:', error);
            throw error;
        }
    },

    // Update user profile
    async updateProfile(profileData) {
        try {
            const token = this.getToken();
            const response = await fetch(API_ENDPOINTS.AUTH.UPDATE_PROFILE, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(profileData),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to update profile');
            }

            // Update stored user data
            if (data.data) {
                localStorage.setItem(USER_KEY, JSON.stringify(data.data));
            }

            showAlert('success', 'Profile updated successfully!');
            return data.data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },

    // Change password
    async changePassword(oldPassword, newPassword, newPasswordConfirm) {
        try {
            const token = this.getToken();
            const response = await fetch(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    old_password: oldPassword,
                    new_password: newPassword,
                    new_password_confirm: newPasswordConfirm,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to change password');
            }

            showAlert('success', 'Password changed successfully!');
            return data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },

    // Resend email verification
    async resendVerification(email) {
        try {
            const response = await fetch(API_ENDPOINTS.AUTH.RESEND_VERIFICATION, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            const data = await response.json();

            if (!response.ok) {
                const error = new Error(data.message || 'Failed to resend verification email');
                error.response = data;
                throw error;
            }

            showAlert('success', data.message || 'Verification email sent!');
            return data;
        } catch (error) {
            if (!error.response) {
                showAlert('error', error.message);
            }
            throw error;
        }
    },

    // Connect wallet
    async connectWallet(walletAddress, signature, network = 'sepolia') {
        try {
            const token = this.getToken();
            const response = await fetch(API_ENDPOINTS.AUTH.CONNECT_WALLET, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    wallet_address: walletAddress,
                    signature: signature,
                    network: network,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to connect wallet');
            }

            // Update user data
            await this.getProfile();

            showAlert('success', 'Wallet connected successfully!');
            return data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },

    // Disconnect wallet
    async disconnectWallet() {
        try {
            const token = this.getToken();
            const response = await fetch(API_ENDPOINTS.AUTH.DISCONNECT_WALLET, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to disconnect wallet');
            }

            // Update user data
            await this.getProfile();

            showAlert('success', 'Wallet disconnected successfully!');
            return data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },

    // Get wallet balance
    async getWalletBalance() {
        try {
            const token = this.getToken();
            const response = await fetch(API_ENDPOINTS.AUTH.WALLET_BALANCE, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch wallet balance');
            }

            return data.data;
        } catch (error) {
            console.error('Get wallet balance error:', error);
            throw error;
        }
    },

    // Utility: Get stored token
    getToken() {
        return localStorage.getItem(TOKEN_KEY);
    },

    // Utility: Get stored user
    getUser() {
        const userData = localStorage.getItem(USER_KEY);
        return userData ? JSON.parse(userData) : null;
    },

    // Utility: Check if user is authenticated
    isAuthenticated() {
        return !!this.getToken();
    },

    // Utility: Require authentication (redirect if not logged in)
    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/pages/auth/login.html';
            return false;
        }
        return true;
    },
};
