/**
 * Admin Dashboard functionality
 */

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadAdminDashboard();
});

// Load admin dashboard data
async function loadAdminDashboard() {
    try {
        await loadAdminStats();
        await loadRecentLogs();
    } catch (error) {
        console.error('Error loading admin dashboard:', error);
    }
}

// Load admin stats
async function loadAdminStats() {
    try {
        const response = await window.api.getAdminStats();
        console.log('[Admin Dashboard] Stats response:', response);
        
        // Handle response format - can be direct data or wrapped
        const stats = response.data || response;
        
        if (stats) {
            // Convert to numbers and ensure they display correctly
            document.getElementById('stat-users').textContent = parseInt(stats.total_users) || 0;
            document.getElementById('stat-active-users').textContent = parseInt(stats.active_users_today) || 0;
            document.getElementById('stat-courses').textContent = parseInt(stats.total_courses) || 0;
            document.getElementById('stat-enrollments').textContent = parseInt(stats.total_enrollments) || 0;
            document.getElementById('stat-pending-fraud').textContent = parseInt(stats.pending_fraud_cases) || 0;
            document.getElementById('stat-pending-certs').textContent = parseInt(stats.pending_certificates) || 0;
            
            console.log('[Admin Dashboard] Stats loaded:', stats);
        } else {
            console.error('[Admin Dashboard] No stats data in response');
            // Set defaults
            document.getElementById('stat-users').textContent = '0';
            document.getElementById('stat-active-users').textContent = '0';
            document.getElementById('stat-courses').textContent = '0';
            document.getElementById('stat-enrollments').textContent = '0';
            document.getElementById('stat-pending-fraud').textContent = '0';
            document.getElementById('stat-pending-certs').textContent = '0';
        }
    } catch (error) {
        console.error('[Admin Dashboard] Error loading admin stats:', error);
        // Set defaults on error but show user-friendly message
        document.getElementById('stat-users').textContent = '0';
        document.getElementById('stat-active-users').textContent = '0';
        document.getElementById('stat-courses').textContent = '0';
        document.getElementById('stat-enrollments').textContent = '0';
        document.getElementById('stat-pending-fraud').textContent = '0';
        document.getElementById('stat-pending-certs').textContent = '0';
        
        // Show error alert
        if (window.utils && window.utils.showAlert) {
            window.utils.showAlert('error', 'Failed to load dashboard statistics. Please refresh the page.');
        }
    }
}

// Load recent logs
async function loadRecentLogs() {
    const container = document.getElementById('recent-logs-container');
    if (!container) return;
    
    try {
        // Simplified - get all logs (no pagination)
        const response = await window.api.getAdminLogs({ page_size: 100 });
        // Handle different response formats
        const logs = response.data || response.results || (Array.isArray(response) ? response : []);
        
        if (logs.length > 0) {
            const logsHtml = `
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>Admin</th>
                            <th>Action</th>
                            <th>Target</th>
                            <th>Description</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${logs.map(log => `
                            <tr>
                                <td>${log.admin_user?.email || 'System'}</td>
                                <td>${log.action_type || '-'}</td>
                                <td>${log.target_type || '-'}</td>
                                <td>${log.description || '-'}</td>
                                <td>${new Date(log.created_at).toLocaleString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            container.innerHTML = '<h3 style="margin-bottom: var(--spacing-md);">Recent Activity</h3>' + logsHtml;
        } else {
            container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: var(--spacing-xl);">No recent activity</p>';
        }
    } catch (error) {
        console.error('Error loading logs:', error);
        container.innerHTML = '<p style="color: var(--text-error); text-align: center; padding: var(--spacing-xl);">Failed to load logs</p>';
    }
}

// Load users
async function loadUsers(search = '') {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: var(--spacing-xl);">Loading...</td></tr>';
    
    try {
        const params = search ? { search } : {};
        // Simplified - get all users (no pagination)
        const response = await window.api.getAdminUsers({ ...params, page_size: 1000 });
        // Handle different response formats
        const users = response.data || response.results || (Array.isArray(response) ? response : []);
        
        if (users.length > 0) {
            tbody.innerHTML = users.map(user => `
                <tr>
                    <td>${user.email || '-'}</td>
                    <td>${user.username || '-'}</td>
                    <td>
                        <span class="badge-status ${user.is_banned ? 'badge-banned' : 'badge-active'}">
                            ${user.is_banned ? 'Banned' : 'Active'}
                        </span>
                    </td>
                    <td>
                        <span class="badge-status ${user.is_verified ? 'badge-active' : 'badge-pending'}">
                            ${user.is_verified ? 'Verified' : 'Unverified'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-secondary" onclick="viewUser(${user.id})" style="padding: var(--spacing-xs) var(--spacing-sm); font-size: 0.85rem;">View</button>
                        ${user.is_banned 
                            ? `<button class="btn btn-secondary" onclick="unbanUser(${user.id})" style="padding: var(--spacing-xs) var(--spacing-sm); font-size: 0.85rem; margin-left: var(--spacing-xs);">Unban</button>`
                            : `<button class="btn btn-secondary" onclick="banUser(${user.id})" style="padding: var(--spacing-xs) var(--spacing-sm); font-size: 0.85rem; margin-left: var(--spacing-xs);">Ban</button>`
                        }
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: var(--spacing-xl);">No users found</td></tr>';
        }
    } catch (error) {
        console.error('Error loading users:', error);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: var(--spacing-xl); color: var(--text-error);">Failed to load users</td></tr>';
    }
}

// Load logs
async function loadLogs() {
    const tbody = document.getElementById('logs-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: var(--spacing-xl);">Loading...</td></tr>';
    
    try {
        // Simplified - get all logs (no pagination)
        const response = await window.api.getAdminLogs({ page_size: 1000 });
        // Handle different response formats
        const logs = response.data || response.results || (Array.isArray(response) ? response : []);
        
        if (logs.length > 0) {
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td>${log.admin_user?.email || 'System'}</td>
                    <td>${log.action_type || '-'}</td>
                    <td>${log.target_type || '-'} #${log.target_id || '-'}</td>
                    <td>${log.ip_address || '-'}</td>
                    <td>${new Date(log.created_at).toLocaleString()}</td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: var(--spacing-xl);">No logs found</td></tr>';
        }
    } catch (error) {
        console.error('Error loading logs:', error);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: var(--spacing-xl); color: var(--text-error);">Failed to load logs</td></tr>';
    }
}

// Load fraud cases
async function loadFraudCases() {
    const tbody = document.getElementById('fraud-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: var(--spacing-xl);">Loading...</td></tr>';
    
    try {
        const response = await window.api.getFraudCases();
        // Handle different response formats
        const frauds = response.data || response.results || (Array.isArray(response) ? response : []);
        
        if (frauds.length > 0) {
            tbody.innerHTML = frauds.map(fraud => `
                <tr>
                    <td>${fraud.user?.email || '-'}</td>
                    <td>${fraud.fraud_type || '-'}</td>
                    <td>${fraud.severity || '-'}</td>
                    <td>
                        <span class="badge-status ${fraud.status === 'resolved' ? 'badge-active' : fraud.status === 'pending' ? 'badge-pending' : 'badge-banned'}">
                            ${fraud.status || 'pending'}
                        </span>
                    </td>
                    <td>${new Date(fraud.created_at).toLocaleString()}</td>
                    <td>
                        <button class="btn btn-secondary" onclick="updateFraudStatus(${fraud.id}, 'resolved')" style="padding: var(--spacing-xs) var(--spacing-sm); font-size: 0.85rem;">Resolve</button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: var(--spacing-xl);">No fraud cases found</td></tr>';
        }
    } catch (error) {
        console.error('Error loading fraud cases:', error);
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: var(--spacing-xl); color: var(--text-error);">Failed to load fraud cases</td></tr>';
    }
}

// Switch admin tab
function switchAdminTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.admin-tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Remove active class
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`tab-${tabName}`);
    const selectedButton = event?.target || document.querySelector(`[onclick="switchAdminTab('${tabName}')"]`);
    
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Load tab data
    if (tabName === 'users') {
        loadUsers();
        // Setup search
        const searchInput = document.getElementById('user-search');
        if (searchInput) {
            const debouncedSearch = window.utils.debounce(() => {
                loadUsers(searchInput.value);
            }, 500);
            searchInput.oninput = debouncedSearch;
        }
    } else if (tabName === 'logs') {
        loadLogs();
    } else if (tabName === 'overview') {
        loadRecentLogs();
    } else if (tabName === 'fraud') {
        loadFraudCases();
    }
}

// Ban user
async function banUser(userId) {
    if (!confirm('Are you sure you want to ban this user?')) return;
    
    const reason = prompt('Enter ban reason:', 'Violation of terms');
    if (reason === null) return;
    
    try {
        await window.api.banUser(userId, reason);
        showAlert('success', 'User banned successfully');
        loadUsers();
    } catch (error) {
        showAlert('error', error.message || 'Failed to ban user');
    }
}

// Unban user
async function unbanUser(userId) {
    if (!confirm('Are you sure you want to unban this user?')) return;
    
    try {
        await window.api.unbanUser(userId);
        showAlert('success', 'User unbanned successfully');
        loadUsers();
    } catch (error) {
        showAlert('error', error.message || 'Failed to unban user');
    }
}

// Update fraud status
async function updateFraudStatus(fraudId, status) {
    try {
        await window.api.updateFraudStatus(fraudId, status);
        showAlert('success', 'Fraud case updated');
        loadFraudCases();
    } catch (error) {
        showAlert('error', error.message || 'Failed to update fraud case');
    }
}

// View user details
async function viewUser(userId) {
    try {
        const response = await window.api.getAdminUser(userId);
        if (response.status === 'success' && response.data) {
            const user = response.data;
            const details = `
                Email: ${user.email}
                Username: ${user.username}
                Verified: ${user.is_verified ? 'Yes' : 'No'}
                Banned: ${user.is_banned ? 'Yes' : 'No'}
                Token Balance: ${user.token_balance || 0}
            `;
            alert(details);
        }
    } catch (error) {
        showAlert('error', error.message || 'Failed to load user details');
    }
}

// Show alert - use centralized utility
function showAlert(type, message) {
    if (window.utils && window.utils.showAlert) {
        window.utils.showAlert(type, message);
    }
}

// Make functions available globally
window.switchAdminTab = switchAdminTab;
window.banUser = banUser;
window.unbanUser = unbanUser;
window.updateFraudStatus = updateFraudStatus;
window.viewUser = viewUser;

