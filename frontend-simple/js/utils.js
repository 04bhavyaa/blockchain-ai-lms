/**
 * Utility Functions
 * LocalStorage management, helpers, etc.
 */

// ========================================
// LocalStorage Helpers
// ========================================

function setToken(token) {
    localStorage.setItem('access_token', token);
}

function getToken() {
    return localStorage.getItem('access_token');
}

function removeToken() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
}

function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

function getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

function setRefreshToken(token) {
    localStorage.setItem('refresh_token', token);
}

function getRefreshToken() {
    return localStorage.getItem('refresh_token');
}

function isAuthenticated() {
    return !!getToken();
}

// ========================================
// URL Helpers
// ========================================

function redirectTo(path) {
    window.location.href = path;
}

function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// ========================================
// UI Helpers
// ========================================

function showError(element, message) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
        element.classList.add('form-error');
    }
}

function hideError(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.style.display = 'none';
        element.textContent = '';
    }
}

function showSuccess(element, message) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
        element.classList.remove('form-error');
        element.classList.add('form-success');
    }
}

function setLoading(button, isLoading) {
    if (typeof button === 'string') {
        button = document.querySelector(button);
    }
    if (button) {
        button.disabled = isLoading;
        if (isLoading) {
            button.classList.add('btn-loading');
        } else {
            button.classList.remove('btn-loading');
        }
    }
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ========================================
// Validation Helpers
// ========================================

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    // At least 8 characters
    return password && password.length >= 8;
}

function validateUsername(username) {
    // Alphanumeric, 3-30 chars
    const re = /^[a-zA-Z0-9_]{3,30}$/;
    return re.test(username);
}

// ========================================
// Export for use in other files
// ========================================

// ========================================
// Alert/Notification Helpers
// ========================================

function showAlert(type, message, duration = 5000) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alert.style.position = 'fixed';
    alert.style.top = '80px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.style.minWidth = '300px';
    alert.style.maxWidth = '400px';
    alert.style.padding = 'var(--spacing-md)';
    alert.style.borderRadius = '8px';
    alert.style.boxShadow = 'var(--shadow-lg)';
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    }, duration);
}

// Make functions available globally
window.utils = {
    setToken,
    getToken,
    removeToken,
    setUser,
    getUser,
    setRefreshToken,
    getRefreshToken,
    isAuthenticated,
    redirectTo,
    getQueryParam,
    showError,
    hideError,
    showSuccess,
    setLoading,
    formatDate,
    debounce,
    validateEmail,
    validatePassword,
    validateUsername,
    showAlert
};

