import { AuthService } from '../services/auth.js';
import { API_ENDPOINTS } from '../config/api.js';
import { showAlert, showLoading, hideLoading, formatDate, formatCurrency } from '../utils/utils.js';

// Initialize admin dashboard
async function initAdminDashboard() {
    if (!AuthService.requireAuth()) return;

    const user = AuthService.getUser();
    
    // Check if user is admin
    if (!user.is_staff && !user.is_superuser) {
        showAlert('error', 'Access denied. Admin only.');
        window.location.href = '/pages/dashboard/dashboard.html';
        return;
    }

    try {
        showLoading(document.getElementById('adminContent'));

        await Promise.all([
            loadAdminStats(),
            loadRecentUsers(),
            loadRecentEnrollments(),
            loadFraudAlerts(),
        ]);

        hideLoading();
    } catch (error) {
        console.error('Admin dashboard initialization error:', error);
        showAlert('error', 'Failed to load admin dashboard');
        hideLoading();
    }
}

// Load admin statistics
async function loadAdminStats() {
    try {
        const token = AuthService.getToken();
        const response = await fetch(API_ENDPOINTS.ADMIN.DASHBOARD, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        const stats = data.data;

        document.getElementById('totalUsers').textContent = stats.total_users || 0;
        document.getElementById('totalCourses').textContent = stats.total_courses || 0;
        document.getElementById('totalEnrollments').textContent = stats.total_enrollments || 0;
        document.getElementById('totalRevenue').textContent = formatCurrency(stats.total_revenue || 0);
    } catch (error) {
        console.error('Load admin stats error:', error);
    }
}

// Load recent users
async function loadRecentUsers() {
    try {
        const token = AuthService.getToken();
        const response = await fetch(`${API_ENDPOINTS.ADMIN.USERS}?limit=10`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        const users = data.data.results || data.data;

        const container = document.getElementById('recentUsers');
        container.innerHTML = `
            <table class="table">
                <thead>
                    <tr>
                        <th>Email</th>
                        <th>Name</th>
                        <th>Joined</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${users.map(user => `
                        <tr>
                            <td>${user.email}</td>
                            <td>${user.first_name || ''} ${user.last_name || ''}</td>
                            <td>${formatDate(user.date_joined)}</td>
                            <td>
                                <span class="badge badge-${user.is_active ? 'success' : 'danger'}">
                                    ${user.is_active ? 'Active' : 'Banned'}
                                </span>
                            </td>
                            <td>
                                ${user.is_active ? 
                                    `<button class="btn btn-sm btn-danger" onclick="banUser(${user.id})">Ban</button>` :
                                    `<button class="btn btn-sm btn-success" onclick="unbanUser(${user.id})">Unban</button>`
                                }
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        console.error('Load recent users error:', error);
    }
}

// Load recent enrollments
async function loadRecentEnrollments() {
    try {
        const token = AuthService.getToken();
        const response = await fetch(`${API_ENDPOINTS.ADMIN.DASHBOARD}/enrollments`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        const enrollments = data.data || [];

        const container = document.getElementById('recentEnrollments');
        container.innerHTML = enrollments.slice(0, 10).map(enroll => `
            <div class="card mb-sm">
                <div class="card-body">
                    <p><strong>${enroll.user_email}</strong> enrolled in <strong>${enroll.course_title}</strong></p>
                    <small>${formatDate(enroll.enrolled_at)}</small>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Load recent enrollments error:', error);
    }
}

// Load fraud alerts
async function loadFraudAlerts() {
    try {
        const token = AuthService.getToken();
        const response = await fetch(API_ENDPOINTS.ADMIN.FRAUD_DETECTION, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        const alerts = data.data || [];

        const container = document.getElementById('fraudAlerts');
        
        if (alerts.length === 0) {
            container.innerHTML = '<p class="text-center">No fraud alerts</p>';
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="alert alert-warning">
                <strong>User ${alert.user_id}:</strong> ${alert.reason}
                <br><small>Risk Score: ${alert.risk_score}</small>
            </div>
        `).join('');
    } catch (error) {
        console.error('Load fraud alerts error:', error);
    }
}

// Ban user
window.banUser = async function(userId) {
    if (!confirm('Are you sure you want to ban this user?')) return;

    try {
        const token = AuthService.getToken();
        const response = await fetch(API_ENDPOINTS.ADMIN.BAN_USER(userId), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            showAlert('success', 'User banned successfully');
            await loadRecentUsers();
        }
    } catch (error) {
        console.error('Ban user error:', error);
        showAlert('error', 'Failed to ban user');
    }
};

// Unban user
window.unbanUser = async function(userId) {
    try {
        const token = AuthService.getToken();
        const response = await fetch(API_ENDPOINTS.ADMIN.UNBAN_USER(userId), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            showAlert('success', 'User unbanned successfully');
            await loadRecentUsers();
        }
    } catch (error) {
        console.error('Unban user error:', error);
        showAlert('error', 'Failed to unban user');
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', initAdminDashboard);
