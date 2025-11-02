/**
 * API Client
 * Handles all HTTP requests to Django REST API
 */

// API Configuration - can be overridden by environment
const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8000/api/v1';

class APIClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    /**
     * Make HTTP request
     */
    async request(method, endpoint, data = null, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        console.log(`[API] [${requestId}] ${method} ${endpoint}`, data ? { dataKeys: Object.keys(data) } : '');
        
        const config = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };

        // Add authentication token if available
        const token = window.utils?.getToken();
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
            console.log(`[API] [${requestId}] Added auth token (length: ${token.length})`);
        } else {
            console.log(`[API] [${requestId}] No auth token`);
        }

        // Add body for POST/PUT/PATCH requests
        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            config.body = JSON.stringify(data);
            console.log(`[API] [${requestId}] Request body:`, data);
        }

        const startTime = Date.now();
        
        try {
            console.log(`[API] [${requestId}] Sending request to:`, url);
            const response = await fetch(url, config);
            const duration = Date.now() - startTime;
            
            console.log(`[API] [${requestId}] Response received:`, {
                status: response.status,
                statusText: response.statusText,
                duration: `${duration}ms`,
                contentType: response.headers.get('content-type')
            });
            
            let responseData = {};
            
            // Try to parse JSON response
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json().catch(() => ({}));
            } else {
                // If not JSON, get text
                const text = await response.text().catch(() => '');
                if (text) {
                    try {
                        responseData = JSON.parse(text);
                    } catch {
                        responseData = { message: text || 'Request failed' };
                    }
                }
            }

            if (!response.ok) {
                console.error(`[API] [${requestId}] Request failed:`, {
                    status: response.status,
                    statusText: response.statusText,
                    errorData: responseData
                });
                
                // Handle 401 Unauthorized - try token refresh
                if (response.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register') && !endpoint.includes('/auth/token')) {
                    // Don't refresh on auth endpoints
                    const refreshed = await this.refreshToken();
                    if (refreshed) {
                        // Retry the original request with new token
                        console.log(`[API] [${requestId}] Retrying request after token refresh`);
                        config.headers['Authorization'] = `Bearer ${window.utils.getToken()}`;
                        const retryResponse = await fetch(url, config);
                        if (retryResponse.ok) {
                            const retryData = await retryResponse.json().catch(() => ({}));
                            return retryData;
                        }
                    }
                }
                
                const error = new Error(responseData.message || responseData.detail || responseData.error || 'Request failed');
                error.status = response.status;
                error.data = responseData;
                
                // Handle 401 by redirecting to login
                if (response.status === 401) {
                    window.utils.removeToken();
                    if (!window.location.pathname.includes('login.html')) {
                        window.utils.redirectTo('login.html');
                    }
                }
                
                throw error;
            }

            console.log(`[API] [${requestId}] ✅ Success:`, {
                status: responseData.status,
                dataType: typeof responseData.data,
                isArray: Array.isArray(responseData.data),
                dataLength: Array.isArray(responseData.data) ? responseData.data.length : 'N/A',
                hasPagination: !!responseData.pagination
            });
            
            return responseData;
        } catch (error) {
            const duration = Date.now() - startTime;
            console.error(`[API] [${requestId}] ❌ Error after ${duration}ms:`, {
                error: error.message,
                status: error.status,
                data: error.data,
                type: error.name
            });
            
            if (error instanceof TypeError) {
                console.error(`[API] [${requestId}] Network error - likely CORS or connection issue`);
                throw new Error('Network error. Please check your connection.');
            }
            throw error;
        }
    }

    // ========================================
    // Authentication Endpoints
    // ========================================

    async register(email, username, password, passwordConfirm, firstName = '', lastName = '') {
        const response = await this.request('POST', '/auth/register/', {
            email,
            username,
            password,
            password_confirm: passwordConfirm,
            first_name: firstName,
            last_name: lastName
        });
        return response;
    }

    async login(email, password) {
        const response = await this.request('POST', '/auth/login/', {
            email,
            password
        });
        
        // Save tokens and user data
        // Response structure: { status: 'success', message: '...', data: { access, refresh, user, expires_in } }
        const responseData = response.data || response;
        
        if (responseData.access) {
            window.utils.setToken(responseData.access);
            if (responseData.refresh) {
                window.utils.setRefreshToken(responseData.refresh);
            }
        }
        
        if (responseData.user) {
            window.utils.setUser(responseData.user);
            // Log user data for debugging
            console.log('API login - User:', responseData.user);
            console.log('API login - is_staff:', responseData.user.is_staff, 'is_superuser:', responseData.user.is_superuser);
        }
        
        return response;
    }

    async logout() {
        try {
            await this.request('POST', '/auth/logout/');
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Always clear local storage
            window.utils.removeToken();
        }
    }

    async getProfile() {
        const response = await this.request('GET', '/auth/profile/');
        if (response.data) {
            window.utils.setUser(response.data);
        }
        return response;
    }

    async updateProfile(data) {
        const response = await this.request('PUT', '/auth/profile/update/', data);
        if (response.data) {
            window.utils.setUser(response.data);
        }
        return response;
    }

    async changePassword(oldPassword, newPassword) {
        return this.request('POST', '/auth/change-password/', {
            old_password: oldPassword,
            new_password: newPassword
        });
    }

    async connectWallet(data) {
        // Handle both old format (address, signature, network) and new format (object)
        if (typeof data === 'string') {
            // Old format - convert to new format
            return this.request('POST', '/auth/connect-wallet/', {
                wallet_address: data,
                signature: arguments[1] || '',
                network: arguments[2] || 'sepolia'
            });
        }
        return this.request('POST', '/auth/connect-wallet/', data);
    }

    async getWalletBalance() {
        return this.request('GET', '/auth/wallet-balance/');
    }

    async disconnectWallet() {
        return this.request('POST', '/auth/disconnect-wallet/');
    }

    async forgotPassword(email) {
        return this.request('POST', '/auth/forgot-password/', { email });
    }

    async resetPassword(token, newPassword) {
        return this.request('POST', '/auth/reset-password/', {
            token,
            new_password: newPassword
        });
    }

    async verifyEmail(token) {
        return this.request('POST', '/auth/verify-email/', { token });
    }

    async resendVerification(email) {
        return this.request('POST', '/auth/resend-verification/', { email });
    }

    // ========================================
    // Courses Endpoints
    // ========================================

    async getCourses(params = {}) {
        console.log('[API] getCourses() called with params:', params);
        
        // Remove pagination params - we want all courses for simplicity
        const { page, page_size, ...filters } = params;
        
        // Add a large page size to get all results (simplified for academic project)
        const queryParams = { ...filters, page_size: 1000 };
        const queryString = new URLSearchParams(queryParams).toString();
        const endpoint = `/courses/${queryString ? '?' + queryString : ''}`;
        
        try {
            const response = await this.request('GET', endpoint);
            
            // Handle different response formats and always return data array
            let courses = [];
            if (response.status === 'success') {
                if (Array.isArray(response.data)) {
                    courses = response.data;
                } else if (response.pagination?.data && Array.isArray(response.pagination.data)) {
                    courses = response.pagination.data;
                } else if (response.results && Array.isArray(response.results)) {
                    courses = response.results;
                }
            } else if (Array.isArray(response)) {
                courses = response;
            }
            
            // Return simplified format
            return {
                status: 'success',
                data: courses
            };
        } catch (error) {
            console.error('[API] getCourses() failed:', error);
            throw error;
        }
    }

    async getCourse(id) {
        return this.request('GET', `/courses/${id}/`);
    }

    async getLesson(id) {
        return this.request('GET', `/courses/lessons/${id}/`);
    }

    async getLessonsByModule(moduleId) {
        return this.request('GET', `/courses/lessons/by_module/?module_id=${moduleId}`);
    }

    async getLessonsByCourse(courseId) {
        return this.request('GET', `/courses/lessons/by_course/?course_id=${courseId}`);
    }

    async getQuiz(quizId) {
        return this.request('GET', `/courses/quizzes/${quizId}/`);
    }

    async enrollCourse(courseId) {
        return this.request('POST', `/courses/${courseId}/enroll/`);
    }

    async bookmarkCourse(courseId) {
        return this.request('POST', `/courses/${courseId}/bookmark/`);
    }

    async removeBookmark(courseId) {
        return this.request('DELETE', `/courses/${courseId}/unbookmark/`);
    }

    async getBookmarks() {
        return this.request('GET', `/courses/bookmarks/my_bookmarks/`);
    }

    // ========================================
    // Admin Endpoints
    // ========================================

    async getAdminStats() {
        return this.request('GET', '/admin/stats/overview/');
    }

    async getBlockchainStats() {
        return this.request('GET', '/blockchain/stats/stats/');
    }

    async getAdminUsers(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request('GET', `/admin/users/${queryString ? '?' + queryString : ''}`);
    }

    async getAdminUser(id) {
        return this.request('GET', `/admin/users/${id}/`);
    }

    async updateAdminUser(id, data) {
        return this.request('PUT', `/admin/users/${id}/`, data);
    }

    async banUser(id, reason = '') {
        return this.request('POST', `/admin/users/${id}/ban_user/`, { reason });
    }

    async unbanUser(id) {
        return this.request('POST', `/admin/users/${id}/unban_user/`);
    }

    async getAdminLogs(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request('GET', `/admin/logs/${queryString ? '?' + queryString : ''}`);
    }

    async getFraudCases() {
        return this.request('GET', '/admin/fraud/');
    }

    async updateFraudStatus(id, status, notes = '') {
        return this.request('PUT', `/admin/fraud/${id}/`, { status, notes });
    }

    async rateCourse(courseId, rating, review = '') {
        return this.request('POST', `/courses/ratings/`, {
            course: courseId,
            rating: rating,
            review: review
        });
    }

    async getEnrollments() {
        return this.request('GET', `/courses/enrollments/`);
    }

    async getMyCourses() {
        return this.request('GET', '/courses/my_courses/');
    }

    async getCategories() {
        return this.request('GET', `/courses/`);
    }

    // ========================================
    // Progress Endpoints
    // ========================================

    async getProgress() {
        return this.request('GET', '/progress/courses/my_courses/');
    }

    async getDashboard() {
        return this.request('GET', '/progress/courses/dashboard/');
    }

    async getLessonProgress(courseId) {
        return this.request('GET', `/progress/lessons/by_course/?course_id=${courseId}`);
    }

    async updateLessonProgress(lessonId, data) {
        return this.request('POST', '/progress/lessons/mark_progress/', {
            lesson_id: lessonId,
            ...data
        });
    }

    async submitQuiz(quizId, responses) {
        return this.request('POST', '/progress/quizzes/submit_quiz/', {
            quiz_id: quizId,
            responses: responses
        });
    }

    // ========================================
    // Recommendations Endpoints
    // ========================================

    async getRecommendations() {
        return this.request('GET', '/recommendations/for-me/');
    }

    async getTrending() {
        return this.request('GET', '/recommendations/trending/');
    }

    // ========================================
    // Wallet & Blockchain Endpoints
    // ========================================

    async connectWallet(walletAddress, signature, network = 'sepolia') {
        return this.request('POST', '/auth/connect-wallet/', {
            wallet_address: walletAddress,
            signature: signature,
            network: network
        });
    }

    async getWalletBalance() {
        return this.request('GET', '/auth/wallet-balance/');
    }

    async disconnectWallet() {
        return this.request('POST', '/auth/disconnect-wallet/');
    }

    async getCertificates() {
        return this.request('GET', '/blockchain/certificates/');
    }

    async getCertificate(id) {
        return this.request('GET', `/blockchain/certificates/${id}/`);
    }

    async verifyCertificate(id) {
        return this.request('POST', `/blockchain/certificates/${id}/verify_certificate/`);
    }


    async requestPaymentApproval(amount, courseId) {
        return this.request('POST', '/blockchain/payment/request-approval/', {
            tokens_amount: amount,
            course_id: courseId
        });
    }

    async confirmPayment(txHash, paymentId) {
        return this.request('POST', '/blockchain/payment/confirm-payment/', {
            transaction_hash: txHash,
            payment_id: paymentId
        });
    }

    async getPaymentHistory() {
        return this.request('GET', '/blockchain/payment/history/');
    }

    // ========================================
    // Chatbot Endpoints
    // ========================================

    async sendChatMessage(message, conversationId = null) {
        return this.request('POST', '/chatbot/send/', {
            message: message,
            conversation_id: conversationId
        });
    }

    async getConversations() {
        return this.request('GET', '/chatbot/conversations-list/');
    }

    async getConversation(id) {
        return this.request('GET', `/chatbot/conversations/${id}/`);
    }

    async createConversation(title = 'New Conversation') {
        return this.request('POST', '/chatbot/conversations/', {
            title: title
        });
    }

    async deleteConversation(id) {
        return this.request('DELETE', `/chatbot/conversations/${id}/`);
    }

    async submitChatFeedback(messageId, rating, comment = '') {
        return this.request('POST', '/chatbot/feedback/', {
            message: messageId,
            rating: rating,
            comment: comment
        });
    }

    // ========================================
    // Preferences & Recommendations
    // ========================================

    async getPreferences() {
        // Use the custom action endpoint
        return this.request('GET', '/recommendations/preferences/my_preferences/');
    }

    async updatePreferences(preferences) {
        // Use the custom action endpoint
        return this.request('POST', '/recommendations/preferences/update_preferences/', preferences);
    }

    // ========================================
    // Token Refresh
    // ========================================

    async refreshToken() {
        const refreshToken = window.utils?.getRefreshToken();
        if (!refreshToken) {
            console.log('[API] No refresh token available');
            return false;
        }

        try {
            console.log('[API] Attempting token refresh...');
            const response = await fetch(`${this.baseURL}/auth/token/refresh/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.access) {
                    window.utils.setToken(data.access);
                    console.log('[API] Token refreshed successfully');
                    return true;
                }
            }
            console.warn('[API] Token refresh failed');
            return false;
        } catch (error) {
            console.error('[API] Token refresh error:', error);
            return false;
        }
    }

    // ========================================
    // Error Handler
    // ========================================

    handleError(error) {
        if (error.status === 401) {
            // Unauthorized - redirect to login
            window.utils.removeToken();
            if (!window.location.pathname.includes('login.html')) {
                window.utils.redirectTo('login.html');
            }
        }
        return error;
    }
}

// Create global API client instance
window.api = new APIClient();

