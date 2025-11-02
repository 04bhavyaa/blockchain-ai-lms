/**
 * Courses listing functionality - Simplified for academic project
 */

let currentFilters = {
    search: '',
    category: '',
    difficulty_level: '',
    access_type: '',
    ordering: '-created_at'
};

// Initialize
document.addEventListener('DOMContentLoaded', async function() {
    console.log('[Courses] Page loaded, initializing...');
    setupFilters();
    // Load courses first, then extract categories from them (optimization)
    await loadCourses();
    loadCategories();
});

// Setup filter event listeners
function setupFilters() {
    const searchInput = document.getElementById('search-input');
    const categoryFilter = document.getElementById('category-filter');
    const difficultyFilter = document.getElementById('difficulty-filter');
    const accessFilter = document.getElementById('access-filter');
    const sortFilter = document.getElementById('sort-filter');

    // Debounced search
    if (searchInput) {
        const debouncedSearch = window.utils.debounce(function() {
            currentFilters.search = searchInput.value;
            loadCourses();
        }, 500);
        
        searchInput.addEventListener('input', debouncedSearch);
    }

    // Filter change handlers
    if (categoryFilter) {
        categoryFilter.addEventListener('change', function() {
            currentFilters.category = this.value;
            loadCourses();
        });
    }

    if (difficultyFilter) {
        difficultyFilter.addEventListener('change', function() {
            currentFilters.difficulty_level = this.value;
            loadCourses();
        });
    }

    if (accessFilter) {
        accessFilter.addEventListener('change', function() {
            currentFilters.access_type = this.value;
            loadCourses();
        });
    }

    if (sortFilter) {
        sortFilter.addEventListener('change', function() {
            currentFilters.ordering = this.value;
            loadCourses();
        });
    }
}

// Load courses - simplified, no pagination
async function loadCourses() {
    const container = document.getElementById('courses-container');
    if (!container) {
        console.error('[Courses] ERROR: courses-container element not found!');
        return;
    }

    // Show loading state
    container.innerHTML = `
        <div class="loading-spinner" style="grid-column: 1 / -1; display: flex; justify-content: center; padding: var(--spacing-xl);">
            <div class="loading"></div>
        </div>
    `;

    try {
        // Clean up filters - remove empty values
        const params = { ...currentFilters };
        Object.keys(params).forEach(key => {
            if (params[key] === '' || params[key] === null || params[key] === undefined) {
                delete params[key];
            }
        });

        // Get all courses (API handles large page size)
        const response = await window.api.getCourses(params);
        
        // Response is now standardized to { status: 'success', data: [...] }
        const courses = response.data || [];

        if (courses.length > 0) {
            // Cache courses for category loading
            window.coursesCache = courses;
            
            container.innerHTML = courses.map(course => renderCourseCard(course)).join('');
            
            // Attach click handlers
            container.querySelectorAll('.course-card').forEach(card => {
                card.addEventListener('click', function() {
                    const courseId = this.dataset.courseId;
                    window.utils.redirectTo(`course-detail.html?id=${courseId}`);
                });
            });
            
            console.log('[Courses] ✅ Loaded', courses.length, 'courses');
        } else {
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: var(--spacing-xl);">
                    <div class="empty-state-icon">🔍</div>
                    <h3>No courses found</h3>
                    <p>Try adjusting your filters or search terms.</p>
                </div>
            `;
        }
        
        // Remove pagination container (no longer needed)
        const paginationContainer = document.getElementById('pagination-container');
        if (paginationContainer) {
            paginationContainer.innerHTML = '';
        }
    } catch (error) {
        console.error('[Courses] ❌ ERROR loading courses:', error);
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: var(--spacing-xl);">
                <p style="color: var(--error);">Failed to load courses. Please try again later.</p>
                <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: var(--spacing-sm);">
                    ${error.message || 'Unknown error'}
                </p>
            </div>
        `;
    }
}

// Render course card
function renderCourseCard(course) {
    const thumbnail = course.thumbnail_url || 'https://via.placeholder.com/400x200?text=Course';
    
    // Convert numeric fields - backend may return strings for Decimal fields
    const rating = parseFloat(course.average_rating) || 0;
    const enrollments = parseInt(course.total_enrollments) || 0;
    const duration = parseInt(course.duration_hours) || 0;
    const tokenCost = parseInt(course.token_cost) || 0;
    const priceUsd = parseFloat(course.price_usd) || 0;
    
    const price = course.access_type === 'free' ? 'Free' : 
                  course.access_type === 'token' ? `${tokenCost} Tokens` :
                  `$${priceUsd.toFixed(2)}`;
    
    return `
        <div class="course-card" data-course-id="${course.id}">
            <img src="${thumbnail}" alt="${course.title || 'Course'}" class="course-thumbnail" 
                 onerror="this.src='https://via.placeholder.com/400x200?text=Course'">
            <div class="course-content">
                ${course.is_featured ? '<span class="badge badge-featured">Featured</span>' : ''}
                <h3 class="course-title">${course.title || 'Untitled Course'}</h3>
                <p class="course-description">${course.description || 'No description available.'}</p>
                <div class="course-meta">
                    <span>⭐ ${rating.toFixed(1)}/5</span>
                    <span>👥 ${enrollments}</span>
                    <span>📚 ${duration}h</span>
                    <span class="badge badge-difficulty">${course.difficulty_level || 'N/A'}</span>
                </div>
                <div class="course-footer">
                    <span class="course-price ${course.access_type === 'free' ? 'course-free' : ''}">
                        ${price}
                    </span>
                </div>
            </div>
        </div>
    `;
}

// Load categories for filter dropdown - extract from already loaded courses
// Cache for categories to avoid redundant API calls
let cachedCategories = null;

async function loadCategories() {
    const categoryFilter = document.getElementById('category-filter');
    if (!categoryFilter) {
        return;
    }
    
    // Return cached categories if available
    if (cachedCategories) {
        populateCategoryFilter(categoryFilter, cachedCategories);
        return;
    }
    
    try {
        // Reuse cached courses if available, otherwise fetch
        let courses = [];
        
        if (window.coursesCache && window.coursesCache.length > 0) {
            courses = window.coursesCache;
        } else {
            // Fetch courses once
            const response = await window.api.getCourses({ page_size: 1000 });
            courses = response.data || [];
            // Cache for reuse
            window.coursesCache = courses;
        }
        
        // Extract unique categories with their IDs for filtering
        const categoryMap = new Map(); // Map of category ID to category name
        
        courses.forEach(course => {
            // course.category is the ID, course.category_name is the name
            if (course.category && course.category_name) {
                categoryMap.set(course.category, course.category_name);
            } else if (course.category && typeof course.category === 'object' && course.category.name) {
                // Handle nested category object
                categoryMap.set(course.category.id, course.category.name);
            }
        });
        
        // Sort by name
        const categories = Array.from(categoryMap.entries()).sort((a, b) => a[1].localeCompare(b[1]));
        
        // Cache categories
        cachedCategories = categories;
        
        // Populate dropdown
        populateCategoryFilter(categoryFilter, categories);
        
        console.log('[Courses] ✅ Loaded', categories.length, 'categories');
    } catch (error) {
        console.error('[Courses] Error loading categories:', error);
        // Not critical - continue without categories
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
    }
}

// Helper function to populate category filter
function populateCategoryFilter(categoryFilter, categories) {
    categoryFilter.innerHTML = '<option value="">All Categories</option>';
    categories.forEach(([categoryId, categoryName]) => {
        const option = document.createElement('option');
        option.value = categoryId; // Use ID for filtering (backend expects category ID)
        option.textContent = categoryName;
        categoryFilter.appendChild(option);
    });
}
