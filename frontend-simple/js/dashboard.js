// Dashboard Logic

async function loadDashboard() {
  try {
    checkAuth();
    showLoading(true);
    
    const user = getUser();
    document.getElementById('user-name').textContent = user.first_name || user.username;
    document.getElementById('token-balance').textContent = user.token_balance || 0;

    const dashboard = await api.getDashboard();
    
    document.getElementById('total-courses').textContent = dashboard.total_courses_enrolled || 0;
    document.getElementById('completed-courses').textContent = dashboard.courses_completed || 0;
    document.getElementById('overall-progress').textContent = Math.round(dashboard.overall_completion || 0) + '%';

    // Load trending courses
    const trending = await api.getTrendingCourses();
    displayTrendingCourses(trending);

  } catch (error) {
    showNotification('Failed to load dashboard: ' + error.message, 'error');
  } finally {
    showLoading(false);
  }
}

function displayTrendingCourses(courses) {
  const container = document.getElementById('trending-courses');
  container.innerHTML = courses.slice(0, 3).map(course => `
    <div class="course-card">
      <img src="${course.thumbnail_url || 'https://via.placeholder.com/300x200'}" alt="${course.title}">
      <h3>${course.title}</h3>
      <p>${course.instructor_name}</p>
      <div class="course-stats">
        <span>⭐ ${course.average_rating || 'N/A'}/5</span>
        <span>👥 ${course.total_enrollments}</span>
      </div>
      <button onclick="navigateTo('course-detail?id=${course.id}')">View Course</button>
    </div>
  `).join('');
}

window.addEventListener('load', loadDashboard);
console.log('✅ Dashboard loaded');