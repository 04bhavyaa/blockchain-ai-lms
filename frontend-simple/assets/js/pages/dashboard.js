import { AuthService } from '../services/auth.js';
import { CoursesService } from '../services/courses.js';
import { showAlert, showLoading, hideLoading, formatDate, calculateProgress } from '../utils/utils.js';

// Initialize dashboard
async function initDashboard() {
    // Check authentication
    if (!AuthService.requireAuth()) return;

    try {
        // Get user data
        const user = AuthService.getUser();
        
        // Update welcome message
        document.getElementById('userName').textContent = user.first_name || user.email;

        // Show loading
        showLoading(document.getElementById('statsContainer'));
        showLoading(document.getElementById('coursesContainer'));

        // Fetch enrolled courses once and reuse
        const myCourses = await CoursesService.getMyCourses();

        // Load dashboard data
        await Promise.all([
            loadStats(user, myCourses),
            loadEnrolledCourses(myCourses),
            loadRecommendations(),
        ]);

        hideLoading();
    } catch (error) {
        console.error('Dashboard initialization error:', error);
        showAlert('error', 'Failed to load dashboard');
        hideLoading();
    }
}

// Load statistics
async function loadStats(user, myCourses) {
    try {
        // Calculate stats
        const enrolledCount = myCourses.length;
        const completedCount = myCourses.filter(c => c.progress === 100).length;
        const tokenBalance = user.token_balance || 0;
        const totalLessons = myCourses.reduce((acc, c) => acc + (c.total_lessons || 0), 0);

        // Update UI
        document.getElementById('enrolledCount').textContent = enrolledCount;
        document.getElementById('completedCount').textContent = completedCount;
        document.getElementById('tokenBalance').textContent = tokenBalance.toFixed(2);
        document.getElementById('totalLessons').textContent = totalLessons;
    } catch (error) {
        console.error('Load stats error:', error);
    }
}

// Load enrolled courses
async function loadEnrolledCourses(courses) {
    try {
        const container = document.getElementById('enrolledCourses');

        if (courses.length === 0) {
            container.innerHTML = '<p class="text-center">No enrolled courses yet. <a href="/pages/courses/courses.html">Browse courses</a></p>';
            return;
        }

        container.innerHTML = courses.map(course => `
            <div class="card course-card" onclick="window.location.href='/pages/courses/course-content.html?id=${course.id}'">
                <img src="${course.thumbnail_url || '/assets/images/placeholder.svg'}" class="card-img-top" alt="${course.title}">
                <div class="card-body">
                    <h3 class="card-title">${course.title}</h3>
                    ${course.description ? `<p>${course.description}</p>` : ''}
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${course.progress || 0}%"></div>
                    </div>
                    <p class="mt-sm">${course.progress || 0}% Complete</p>
                    <button class="btn btn-primary btn-block">Continue Learning</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Load enrolled courses error:', error);
    }
}

// Load AI recommendations
async function loadRecommendations() {
    try {
        const response = await fetch(API_ENDPOINTS.RECOMMENDATIONS.GET, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${AuthService.getToken()}`,
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        const recommendations = data.data || [];

        const container = document.getElementById('recommendedCourses');

        if (recommendations.length === 0) {
            container.innerHTML = '<p class="text-center">No recommendations available</p>';
            return;
        }

        container.innerHTML = recommendations.slice(0, 3).map(course => `
            <div class="card course-card" onclick="window.location.href='/pages/courses/course-detail.html?id=${course.id}'">
                <img src="${course.thumbnail_url || '/assets/images/placeholder.svg'}" class="card-img-top" alt="${course.title}">
                <div class="card-body">
                    <h3 class="card-title">${course.title}</h3>
                    <p>${course.description || ''}</p>
                    <span class="badge badge-primary">${course.difficulty_level || 'beginner'}</span>
                    <p class="course-price">${course.access_type === 'free' ? 'Free' : course.access_type === 'token' ? `${course.token_cost || 0} LMS Tokens` : `$${course.price_usd || 0}`}</p>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Load recommendations error:', error);
    }
}

// Logout handler
document.getElementById('logoutBtn')?.addEventListener('click', async () => {
    await AuthService.logout();
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDashboard);
