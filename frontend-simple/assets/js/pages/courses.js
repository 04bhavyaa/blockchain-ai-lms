import { CoursesService } from '../services/courses.js';
import { showAlert, showLoading, hideLoading, getQueryParam, setQueryParam, debounce } from '../utils/utils.js';

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
        showAlert('error', 'Failed to load courses');
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
        allCourses = response.data.results || response.data;

        renderCourses(allCourses);
        renderPagination(response.data);
    } catch (error) {
        console.error('Load courses error:', error);
        showAlert('error', 'Failed to load courses');
    }
}

// Render courses
function renderCourses(courses) {
    const container = document.getElementById('coursesGrid');

    if (courses.length === 0) {
        container.innerHTML = '<p class="text-center">No courses found</p>';
        return;
    }

    container.innerHTML = courses.map(course => `
        <div class="card course-card">
            <img src="${course.thumbnail || '/assets/images/placeholder.jpg'}" 
                 class="card-img-top" 
                 alt="${course.title}"
                 onclick="window.location.href='/pages/courses/course-detail.html?id=${course.id}'">
            <div class="card-body">
                <h3 class="card-title">${course.title}</h3>
                <p>${course.description.substring(0, 100)}...</p>
                
                <div class="course-meta">
                    <span>📚 ${course.total_lessons || 0} lessons</span>
                    <span>⏱️ ${course.duration || 'N/A'}</span>
                    <span>👥 ${course.enrolled_count || 0} students</span>
                </div>

                <div class="mt-md">
                    <span class="badge badge-primary">${course.level || 'Beginner'}</span>
                    ${course.category ? `<span class="badge badge-secondary">${course.category}</span>` : ''}
                </div>

                <p class="course-price">${course.price === 0 ? 'Free' : `${course.price} LMS Tokens`}</p>
                
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
    
    if (!data.next && !data.previous) {
        container.innerHTML = '';
        return;
    }

    const totalPages = Math.ceil(data.count / 12);

    container.innerHTML = `
        <button class="btn btn-outline" 
                ${!data.previous ? 'disabled' : ''} 
                onclick="changePage(${currentPage - 1})">
            Previous
        </button>
        <span>Page ${currentPage} of ${totalPages}</span>
        <button class="btn btn-outline" 
                ${!data.next ? 'disabled' : ''} 
                onclick="changePage(${currentPage + 1})">
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
