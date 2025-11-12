// API Configuration - Matches your Django backend endpoints

const API_BASE_URL = 'http://127.0.0.1:8000/api';

const API_ENDPOINTS = {
    // Authentication Service
    AUTH: {
        REGISTER: `${API_BASE_URL}/auth/register/`,
        LOGIN: `${API_BASE_URL}/auth/login/`,
        LOGOUT: `${API_BASE_URL}/auth/logout/`,
        PROFILE: `${API_BASE_URL}/auth/profile/`,
        UPDATE_PROFILE: `${API_BASE_URL}/auth/profile/update/`,
        CHANGE_PASSWORD: `${API_BASE_URL}/auth/change-password/`,
        FORGOT_PASSWORD: `${API_BASE_URL}/auth/forgot-password/`,
        RESET_PASSWORD: `${API_BASE_URL}/auth/reset-password/`,
        VERIFY_EMAIL: `${API_BASE_URL}/auth/verify-email/`,
        RESEND_VERIFICATION: `${API_BASE_URL}/auth/resend-verification/`,
        CONNECT_WALLET: `${API_BASE_URL}/auth/connect-wallet/`,
        DISCONNECT_WALLET: `${API_BASE_URL}/auth/disconnect-wallet/`,
        WALLET_BALANCE: `${API_BASE_URL}/auth/wallet-balance/`,
    },

    // Courses Service
    COURSES: {
        LIST: `${API_BASE_URL}/courses/`,
        DETAIL: (id) => `${API_BASE_URL}/courses/${id}/`,
        ENROLL: (id) => `${API_BASE_URL}/courses/${id}/enroll/`,
        UNENROLL: (id) => `${API_BASE_URL}/courses/${id}/unenroll/`,
        LESSONS: (courseId) => `${API_BASE_URL}/courses/${courseId}/lessons/`,
        LESSON_DETAIL: (courseId, lessonId) => `${API_BASE_URL}/courses/${courseId}/lessons/${lessonId}/`,
        MARK_COMPLETE: (courseId, lessonId) => `${API_BASE_URL}/courses/${courseId}/lessons/${lessonId}/complete/`,
        MY_COURSES: `${API_BASE_URL}/courses/my-courses/`,
        CATEGORIES: `${API_BASE_URL}/courses/categories/`,
    },

    // AI Recommendations
    RECOMMENDATIONS: {
        GET: `${API_BASE_URL}/recommendations/`,
        FEEDBACK: `${API_BASE_URL}/recommendations/feedback/`,
    },

    // Chatbot Service
    CHATBOT: {
        MESSAGE: `${API_BASE_URL}/chatbot/message/`,
        HISTORY: `${API_BASE_URL}/chatbot/history/`,
        CLEAR: `${API_BASE_URL}/chatbot/clear/`,
    },

    // Payment Service
    PAYMENTS: {
        CREATE_INTENT: `${API_BASE_URL}/payments/create-payment-intent/`,
        CONFIRM: `${API_BASE_URL}/payments/confirm/`,
        HISTORY: `${API_BASE_URL}/payments/history/`,
        TOKEN_PAYMENT: `${API_BASE_URL}/payments/token-payment/`,
    },

    // Blockchain Service
    BLOCKCHAIN: {
        WALLET_INFO: `${API_BASE_URL}/blockchain/wallet-info/`,
        TOKEN_BALANCE: `${API_BASE_URL}/blockchain/token-balance/`,
        TRANSFER_TOKENS: `${API_BASE_URL}/blockchain/transfer-tokens/`,
        MINT_CERTIFICATE: (courseId) => `${API_BASE_URL}/blockchain/mint-certificate/${courseId}/`,
        MY_CERTIFICATES: `${API_BASE_URL}/blockchain/my-certificates/`,
        VERIFY_CERTIFICATE: (tokenId) => `${API_BASE_URL}/blockchain/verify-certificate/${tokenId}/`,
    },

    // Progress Service
    PROGRESS: {
        OVERVIEW: `${API_BASE_URL}/progress/overview/`,
        COURSE_PROGRESS: (courseId) => `${API_BASE_URL}/progress/course/${courseId}/`,
        ANALYTICS: `${API_BASE_URL}/progress/analytics/`,
    },

    // Admin Service
    ADMIN: {
        DASHBOARD: `${API_BASE_URL}/admin/dashboard/`,
        USERS: `${API_BASE_URL}/admin/users/`,
        USER_DETAIL: (id) => `${API_BASE_URL}/admin/users/${id}/`,
        BAN_USER: (id) => `${API_BASE_URL}/admin/users/${id}/ban/`,
        UNBAN_USER: (id) => `${API_BASE_URL}/admin/users/${id}/unban/`,
        COURSES: `${API_BASE_URL}/admin/courses/`,
        FRAUD_DETECTION: `${API_BASE_URL}/admin/fraud-detection/`,
    },
};

export { API_BASE_URL, API_ENDPOINTS };
