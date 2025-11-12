import { API_ENDPOINTS } from '../config/api.js';
import { AuthService } from './auth.js';
import { showAlert } from '../utils/utils.js';

export const ChatbotService = {
    // Send message to chatbot
    async sendMessage(message, conversationId = null) {
        try {
            const token = AuthService.getToken();
            const response = await fetch(API_ENDPOINTS.CHATBOT.MESSAGE, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: conversationId,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to send message');
            }

            return data.data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },

    // Get chat history
    async getChatHistory(conversationId = null) {
        try {
            const token = AuthService.getToken();
            const url = conversationId 
                ? `${API_ENDPOINTS.CHATBOT.HISTORY}?conversation_id=${conversationId}`
                : API_ENDPOINTS.CHATBOT.HISTORY;

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch chat history');
            }

            return data.data;
        } catch (error) {
            console.error('Get chat history error:', error);
            throw error;
        }
    },

    // Clear chat history
    async clearHistory(conversationId = null) {
        try {
            const token = AuthService.getToken();
            const response = await fetch(API_ENDPOINTS.CHATBOT.CLEAR, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation_id: conversationId,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to clear chat history');
            }

            showAlert('success', 'Chat history cleared');
            return data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },
};
