// API Configuration
const API_CONFIG = {
  BASE_URL: 'http://localhost:8000/api/v1',
  TIMEOUT: 10000,
  HEADERS: {
    'Content-Type': 'application/json',
  }
};

// Store token in localStorage
const getToken = () => localStorage.getItem('access_token');
const setToken = (token) => localStorage.setItem('access_token', token);
const removeToken = () => localStorage.removeItem('access_token');

// Store user data - FIX: Handle undefined
const getUser = () => {
  try {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : { username: 'User', token_balance: 0 };
  } catch (e) {
    return { username: 'User', token_balance: 0 };
  }
};

const setUser = (user) => localStorage.setItem('user', JSON.stringify(user));
const removeUser = () => localStorage.removeItem('user');

// Check if authenticated
const isAuthenticated = () => !!getToken();

console.log('✅ Config loaded');