import { CoursesService } from '../services/courses.js';
import { showAlert, showLoading, hideLoading, getQueryParam, setQueryParam, debounce } from '../utils/utils.js';
import { ErrorHandler } from '../utils/errorHandler.js';

// State
let allCourses = [];
let currentPage = 1;
let filters = {
    search: '',
    category: '',
    level: '',
    price: '',
};

// Initialize courses page
async function initCoursesPage() {
    try {
        showLoading(document.getElementById('coursesGrid'));

        // Load categories
        await loadCategories();

        // Load courses
        await loadCourses();

        // Setup event listeners
        setupEventListeners();

        hideLoading();
    } catch (error) {
        console.error('Courses page initialization error:', error);
        await ErrorHandler.handleApiError(error, {
            customMessage: 'Failed to load courses page. Please refresh.'
        });
        hideLoading();
    }
}

// Load all courses
async function loadCourses() {
    try {
        const params = {
            page: currentPage,
            search: filters.search,
            category: filters.category,
            level: filters.level,
            price_range: filters.price,
        };

        const response = await CoursesService.getCourses(params);
        
        // Backend returns: { status: 'success', data: [...], pagination: {...} }
        allCourses = response.data || [];

        renderCourses(allCourses);
        renderPagination(response.pagination || response);
    } catch (error) {
        console.error('Load courses error:', error);
        await ErrorHandler.handleApiError(error, {
            customMessage: 'Failed to load courses. Please try again.'
        });
        // Show empty state with error message
        const container = document.getElementById('coursesGrid');
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">⚠️</div>
                <h3 style="color: var(--text-secondary); margin-bottom: 1rem;">Unable to Load Courses</h3>
                <p style="color: var(--text-muted); margin-bottom: 2rem;">
                    There was an error loading courses. Please try refreshing the page.
                </p>
                <button class="btn btn-primary" onclick="window.location.reload()">Refresh Page</button>
            </div>
        `;
    }
}

// Render courses
function renderCourses(courses) {
    const container = document.getElementById('coursesGrid');

    if (!courses || courses.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">📚</div>
                <h3 style="color: var(--text-secondary); margin-bottom: 1rem;">No Courses Found</h3>
                <p style="color: var(--text-muted); margin-bottom: 2rem;">
                    ${filters.search || filters.category || filters.level || filters.price 
                        ? 'Try adjusting your filters to see more courses.' 
                        : 'There are no courses available at the moment. Please check back later.'}
                </p>
                ${filters.search || filters.category || filters.level || filters.price 
                    ? '<button class="btn btn-primary" onclick="document.getElementById(\'clearFilters\').click()">Clear Filters</button>' 
                    : ''}
            </div>
        `;
        return;
    }

    container.innerHTML = courses.map(course => `
        <div class="card course-card">
            <img src="${course.thumbnail_url || '/assets/images/placeholder.svg'}" 
                 class="card-img-top" 
                 alt="${course.title}"
                 onclick="window.location.href='/pages/courses/course-detail.html?id=${course.id}'">
            <div class="card-body">
                <h3 class="card-title">${course.title}</h3>
                ${course.description ? `<p>${course.description.substring(0, 100)}...</p>` : ''}
                
                <div class="course-meta">
                    <span>📚 ${course.total_modules || 0} modules</span>
                    <span>⏱️ ${course.duration_hours || 0}h</span>
                    <span>👥 ${course.total_enrollments || 0} students</span>
                </div>

                <div class="mt-md">
                    <span class="badge badge-primary">${course.difficulty_level || 'beginner'}</span>
                    ${course.category_name ? `<span class="badge badge-secondary">${course.category_name}</span>` : ''}
                </div>

                <p class="course-price">${course.access_type === 'free' ? 'Free' : course.access_type === 'token' ? `${course.token_cost || 0} LMS Tokens` : `$${course.price_usd || 0}`}</p>
                
                <button class="btn btn-primary btn-block" onclick="viewCourse(${course.id})">
                    View Course
                </button>
            </div>
        </div>
    `).join('');
}

// Load categories
async function loadCategories() {
    try {
        const categories = await CoursesService.getCategories();
        const select = document.getElementById('categoryFilter');

        select.innerHTML = '<option value="">All Categories</option>' +
            categories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('');
    } catch (error) {
        console.error('Load categories error:', error);
    }
}

// Render pagination
function renderPagination(data) {
    const container = document.getElementById('pagination');
    
    // Handle both old format (next/previous) and new format (total_pages)
    const hasNext = data.next || (data.total_pages && data.current_page < data.total_pages);
    const hasPrevious = data.previous || (data.current_page && data.current_page > 1);
    
    if (!hasNext && !hasPrevious) {
        container.innerHTML = '';
        return;
    }

    const totalPages = data.total_pages || Math.ceil(data.count / (data.page_size || 12));
    const currentPageNum = data.current_page || currentPage;

    container.innerHTML = `
        <button class="btn btn-outline" 
                ${!hasPrevious ? 'disabled' : ''} 
                onclick="changePage(${currentPageNum - 1})">
            Previous
        </button>
        <span>Page ${currentPageNum} of ${totalPages}</span>
        <button class="btn btn-outline" 
                ${!hasNext ? 'disabled' : ''} 
                onclick="changePage(${currentPageNum + 1})">
            Next
        </button>
    `;
}

// Change page
window.changePage = function(page) {
    currentPage = page;
    loadCourses();
    window.scrollTo(0, 0);
};

// View course
window.viewCourse = function(courseId) {
    window.location.href = `/pages/courses/course-detail.html?id=${courseId}`;
};

// Setup event listeners
function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('searchInput');
    searchInput?.addEventListener('input', debounce((e) => {
        filters.search = e.target.value;
        currentPage = 1;
        loadCourses();
    }, 500));

    // Category filter
    document.getElementById('categoryFilter')?.addEventListener('change', (e) => {
        filters.category = e.target.value;
        currentPage = 1;
        loadCourses();
    });

    // Level filter
    document.getElementById('levelFilter')?.addEventListener('change', (e) => {
        filters.level = e.target.value;
        currentPage = 1;
        loadCourses();
    });

    // Price filter
    document.getElementById('priceFilter')?.addEventListener('change', (e) => {
        filters.price = e.target.value;
        currentPage = 1;
        loadCourses();
    });

    // Clear filters
    document.getElementById('clearFilters')?.addEventListener('click', () => {
        filters = { search: '', category: '', level: '', price: '' };
        currentPage = 1;
        
        document.getElementById('searchInput').value = '';
        document.getElementById('categoryFilter').value = '';
        document.getElementById('levelFilter').value = '';
        document.getElementById('priceFilter').value = '';
        
        loadCourses();
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initCoursesPage);
