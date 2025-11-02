// Authentication Logic

async function handleLogin(event) {
  event.preventDefault();
  showLoading(true);

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  try {
    const response = await api.login(email, password);
    
    setToken(response.access);
    setUser(response.user);
    
    showNotification('Login successful!', 'success');
    setTimeout(() => {
      window.location.href = '/pages/dashboard.html';
    }, 1000);
  } catch (error) {
    showNotification(error.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function handleRegister(event) {
  event.preventDefault();
  showLoading(true);

  const email = document.getElementById('email').value;
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirm_password').value;

  if (password !== confirmPassword) {
    showNotification('Passwords do not match', 'error');
    showLoading(false);
    return;
  }

  try {
    await api.register(email, username, password);
    showNotification('Registration successful! Please login.', 'success');
    setTimeout(() => {
      window.location.href = '/pages/login.html';
    }, 1000);
  } catch (error) {
    showNotification(error.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function handleLogout() {
  try {
    await api.logout();
  } catch (error) {
    console.error('Logout error:', error);
  }
  
  removeToken();
  removeUser();
  showNotification('Logged out', 'success');
  setTimeout(() => {
    window.location.href = '/pages/login.html';
  }, 1000);
}

function checkAuth() {
  if (!isAuthenticated()) {
    window.location.href = '/pages/login.html';
  }
}

console.log('✅ Auth loaded');