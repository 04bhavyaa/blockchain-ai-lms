import { AuthService } from '../services/auth.js';
import { CoursesService } from '../services/courses.js';
import { PaymentsService } from '../services/payments.js';
import { showAlert, showLoading, hideLoading, getQueryParam } from '../utils/utils.js';

let currentCourse = null;

// Initialize course detail page
async function initCourseDetail() {
    const courseId = getQueryParam('id');
    
    if (!courseId) {
        showAlert('error', 'Course ID not found');
        window.location.href = '/pages/courses/courses.html';
        return;
    }

    try {
        showLoading(document.getElementById('courseContent'));

        // Load course details
        currentCourse = await CoursesService.getCourseDetail(courseId);
        
        // Render course details
        renderCourseDetail(currentCourse);

        // Load lessons if enrolled
        if (currentCourse.is_enrolled) {
            await loadCourseLessons(courseId);
        }

        hideLoading();
    } catch (error) {
        console.error('Course detail initialization error:', error);
        showAlert('error', 'Failed to load course details');
        hideLoading();
    }
}

// Render course details
function renderCourseDetail(course) {
    document.getElementById('courseTitle').textContent = course.title;
    document.getElementById('courseDescription').textContent = course.description;
    document.getElementById('courseInstructor').textContent = course.instructor_name || 'Unknown';
    document.getElementById('courseLevel').textContent = course.level || 'Beginner';
    document.getElementById('courseDuration').textContent = course.duration || 'N/A';
    document.getElementById('totalLessons').textContent = course.total_lessons || 0;
    document.getElementById('enrolledCount').textContent = course.enrolled_count || 0;
    document.getElementById('coursePrice').textContent = course.price === 0 ? 'Free' : `${course.price} LMS Tokens`;
    
    // Set course image
    const courseImage = document.getElementById('courseImage');
    if (courseImage) {
        courseImage.src = course.thumbnail || '/assets/images/placeholder.jpg';
        courseImage.alt = course.title;
    }

    // Show/hide enrollment button
    const enrollBtn = document.getElementById('enrollBtn');
    const startLearningBtn = document.getElementById('startLearningBtn');

    if (course.is_enrolled) {
        enrollBtn.classList.add('hidden');
        startLearningBtn.classList.remove('hidden');
    } else {
        enrollBtn.classList.remove('hidden');
        startLearningBtn.classList.add('hidden');
    }

    // Update button text based on price
    if (enrollBtn) {
        enrollBtn.textContent = course.price === 0 ? 'Enroll Free' : `Enroll for ${course.price} Tokens`;
    }
}

// Load course lessons
async function loadCourseLessons(courseId) {
    try {
        const lessons = await CoursesService.getCourseLessons(courseId);
        const container = document.getElementById('lessonsContainer');

        if (!container) return;

        container.innerHTML = `
            <h3>Course Content</h3>
            <div class="lessons-list">
                ${lessons.map((lesson, index) => `
                    <div class="lesson-item ${lesson.is_completed ? 'completed' : ''}">
                        <div class="lesson-number">${index + 1}</div>
                        <div class="lesson-info">
                            <h4>${lesson.title}</h4>
                            <p>${lesson.description || ''}</p>
                            <span class="lesson-duration">⏱️ ${lesson.duration || 'N/A'}</span>
                        </div>
                        ${lesson.is_completed ? '<span class="badge badge-success">✓ Completed</span>' : ''}
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Load lessons error:', error);
    }
}

// Enroll in course
async function enrollInCourse() {
    if (!AuthService.isAuthenticated()) {
        showAlert('error', 'Please login to enroll');
        window.location.href = '/pages/auth/login.html';
        return;
    }

    const courseId = getQueryParam('id');

    try {
        // Check if course is free
        if (currentCourse.price === 0) {
            await CoursesService.enrollCourse(courseId);
            showAlert('success', 'Successfully enrolled!');
            window.location.reload();
        } else {
            // Show payment modal
            showPaymentModal(currentCourse);
        }
    } catch (error) {
        console.error('Enrollment error:', error);
    }
}

// Show payment modal
function showPaymentModal(course) {
    const user = AuthService.getUser();
    const userTokens = user.token_balance || 0;

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">Enroll in ${course.title}</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <p><strong>Price:</strong> ${course.price} LMS Tokens</p>
                <p><strong>Your Balance:</strong> ${userTokens.toFixed(2)} LMS Tokens</p>
                
                ${userTokens >= course.price ? 
                    '<p class="alert alert-success">You have enough tokens!</p>' :
                    '<p class="alert alert-error">Insufficient tokens. Please purchase more tokens or complete lessons to earn more.</p>'
                }
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                ${userTokens >= course.price ?
                    `<button class="btn btn-primary" onclick="confirmTokenPayment(${course.id}, ${course.price})">Pay with Tokens</button>` :
                    '<button class="btn btn-primary" disabled>Insufficient Tokens</button>'
                }
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// Confirm token payment
window.confirmTokenPayment = async function(courseId, amount) {
    try {
        await PaymentsService.payWithTokens(courseId, amount);
        
        // Close modal
        document.querySelector('.modal-overlay')?.remove();
        
        // Enroll in course
        await CoursesService.enrollCourse(courseId);
        
        showAlert('success', 'Payment successful! You are now enrolled.');
        
        // Reload page
        setTimeout(() => window.location.reload(), 2000);
    } catch (error) {
        console.error('Payment error:', error);
    }
};

// Start learning
function startLearning() {
    const courseId = getQueryParam('id');
    window.location.href = `/pages/courses/course-content.html?id=${courseId}`;
}

// Event listeners
document.getElementById('enrollBtn')?.addEventListener('click', enrollInCourse);
document.getElementById('startLearningBtn')?.addEventListener('click', startLearning);

// Initialize on page load
document.addEventListener('DOMContentLoaded', initCourseDetail);
