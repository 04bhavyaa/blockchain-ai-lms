/**
 * Enhanced Error Handler for Frontend
 * Provides consistent error handling and display across the application
 */

import { showAlert } from './utils.js';

/**
 * Error severity levels
 */
export const ErrorLevel = {
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'error',
    CRITICAL: 'danger'
};

/**
 * Error codes mapping to user-friendly messages
 */
const ERROR_MESSAGES = {
    // Authentication errors
    'AUTHENTICATION_ERROR': 'Invalid credentials. Please try again.',
    'NOT_AUTHENTICATED': 'Please log in to continue.',
    'UNAUTHORIZED': 'You are not authorized to perform this action.',
    'PERMISSION_DENIED': 'You do not have permission to access this resource.',
    'FORBIDDEN': 'Access to this resource is forbidden.',
    'INVALID_TOKEN': 'Your session has expired. Please log in again.',
    
    // Validation errors
    'VALIDATION_ERROR': 'Please check the form for errors.',
    'BAD_REQUEST': 'Invalid request. Please check your input.',
    
    // Resource errors
    'NOT_FOUND': 'The requested resource was not found.',
    'RESOURCE_NOT_FOUND': 'Resource not found.',
    'CONFLICT_ERROR': 'This resource already exists or conflicts with existing data.',
    
    // Service errors
    'INTERNAL_ERROR': 'An unexpected error occurred. Please try again later.',
    'INTERNAL_SERVER_ERROR': 'Server error. Our team has been notified.',
    'SERVICE_UNAVAILABLE': 'Service temporarily unavailable. Please try again later.',
    'BLOCKCHAIN_ERROR': 'Blockchain service is currently unavailable.',
    'PAYMENT_ERROR': 'Payment processing failed. Please try again.',
    
    // Rate limiting
    'RATE_LIMIT_ERROR': 'Too many requests. Please wait a moment and try again.',
    'THROTTLED': 'You are making requests too quickly. Please slow down.',
    'TOO_MANY_REQUESTS': 'Rate limit exceeded. Please try again later.',
    
    // Network errors
    'NETWORK_ERROR': 'Network error. Please check your connection.',
    'TIMEOUT_ERROR': 'Request timeout. Please try again.',
};

/**
 * Main error handler class
 */
export class ErrorHandler {
    /**
     * Handle API error response
     * @param {Error} error - Error object from fetch/axios
     * @param {Object} options - Additional options
     */
    static async handleApiError(error, options = {}) {
        const {
            showNotification = true,
            logToConsole = true,
            onError = null,
            customMessage = null,
        } = options;

        // Log to console if enabled
        if (logToConsole) {
            console.error('API Error:', error);
        }

        // Parse error details
        const errorDetails = await this.parseError(error);

        // Show notification if enabled
        if (showNotification) {
            this.displayError(errorDetails, customMessage);
        }

        // Call custom error handler if provided
        if (onError && typeof onError === 'function') {
            onError(errorDetails);
        }

        // Handle specific error codes
        this.handleSpecialCases(errorDetails);

        return errorDetails;
    }

    /**
     * Parse error from various sources
     * @param {Error} error - Error object
     * @returns {Object} Parsed error details
     */
    static async parseError(error) {
        const errorDetails = {
            level: ErrorLevel.ERROR,
            message: 'An error occurred',
            errorCode: 'UNKNOWN_ERROR',
            errors: {},
            timestamp: new Date().toISOString(),
            raw: error,
        };

        try {
            // Network errors
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorDetails.level = ErrorLevel.CRITICAL;
                errorDetails.message = 'Cannot connect to server. Please check your network connection.';
                errorDetails.errorCode = 'NETWORK_ERROR';
                return errorDetails;
            }

            // Timeout errors
            if (error.name === 'AbortError' || error.message.includes('timeout')) {
                errorDetails.level = ErrorLevel.WARNING;
                errorDetails.message = 'Request timeout. Please try again.';
                errorDetails.errorCode = 'TIMEOUT_ERROR';
                return errorDetails;
            }

            // Parse error response
            if (error.response) {
                const data = error.response;
                
                // Extract standardized error format from backend
                if (data.status === 'error') {
                    errorDetails.message = data.message || errorDetails.message;
                    errorDetails.errorCode = data.error_code || 'UNKNOWN_ERROR';
                    errorDetails.errors = data.errors || {};
                    errorDetails.path = data.path;
                    errorDetails.timestamp = data.timestamp;
                    
                    // Determine severity based on error code
                    errorDetails.level = this.getErrorLevel(data.error_code);
                } else {
                    // Fallback for non-standardized errors
                    errorDetails.message = data.message || data.detail || error.message;
                    errorDetails.errors = data.errors || {};
                }
            } else if (error.message) {
                errorDetails.message = error.message;
            }
        } catch (parseError) {
            console.error('Error parsing error:', parseError);
        }

        // Get user-friendly message
        if (ERROR_MESSAGES[errorDetails.errorCode]) {
            errorDetails.userMessage = ERROR_MESSAGES[errorDetails.errorCode];
        } else {
            errorDetails.userMessage = errorDetails.message;
        }

        return errorDetails;
    }

    /**
     * Display error to user
     * @param {Object} errorDetails - Parsed error details
     * @param {string} customMessage - Custom message to override default
     */
    static displayError(errorDetails, customMessage = null) {
        const message = customMessage || errorDetails.userMessage || errorDetails.message;
        
        // If there are field-specific errors, format them
        let displayMessage = message;
        if (errorDetails.errors && Object.keys(errorDetails.errors).length > 0) {
            displayMessage = this.formatFieldErrors(message, errorDetails.errors);
        }

        // Map error level to alert type
        const alertType = this.getAlertType(errorDetails.level);
        
        // Show alert
        showAlert(alertType, displayMessage, 7000);
    }

    /**
     * Format field-specific errors for display
     * @param {string} baseMessage - Base error message
     * @param {Object} errors - Field errors object
     * @returns {string} Formatted error message
     */
    static formatFieldErrors(baseMessage, errors) {
        let message = baseMessage;
        const fieldErrors = [];

        for (const [field, error] of Object.entries(errors)) {
            const errorText = Array.isArray(error) ? error.join(', ') : error;
            fieldErrors.push(`${field}: ${errorText}`);
        }

        if (fieldErrors.length > 0) {
            message += '\n' + fieldErrors.join('\n');
        }

        return message;
    }

    /**
     * Get error level based on error code
     * @param {string} errorCode - Error code
     * @returns {string} Error level
     */
    static getErrorLevel(errorCode) {
        const criticalErrors = ['INTERNAL_ERROR', 'NETWORK_ERROR', 'BLOCKCHAIN_ERROR'];
        const warningErrors = ['VALIDATION_ERROR', 'RATE_LIMIT_ERROR', 'NOT_FOUND'];

        if (criticalErrors.includes(errorCode)) {
            return ErrorLevel.CRITICAL;
        } else if (warningErrors.includes(errorCode)) {
            return ErrorLevel.WARNING;
        }
        return ErrorLevel.ERROR;
    }

    /**
     * Map error level to alert type
     * @param {string} level - Error level
     * @returns {string} Alert type for showAlert
     */
    static getAlertType(level) {
        const mapping = {
            [ErrorLevel.INFO]: 'info',
            [ErrorLevel.WARNING]: 'warning',
            [ErrorLevel.ERROR]: 'error',
            [ErrorLevel.CRITICAL]: 'danger'
        };
        return mapping[level] || 'error';
    }

    /**
     * Handle special error cases
     * @param {Object} errorDetails - Error details
     */
    static handleSpecialCases(errorDetails) {
        const { errorCode } = errorDetails;

        // Redirect to login for authentication errors
        if (['NOT_AUTHENTICATED', 'INVALID_TOKEN', 'AUTHENTICATION_ERROR'].includes(errorCode)) {
            setTimeout(() => {
                // Clear auth data
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user_data');
                
                // Redirect to login if not already there
                if (!window.location.pathname.includes('/pages/auth/login.html')) {
                    window.location.href = '/pages/auth/login.html?redirect=' + 
                        encodeURIComponent(window.location.pathname);
                }
            }, 2000);
        }

        // Log critical errors to external service (if configured)
        if (errorDetails.level === ErrorLevel.CRITICAL) {
            this.logToExternalService(errorDetails);
        }
    }

    /**
     * Log error to external monitoring service
     * @param {Object} errorDetails - Error details
     */
    static logToExternalService(errorDetails) {
        // Placeholder for external logging service (e.g., Sentry, LogRocket)
        // In production, you would send this to your monitoring service
        console.error('Critical Error Logged:', errorDetails);
        
        // Example: Sentry integration
        // if (window.Sentry) {
        //     window.Sentry.captureException(errorDetails.raw, {
        //         extra: errorDetails
        //     });
        // }
    }

    /**
     * Display field errors on form
     * @param {Object} errors - Field errors object
     * @param {HTMLFormElement} formElement - Form element
     */
    static displayFieldErrors(errors, formElement) {
        if (!errors || !formElement) return;

        // Clear existing error messages
        formElement.querySelectorAll('.error-message').forEach(el => el.remove());
        formElement.querySelectorAll('.error').forEach(el => el.classList.remove('error'));

        // Display new errors
        for (const [fieldName, errorMessage] of Object.entries(errors)) {
            const field = formElement.querySelector(`[name="${fieldName}"]`);
            if (field) {
                // Add error class to field
                field.classList.add('error');

                // Create and insert error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.style.color = 'var(--danger-color, #dc3545)';
                errorDiv.style.fontSize = '0.875rem';
                errorDiv.style.marginTop = '0.25rem';
                errorDiv.textContent = Array.isArray(errorMessage) 
                    ? errorMessage.join(', ') 
                    : errorMessage;

                // Insert after field
                field.parentNode.insertBefore(errorDiv, field.nextSibling);
            }
        }
    }

    /**
     * Clear field errors from form
     * @param {HTMLFormElement} formElement - Form element
     */
    static clearFieldErrors(formElement) {
        if (!formElement) return;

        formElement.querySelectorAll('.error-message').forEach(el => el.remove());
        formElement.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
    }
}

/**
 * Convenience function for handling API errors
 * @param {Error} error - Error object
 * @param {Object} options - Options
 */
export async function handleApiError(error, options = {}) {
    return await ErrorHandler.handleApiError(error, options);
}

/**
 * Create error-aware fetch wrapper
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @returns {Promise} Response data
 */
export async function fetchWithErrorHandling(url, options = {}) {
    try {
        const response = await fetch(url, options);
        const data = await response.json();

        if (!response.ok) {
            const error = new Error(data.message || 'Request failed');
            error.response = data;
            throw error;
        }

        return data;
    } catch (error) {
        await handleApiError(error);
        throw error;
    }
}

export default ErrorHandler;
