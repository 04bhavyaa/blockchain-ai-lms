/**
 * Course detail page functionality
 */

let courseId = null;
let courseData = null;
let isBookmarked = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    courseId = window.utils.getQueryParam('id');
    
    if (!courseId) {
        showAlert('error', 'No course ID provided');
        setTimeout(() => window.utils.redirectTo('courses.html'), 2000);
        return;
    }
    
    loadCourseDetail();
    checkBookmark();
});

// Load course details
async function loadCourseDetail() {
    try {
        const response = await window.api.getCourse(courseId);
        
        if (response.status === 'success' && response.data) {
            courseData = response.data;
            renderCourseDetail(courseData);
        } else {
            showAlert('error', 'Course not found');
            setTimeout(() => window.utils.redirectTo('courses.html'), 2000);
        }
    } catch (error) {
        console.error('Error loading course:', error);
        showAlert('error', error.message || 'Failed to load course details');
    }
}

// Render course details
function renderCourseDetail(course) {
    // Show content, hide loading
    document.getElementById('course-loading').style.display = 'none';
    document.getElementById('course-content').style.display = 'block';
    
    // Hero section
    document.getElementById('course-title').textContent = course.title || 'Untitled Course';
    document.getElementById('course-cover').src = course.cover_image_url || course.thumbnail_url || 'https://via.placeholder.com/800x400?text=Course';
    document.getElementById('course-description').textContent = course.description || 'No description available.';
    
    // Meta info - convert numeric fields
    document.getElementById('course-instructor').textContent = `By ${course.instructor_name || 'Instructor'}`;
    const rating = parseFloat(course.average_rating) || 0;
    document.getElementById('course-rating').textContent = rating.toFixed(1);
    document.getElementById('course-enrollments').textContent = parseInt(course.total_enrollments) || 0;
    document.getElementById('course-duration').textContent = parseInt(course.duration_hours) || 0;
    
    // Difficulty badge
    const difficultyBadge = document.getElementById('course-difficulty-badge');
    if (course.difficulty_level) {
        difficultyBadge.innerHTML = `<span class="badge badge-difficulty">${course.difficulty_level}</span>`;
    }
    
    // Sidebar info - convert numeric fields
    const priceEl = document.getElementById('course-price');
    if (course.access_type === 'free') {
        priceEl.textContent = 'Free';
        priceEl.classList.add('course-free-large');
    } else if (course.access_type === 'token') {
        const tokenCost = parseInt(course.token_cost) || 0;
        priceEl.textContent = `${tokenCost} Tokens`;
    } else {
        const priceUsd = parseFloat(course.price_usd) || 0;
        priceEl.textContent = `$${priceUsd.toFixed(2)}`;
    }
    
    document.getElementById('course-status').textContent = course.status || 'Published';
    document.getElementById('course-category').textContent = course.category?.name || 'Uncategorized';
    document.getElementById('course-modules-count').textContent = course.total_modules || 0;
    document.getElementById('course-access-type').textContent = course.access_type || 'N/A';
    
    // Enroll button
    const enrollBtn = document.getElementById('enroll-btn');
    if (course.is_enrolled) {
        enrollBtn.textContent = 'Access Course';
        enrollBtn.classList.remove('btn-primary');
        enrollBtn.classList.add('btn-secondary');
        enrollBtn.onclick = () => {
            // Navigate to course content page (you can create this later)
            window.utils.redirectTo(`course-content.html?courseId=${course.id}`);
        };
    } else {
        // Convert numeric fields for button text
        const tokenCost = parseInt(course.token_cost) || 0;
        const priceUsd = parseFloat(course.price_usd) || 0;
        
        enrollBtn.textContent = course.access_type === 'free' ? 'Enroll Now (Free)' : 
                                course.access_type === 'token' ? `Enroll Now (${tokenCost} Tokens)` :
                                `Enroll Now ($${priceUsd.toFixed(2)})`;
        enrollBtn.onclick = handleEnrollment;
    }
    
    // Ratings - convert numeric fields
    document.getElementById('average-rating').textContent = rating.toFixed(1);
    document.getElementById('total-ratings').textContent = parseInt(course.total_ratings) || 0;
    
    // Render modules
    renderModules(course.modules || []);
    
    // Bookmark button
    isBookmarked = course.is_bookmarked || false;
    updateBookmarkButton();
}

// Render modules
function renderModules(modules) {
    const container = document.getElementById('modules-list');
    if (!container) return;
    
    if (modules.length === 0) {
        container.innerHTML = '<li style="color: var(--text-secondary);">No modules available yet.</li>';
        return;
    }
    
    container.innerHTML = modules.map((module, index) => {
        const lessons = module.lessons || [];
        return `
            <li class="module-item">
                <div class="module-header" onclick="toggleModule(${index})">
                    <div>
                        <span class="module-title">Module ${index + 1}: ${module.title || 'Untitled Module'}</span>
                        <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 4px;">
                            ${lessons.length} lessons
                        </div>
                    </div>
                    <span id="module-toggle-${index}">▼</span>
                </div>
                <ul class="lesson-list" id="lesson-list-${index}">
                    ${lessons.map((lesson, lessonIndex) => `
                        <li class="lesson-item">
                            ${lessonIndex + 1}. ${lesson.title || 'Untitled Lesson'}
                            ${lesson.duration_minutes ? ` (${parseInt(lesson.duration_minutes) || 0} min)` : ''}
                        </li>
                    `).join('')}
                </ul>
            </li>
        `;
    }).join('');
}

// Toggle module expansion
function toggleModule(index) {
    const lessonList = document.getElementById(`lesson-list-${index}`);
    const toggle = document.getElementById(`module-toggle-${index}`);
    
    if (lessonList) {
        lessonList.classList.toggle('expanded');
        toggle.textContent = lessonList.classList.contains('expanded') ? '▲' : '▼';
    }
}

/**
 * Handle course enrollment with token payment
 */
/**
 * Handle course enrollment with token payment
 */
async function handleEnrollment() {
    const enrollBtn = document.getElementById('enroll-btn');
    if (!enrollBtn) return;
    
    window.utils.setLoading(enrollBtn, true);
    
    try {
        // Check if wallet is connected
        const account = await window.wallet.getAccount();
        if (!account) {
            const shouldConnect = confirm('You need to connect your MetaMask wallet to purchase this course. Connect now?');
            if (shouldConnect) {
                await window.wallet.connect();
                // Retry after connection
                return handleEnrollment();
            } else {
                throw new Error('Wallet connection required for token-gated courses');
            }
        }
        
        // Handle different access types
        if (courseData && courseData.access_type === 'token') {
            // TOKEN-GATED PURCHASE FLOW
            const requiredTokens = parseInt(courseData.token_cost) || 1;
            
            window.utils.showAlert('info', `This course costs ${requiredTokens} ${window.WEB3_CONFIG.CONTRACTS.TOKEN.symbol}. Processing payment...`);
            
            // Step 1: Check token balance
            const tokenBalance = await window.contracts.getTokenBalance(account);
            if (parseFloat(tokenBalance) < requiredTokens) {
                throw new Error(`Insufficient tokens. You need ${requiredTokens} ${window.WEB3_CONFIG.CONTRACTS.TOKEN.symbol} but only have ${parseFloat(tokenBalance).toFixed(2)}`);
            }
            
            // Step 2: Request approval from backend
            const approvalResp = await window.api.requestPaymentApproval(courseId, requiredTokens);
            if (!approvalResp || approvalResp.status !== 'success') {
                throw new Error('Failed to initiate payment. Please try again.');
            }
            
            const spenderAddress = approvalResp.data.spender_address || window.WEB3_CONFIG.TREASURY_ADDRESS;
            
            // Step 3: Check current allowance
            const currentAllowance = await window.contracts.checkAllowance(account, spenderAddress);
            if (parseFloat(currentAllowance) < requiredTokens) {
                // Need approval
                window.utils.showAlert('info', 'Please approve token spending in MetaMask...');
                
                const approveTx = await window.contracts.approveERC20(spenderAddress, requiredTokens);
                
                window.utils.showAlert('success', 'Token approval confirmed! Now confirming payment...');
            }
            
            // Step 4: Confirm payment with backend
            const confirmResp = await window.api.confirmPayment({
                course_id: courseId,
                transaction_hash: approveTx ? approveTx.hash : '0x' + Date.now().toString(16)
            });
            
            if (confirmResp && confirmResp.status === 'success') {
                window.utils.showAlert('success', 'Payment confirmed! You are now enrolled in the course.');
                
                // Update UI
                enrollBtn.textContent = 'Access Course';
                enrollBtn.classList.remove('btn-primary');
                enrollBtn.classList.add('btn-secondary');
                enrollBtn.onclick = () => window.utils.redirectTo(`course-content.html?courseId=${courseId}`);
                
                // Reload course data
                setTimeout(() => loadCourseDetail(), 1500);
            } else {
                throw new Error(confirmResp?.message || 'Failed to confirm payment');
            }
            
        } else if (courseData && courseData.access_type === 'free') {
            // FREE COURSE ENROLLMENT
            const response = await window.api.enrollCourse(courseId);
            
            if (response.status === 'success') {
                window.utils.showAlert('success', 'Successfully enrolled in free course!');
                
                enrollBtn.textContent = 'Access Course';
                enrollBtn.classList.remove('btn-primary');
                enrollBtn.classList.add('btn-secondary');
                enrollBtn.onclick = () => window.utils.redirectTo(`course-content.html?courseId=${courseId}`);
                
                setTimeout(() => loadCourseDetail(), 1000);
            }
            
        } else {
            // PAID COURSE (Stripe/other payment)
            window.utils.showAlert('info', 'Redirecting to payment...');
            // Implement Stripe Checkout here
        }
        
    } catch (error) {
        console.error('Enrollment error:', error);
        let errorMessage = error.message || 'Failed to enroll in course';
        
        if (error.code === 4001) {
            errorMessage = 'Transaction rejected by user';
        } else if (error.code === -32603) {
            errorMessage = 'Transaction failed. Please check your token balance and try again.';
        }
        
        window.utils.showAlert('error', errorMessage);
    } finally {
        window.utils.setLoading(enrollBtn, false);
    }
}



// Check bookmark status
async function checkBookmark() {
    try {
        const response = await window.api.getBookmarks();
        if (response.status === 'success' && response.data) {
            const bookmarks = Array.isArray(response.data) ? response.data : 
                            (response.pagination?.data || []);
            isBookmarked = bookmarks.some(b => b.course === courseId || b.course_id === courseId);
            updateBookmarkButton();
        }
    } catch (error) {
        console.error('Error checking bookmark:', error);
    }
}

// Update bookmark button
function updateBookmarkButton() {
    const bookmarkBtn = document.getElementById('bookmark-btn');
    const bookmarkText = document.getElementById('bookmark-text');
    
    if (bookmarkBtn && bookmarkText) {
        bookmarkText.textContent = isBookmarked ? '✓ Bookmarked' : 'Bookmark';
        bookmarkBtn.onclick = toggleBookmark;
    }
}

// Toggle bookmark
async function toggleBookmark() {
    const bookmarkBtn = document.getElementById('bookmark-btn');
    if (bookmarkBtn) {
        window.utils.setLoading(bookmarkBtn, true);
    }
    
    try {
        if (isBookmarked) {
            await window.api.removeBookmark(courseId);
            isBookmarked = false;
            updateBookmarkButton();
            showAlert('success', 'Bookmark removed');
        } else {
            await window.api.bookmarkCourse(courseId);
            isBookmarked = true;
            updateBookmarkButton();
            showAlert('success', 'Course bookmarked');
        }
    } catch (error) {
        showAlert('error', error.message || 'Failed to update bookmark');
    } finally {
        if (bookmarkBtn) {
            window.utils.setLoading(bookmarkBtn, false);
        }
    }
}

// Show alert - use centralized utility
function showAlert(type, message) {
    if (window.utils && window.utils.showAlert) {
        window.utils.showAlert(type, message);
    }
}

// Make functions available globally
window.toggleModule = toggleModule;

