/**
 * Dashboard functionality
 */

// Check if user is admin and redirect to admin dashboard
async function checkAdminRedirect() {
    try {
        // First, refresh user profile to get latest admin status
        const profileResponse = await window.api.getProfile();
        if (profileResponse.status === 'success' && profileResponse.data) {
            const userData = profileResponse.data;
            window.utils.setUser(userData); // Update stored user data
            
            if (userData && (userData.is_staff || userData.is_superuser)) {
                // Check if we're already on admin dashboard
                if (!window.location.pathname.includes('admin-dashboard.html')) {
                    window.utils.redirectTo('admin-dashboard.html');
                    return true;
                }
            }
        } else {
            // Fallback to stored user data
            const user = window.utils.getUser();
            console.log('Stored user data:', user);
            if (user && (user.is_staff || user.is_superuser)) {
                if (!window.location.pathname.includes('admin-dashboard.html')) {
                    window.utils.redirectTo('admin-dashboard.html');
                    return true;
                }
            }
        }
    } catch (error) {
        console.error('Error checking admin status:', error);
        // Fallback to stored user data on error
        const user = window.utils.getUser();
        console.log('Error fallback - stored user data:', user);
        if (user && (user.is_staff || user.is_superuser)) {
            if (!window.location.pathname.includes('admin-dashboard.html')) {
                window.utils.redirectTo('admin-dashboard.html');
                return true;
            }
        }
    }
    return false;
}

// Load dashboard data
async function loadDashboard() {
    // Check if admin and redirect
    const isAdmin = await checkAdminRedirect();
    if (isAdmin) return;
    
    try {
        // Load user info
        const user = window.utils.getUser();
        if (user) {
            const greeting = document.getElementById('user-greeting');
            if (greeting) {
                greeting.textContent = `Hello, ${user.first_name || user.username || user.email}!`;
            }
        }

        // Load all sections independently to prevent one failure from breaking the dashboard
        // Use Promise.allSettled to ensure all attempts are made
        const loadPromises = [
            { name: 'stats', promise: loadDashboardStats().catch(e => { console.error('Stats failed:', e); throw e; }) },
            { name: 'myCourses', promise: loadMyCourses().catch(e => { console.error('My courses failed:', e); throw e; }) },
            { name: 'bookmarks', promise: loadBookmarkedCourses().catch(e => { console.error('Bookmarks failed:', e); throw e; }) },
            { name: 'recommendations', promise: loadRecommendations().catch(e => { console.error('Recommendations failed:', e); throw e; }) },
            { name: 'trending', promise: loadTrending().catch(e => { console.error('Trending failed:', e); throw e; }) }
        ];
        
        // Execute all loads in parallel
        const results = await Promise.allSettled(loadPromises.map(p => p.promise));
        
        // Log failures but don't block the UI
        const failedSections = [];
        results.forEach((result, index) => {
            if (result.status === 'rejected') {
                const sectionName = loadPromises[index].name;
                failedSections.push(sectionName);
            }
        });
        
        // Show general error only if all sections failed
        if (failedSections.length === loadPromises.length) {
            showAlert('error', 'Failed to load dashboard data. Please refresh the page.');
        } else if (failedSections.length > 0) {
            console.warn('Some dashboard sections failed to load:', failedSections);
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showAlert('error', 'Failed to load dashboard data. Please refresh the page.');
    }
}

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        const response = await window.api.getDashboard();
        console.log('[Dashboard] Stats response:', response);
        
        if (response.status === 'success' && response.data) {
            const stats = response.data;
            
            // Update stats
            const statCourses = document.getElementById('stat-courses');
            const statCompletion = document.getElementById('stat-completion');
            const statTokens = document.getElementById('stat-tokens');
            const statTime = document.getElementById('stat-time');

            if (statCourses) {
                const courses = stats.total_courses_enrolled || 0;
                statCourses.textContent = courses;
                console.log('[Dashboard] Total courses enrolled:', courses);
            }
            if (statCompletion) {
                const completion = parseFloat(stats.overall_completion) || 0;
                statCompletion.textContent = `${Math.round(completion)}%`;
                console.log('[Dashboard] Overall completion:', completion);
            }
            if (statTokens) {
                const tokens = parseInt(stats.total_tokens_earned) || 0;
                statTokens.textContent = tokens;
                console.log('[Dashboard] Total tokens earned:', tokens);
            }
            if (statTime) {
                const time = parseFloat(stats.total_time_hours) || 0;
                statTime.textContent = `${Math.round(time)}h`;
                console.log('[Dashboard] Total time:', time);
            }
        } else {
            console.error('[Dashboard] Invalid stats response format:', response);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        // Show user-friendly error message
        const statCourses = document.getElementById('stat-courses');
        if (statCourses) {
            statCourses.textContent = '0';
        }
    }
}

// Load my enrolled courses
async function loadMyCourses() {
    const container = document.getElementById('my-courses-container');
    if (!container) return;

    try {
        // Use the courses/my_courses endpoint which returns full course objects
        const response = await window.api.getMyCourses();
        
        // Handle different response formats
        const courses = response.data || response.results || (Array.isArray(response) ? response : []);
        
        if (courses.length > 0) {
            // Get progress data to show completion percentage
            try {
                const progressResponse = await window.api.getProgress();
                const progressData = progressResponse.data || [];
                
                // Create a map of course_id to progress
                const progressMap = {};
                progressData.forEach(progress => {
                    progressMap[progress.course_id] = progress;
                });
                
                // Render courses with progress
                container.innerHTML = courses.map(course => {
                    const progress = progressMap[course.id];
                    const completion = progress ? parseFloat(progress.completion_percentage) || 0 : 0;
                    return renderCourseCard(course, true, completion);
                }).join('');
            } catch (progressError) {
                // Fallback if progress fails - just show courses without progress
                console.warn('Failed to load progress, showing courses without progress:', progressError);
                container.innerHTML = courses.map(course => renderCourseCard(course, false)).join('');
            }
            
            // Add click handlers
            container.querySelectorAll('.course-card').forEach(card => {
                card.addEventListener('click', function() {
                    const courseId = this.dataset.courseId;
                    window.utils.redirectTo(`course-detail.html?id=${courseId}`);
                });
            });
        } else {
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <div class="empty-state-icon">📚</div>
                    <h3>No enrolled courses yet</h3>
                    <p>Start your learning journey by exploring our course catalog!</p>
                    <a href="courses.html" class="btn btn-primary mt-md">Browse Courses</a>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading my courses:', error);
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <p>Failed to load courses. Please try again later.</p>
                <p style="color: var(--text-muted); font-size: 0.9rem;">${error.message || 'Unknown error'}</p>
            </div>
        `;
    }
}

// Load recommended courses
async function loadRecommendations() {
    const container = document.getElementById('recommended-container');
    if (!container) return;

    try {
        const response = await window.api.getRecommendations();
        if (response.status === 'success' && response.data && response.data.length > 0) {
            container.innerHTML = response.data.slice(0, 6).map(course => renderCourseCard(course)).join('');
            attachCourseClickHandlers(container);
        } else {
            container.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;"><p>No recommendations available</p></div>';
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        container.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;"><p>Failed to load recommendations</p></div>';
    }
}

// Load bookmarked courses
async function loadBookmarkedCourses() {
    const container = document.getElementById('bookmarked-container');
    if (!container) return;

    try {
        const response = await window.api.getBookmarks();
        // Handle different response formats
        const bookmarks = response.data || response.results || (Array.isArray(response) ? response : []);
        
        if (bookmarks.length > 0) {
            // Bookmarks may have course nested or direct course data
            const courses = bookmarks.map(bookmark => {
                return bookmark.course || bookmark;
            });
            
            container.innerHTML = courses.map(course => renderCourseCard(course)).join('');
            attachCourseClickHandlers(container);
        } else {
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <p>No bookmarked courses yet. Bookmark courses to save them for later!</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading bookmarked courses:', error);
        container.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;"><p>Failed to load bookmarks</p></div>';
    }
}

// Load trending courses
async function loadTrending() {
    const container = document.getElementById('trending-container');
    if (!container) return;

    try {
        const response = await window.api.getTrending();
        if (response.status === 'success' && response.data && response.data.length > 0) {
            container.innerHTML = response.data.slice(0, 6).map(course => renderCourseCard(course)).join('');
            attachCourseClickHandlers(container);
        } else {
            // Fallback to get courses sorted by popularity
            const coursesResponse = await window.api.getCourses({ ordering: '-total_enrollments', page_size: 6 });
            if (coursesResponse.status === 'success' && coursesResponse.data) {
                container.innerHTML = coursesResponse.data.map(course => renderCourseCard(course)).join('');
                attachCourseClickHandlers(container);
            } else {
                container.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;"><p>No trending courses available</p></div>';
            }
        }
    } catch (error) {
        console.error('Error loading trending:', error);
        // Fallback to regular courses
        try {
            const coursesResponse = await window.api.getCourses({ page_size: 6 });
            if (coursesResponse.status === 'success' && coursesResponse.data) {
                container.innerHTML = coursesResponse.data.map(course => renderCourseCard(course)).join('');
                attachCourseClickHandlers(container);
            }
        } catch (fallbackError) {
            container.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;"><p>Failed to load trending courses</p></div>';
        }
    }
}

// Render course card
function renderCourseCard(course, showProgress = false, progressPercentage = 0) {
    const courseData = course.course || course;
    const progress = progressPercentage || parseFloat(course.completion_percentage) || 0;
    const thumbnail = courseData.thumbnail_url || 'https://via.placeholder.com/400x200?text=Course';
    // Handle both title and course_name (from recommendations API)
    const courseTitle = courseData.title || courseData.course_name || course.title || course.course_name || 'Untitled Course';
    const courseId = courseData.id || course.course_id || course.id;
    
    // Convert numeric fields - backend may return strings
    const rating = parseFloat(courseData.average_rating || course.average_rating) || 0;
    const enrollments = parseInt(courseData.total_enrollments || course.total_enrollments) || 0;
    const duration = parseInt(courseData.duration_hours || course.duration_hours) || 0;
    
    return `
        <div class="course-card" data-course-id="${courseId}">
            <img src="${thumbnail}" alt="${courseTitle}" class="course-thumbnail" onerror="this.src='https://via.placeholder.com/400x200?text=Course'">
            <div class="course-content">
                <h3 class="course-title">${courseTitle}</h3>
                <div class="course-meta">
                    <span>⭐ ${rating.toFixed(1)}/5</span>
                    <span>👥 ${enrollments}</span>
                    <span>📚 ${duration}h</span>
                </div>
                ${showProgress ? `
                    <div class="course-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                        <div class="progress-text">${Math.round(progress)}% Complete</div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Attach click handlers to course cards
function attachCourseClickHandlers(container) {
    container.querySelectorAll('.course-card').forEach(card => {
        card.addEventListener('click', function() {
            const courseId = this.dataset.courseId;
            window.utils.redirectTo(`course-detail.html?id=${courseId}`);
        });
    });
}

// Show alert - use centralized utility
function showAlert(type, message) {
    if (window.utils && window.utils.showAlert) {
        window.utils.showAlert(type, message);
    } else {
        console.error('Alert utility not available');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
});

// Make functions available globally
window.loadDashboard = loadDashboard;
window.showAlert = showAlert;

