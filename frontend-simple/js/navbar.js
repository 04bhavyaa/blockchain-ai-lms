// Navbar Logic

function loadNavbar() {
  const navbar = document.getElementById('navbar');
  const user = getUser();
  
  navbar.innerHTML = `
    <div class="navbar-container">
      <div class="navbar-brand">
        <span>🎓 Web3 LMS</span>
      </div>
      
      <div class="navbar-menu">
        <a href="/pages/dashboard.html">Dashboard</a>
        <a href="/pages/courses.html">Courses</a>
        <a href="/pages/profile.html">Profile</a>
      </div>

      <div class="navbar-user">
        <span class="token-balance">💰 ${user.token_balance || 0} Tokens</span>
        <div class="user-menu">
          <img src="https://via.placeholder.com/40" alt="Avatar" class="avatar">
          <div class="dropdown">
            <a href="/pages/profile.html">Profile</a>
            <button onclick="handleLogout()">Logout</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

window.addEventListener('load', () => {
  if (isAuthenticated()) {
    loadNavbar();
  }
});

console.log('✅ Navbar loaded');