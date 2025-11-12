import { API_ENDPOINTS } from '../config/api.js';
import { AuthService } from './auth.js';
import { showAlert } from '../utils/utils.js';

export const PaymentsService = {
    // Create payment intent (Stripe)
    async createPaymentIntent(courseId, amount, currency = 'usd') {
        try {
            const token = AuthService.getToken();
            const response = await fetch(API_ENDPOINTS.PAYMENTS.CREATE_INTENT, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    course_id: courseId,
                    amount: amount,
                    currency: currency,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to create payment intent');
            }

            return data.data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },

    // Confirm payment
    async confirmPayment(paymentIntentId, paymentMethodId) {
        try {
            const token = AuthService.getToken();
            const response = await fetch(API_ENDPOINTS.PAYMENTS.CONFIRM, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    payment_intent_id: paymentIntentId,
                    payment_method_id: paymentMethodId,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Payment confirmation failed');
            }

            showAlert('success', 'Payment successful!');
            return data.data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },

    // Pay with LMS tokens
    async payWithTokens(courseId, tokenAmount) {
        try {
            const token = AuthService.getToken();
            const response = await fetch(API_ENDPOINTS.PAYMENTS.TOKEN_PAYMENT, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    course_id: courseId,
                    token_amount: tokenAmount,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Token payment failed');
            }

            showAlert('success', 'Payment successful with LMS tokens!');
            return data.data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },

    // Get payment history
    async getPaymentHistory(params = {}) {
        try {
            const token = AuthService.getToken();
            const queryString = new URLSearchParams(params).toString();
            const url = `${API_ENDPOINTS.PAYMENTS.HISTORY}${queryString ? '?' + queryString : ''}`;

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch payment history');
            }

            return data.data;
        } catch (error) {
            console.error('Get payment history error:', error);
            throw error;
        }
    },
};
