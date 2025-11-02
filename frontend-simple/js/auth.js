/**
 * Authentication Handlers
 * Login, Register, Logout functions
 */

/**
 * Handle login form submission
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const form = event.target;
    const email = form.email.value.trim();
    const password = form.password.value;
    const loginBtn = document.getElementById('login-btn');
    
    // Clear previous errors
    window.utils.hideError(document.getElementById('email-error'));
    window.utils.hideError(document.getElementById('password-error'));
    
    // Validate email
    if (!window.utils.validateEmail(email)) {
        window.utils.showError(document.getElementById('email-error'), 'Please enter a valid email address');
        return;
    }
    
    // Validate password
    if (!window.utils.validatePassword(password)) {
        window.utils.showError(document.getElementById('password-error'), 'Password must be at least 8 characters');
        return;
    }
    
    // Set loading state
    window.utils.setLoading(loginBtn, true);
    
    try {
        const response = await window.api.login(email, password);
        
        if (response.status === 'success') {
            // Show success message
            showAlert('success', response.message || 'Login successful! Redirecting...');
            
            // Check if user is admin and redirect accordingly
            const user = window.utils.getUser();
            console.log('Login handler - User:', user);
            console.log('Login handler - is_staff:', user?.is_staff, 'is_superuser:', user?.is_superuser);
            
            // Redirect after short delay
            setTimeout(() => {
                if (user && (user.is_staff || user.is_superuser)) {
                    window.utils.redirectTo('admin-dashboard.html');
                } else {
                    window.utils.redirectTo('dashboard.html');
                }
            }, 1000);
        }
    } catch (error) {
        // Handle error
        let errorMessage = error.message || error.data?.message || error.data?.detail || 'Login failed. Please try again.';
        
        // Show specific field errors if available
        if (error.data) {
            if (error.data.email) {
                const emailError = Array.isArray(error.data.email) ? error.data.email[0] : error.data.email;
                window.utils.showError(document.getElementById('email-error'), emailError);
                errorMessage = emailError;
            }
            if (error.data.password) {
                const passwordError = Array.isArray(error.data.password) ? error.data.password[0] : error.data.password;
                window.utils.showError(document.getElementById('password-error'), passwordError);
                if (!error.data.email) errorMessage = passwordError;
            }
            if (error.data.non_field_errors) {
                const generalError = Array.isArray(error.data.non_field_errors) ? error.data.non_field_errors[0] : error.data.non_field_errors;
                errorMessage = generalError;
            }
        }
        
        showAlert('error', errorMessage);
    } finally {
        window.utils.setLoading(loginBtn, false);
    }
}

/**
 * Handle register form submission
 */
async function handleRegister(event) {
    event.preventDefault();
    
    const form = event.target;
    const email = form.email.value.trim();
    const username = form.username.value.trim();
    const password = form.password.value;
    const confirmPassword = form['confirm-password'].value;
    const terms = form.terms.checked;
    const registerBtn = document.getElementById('register-btn');
    
    // Clear previous errors
    window.utils.hideError(document.getElementById('email-error'));
    window.utils.hideError(document.getElementById('username-error'));
    window.utils.hideError(document.getElementById('password-error'));
    window.utils.hideError(document.getElementById('confirm-password-error'));
    window.utils.hideError(document.getElementById('terms-error'));
    
    // Validate email
    if (!window.utils.validateEmail(email)) {
        window.utils.showError(document.getElementById('email-error'), 'Please enter a valid email address');
        return;
    }
    
    // Validate username
    if (!window.utils.validateUsername(username)) {
        window.utils.showError(document.getElementById('username-error'), 'Username must be 3-30 characters, alphanumeric and underscores only');
        return;
    }
    
    // Validate password
    if (!window.utils.validatePassword(password)) {
        window.utils.showError(document.getElementById('password-error'), 'Password must be at least 8 characters');
        return;
    }
    
    // Validate password match
    if (password !== confirmPassword) {
        window.utils.showError(document.getElementById('confirm-password-error'), 'Passwords do not match');
        return;
    }
    
    // Validate terms
    if (!terms) {
        window.utils.showError(document.getElementById('terms-error'), 'You must agree to the terms and conditions');
        return;
    }
    
    // Set loading state
    window.utils.setLoading(registerBtn, true);
    
    try {
        const response = await window.api.register(email, username, password, confirmPassword);
        
        if (response.status === 'success') {
            // Show success message
            showAlert('success', response.message || 'Registration successful! Please check your email to verify your account.');
            
            // Redirect to login page after delay
            setTimeout(() => {
                window.utils.redirectTo('login.html');
            }, 3000);
        }
    } catch (error) {
        // Handle error
        let errorMessage = error.message || error.data?.message || 'Registration failed. Please try again.';
        
        // Show specific field errors if available
        if (error.data) {
            // Handle validation errors from backend
            if (error.data.email) {
                const emailError = Array.isArray(error.data.email) ? error.data.email[0] : error.data.email;
                window.utils.showError(document.getElementById('email-error'), emailError);
                errorMessage = emailError;
            }
            if (error.data.username) {
                const usernameError = Array.isArray(error.data.username) ? error.data.username[0] : error.data.username;
                window.utils.showError(document.getElementById('username-error'), usernameError);
                if (!error.data.email) errorMessage = usernameError;
            }
            if (error.data.password) {
                const passwordError = Array.isArray(error.data.password) ? error.data.password[0] : error.data.password;
                window.utils.showError(document.getElementById('password-error'), passwordError);
                if (!error.data.email && !error.data.username) errorMessage = passwordError;
            }
            if (error.data.password_confirm) {
                const confirmError = Array.isArray(error.data.password_confirm) ? error.data.password_confirm[0] : error.data.password_confirm;
                window.utils.showError(document.getElementById('confirm-password-error'), confirmError);
                if (!error.data.email && !error.data.username && !error.data.password) errorMessage = confirmError;
            }
            if (error.data.non_field_errors) {
                const generalError = Array.isArray(error.data.non_field_errors) ? error.data.non_field_errors[0] : error.data.non_field_errors;
                showAlert('error', generalError);
                return; // Don't show another alert
            }
        }
        
        showAlert('error', errorMessage);
    } finally {
        window.utils.setLoading(registerBtn, false);
    }
}

/**
 * Handle logout
 */
async function handleLogout() {
    try {
        await window.api.logout();
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        // Always redirect to home
        window.utils.redirectTo('index.html');
    }
}

/**
 * Show alert message (uses utils.showAlert, but also shows in form container if available)
 */
function showAlert(type, message) {
    // Use centralized alert utility
    if (window.utils && window.utils.showAlert) {
        window.utils.showAlert(type, message);
    }
    
    // Also show in form container if it exists (for login/register pages)
    const container = document.getElementById('alert-container');
    if (container) {
        container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
        setTimeout(() => {
            container.innerHTML = '';
        }, 5000);
    }
}

// Make functions available globally
window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.handleLogout = handleLogout;
window.showAlert = showAlert;

