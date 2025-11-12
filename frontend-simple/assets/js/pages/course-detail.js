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
    document.getElementById('courseLevel').textContent = course.difficulty_level || 'beginner';
    document.getElementById('courseDuration').textContent = `${course.duration_hours || 0} hours`;
    document.getElementById('totalLessons').textContent = course.total_modules || 0;
    document.getElementById('enrolledCount').textContent = course.total_enrollments || 0;
    
    // Fix: Use correct field names based on access_type
    let priceText = 'Free';
    if (course.access_type === 'token') {
        priceText = `${course.token_cost || 0} LMS Tokens`;
    } else if (course.access_type === 'paid') {
        priceText = `$${course.price_usd || 0}`;
    }
    document.getElementById('coursePrice').textContent = priceText;
    
    // Set course image
    const courseImage = document.getElementById('courseImage');
    if (courseImage) {
        courseImage.src = course.thumbnail_url || '/assets/images/placeholder.svg';
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

    // Update button text based on access type
    if (enrollBtn) {
        if (course.access_type === 'free') {
            enrollBtn.textContent = 'Enroll Free';
        } else if (course.access_type === 'token') {
            enrollBtn.textContent = `Enroll for ${course.token_cost || 0} Tokens`;
        } else {
            enrollBtn.textContent = `Enroll for $${course.price_usd || 0}`;
        }
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
        // Check course access type
        if (currentCourse.access_type === 'free') {
            // Free course - enroll directly
            await CoursesService.enrollCourse(courseId);
            showAlert('success', 'Successfully enrolled!');
            window.location.reload();
        } else if (currentCourse.access_type === 'token') {
            // Token-gated course - show blockchain payment modal
            showBlockchainPaymentModal(currentCourse);
        } else if (currentCourse.access_type === 'paid') {
            // Paid course - show USD payment modal
            showPaymentModal(currentCourse);
        }
    } catch (error) {
        console.error('Enrollment error:', error);
        
        // Handle "already enrolled" error gracefully
        if (error.message && error.message.includes('Already enrolled')) {
            showAlert('info', 'You are already enrolled in this course!');
            // Refresh to show correct button state
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showAlert('error', error.message || 'Failed to enroll');
        }
    }
}

// Show payment modal for USD payments
function showPaymentModal(course) {
    const user = AuthService.getUser();
    const userTokens = user.token_balance || 0;
    const requiredTokens = course.price_usd || 0;

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">Enroll in ${course.title}</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <p><strong>Price:</strong> $${requiredTokens}</p>
                <p class="alert alert-info">USD payment integration coming soon!</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" disabled>Pay with Card</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// Show blockchain payment modal for token-gated courses
function showBlockchainPaymentModal(course) {
    const user = AuthService.getUser();
    const requiredTokens = course.token_cost || 0;
    const walletAddress = user.wallet_address;

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">Unlock ${course.title}</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <p><strong>Required Tokens:</strong> ${requiredTokens} LMS</p>
                ${walletAddress ? 
                    `<p><strong>Wallet:</strong> ${walletAddress.substring(0, 6)}...${walletAddress.substring(38)}</p>
                     <p class="alert alert-info">Click below to connect MetaMask and pay with LMS tokens</p>` :
                    `<p class="alert alert-warning">Please connect your wallet first</p>`
                }
                <div id="paymentStatus"></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                ${walletAddress ?
                    `<button class="btn btn-primary" onclick="payWithBlockchain(${course.id}, ${requiredTokens})">Pay with Tokens</button>` :
                    `<button class="btn btn-primary" onclick="connectWallet()">Connect Wallet</button>`
                }
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// Connect wallet
window.connectWallet = async function() {
    try {
        // Import wallet service dynamically
        const { WalletService } = await import('../web3/wallet.js');
        const address = await WalletService.connect();
        
        if (address) {
            // Update user profile with wallet address
            await AuthService.updateProfile({ wallet_address: address });
            showAlert('success', 'Wallet connected successfully!');
            
            // Reload modal with wallet connected
            document.querySelector('.modal-overlay')?.remove();
            showBlockchainPaymentModal(currentCourse);
        }
    } catch (error) {
        console.error('Wallet connection error:', error);
        showAlert('error', 'Failed to connect wallet');
    }
};

// Pay with blockchain tokens
window.payWithBlockchain = async function(courseId, tokenAmount) {
    try {
        const statusDiv = document.getElementById('paymentStatus');
        statusDiv.innerHTML = '<p class="alert alert-info">🔄 Initiating blockchain payment...</p>';
        
        // Import blockchain services
        const { WalletService } = await import('../web3/wallet.js');
        const { ContractsService } = await import('../web3/contracts.js');
        
        // Get current account
        const account = await WalletService.getCurrentAccount();
        if (!account) {
            throw new Error('Please connect your wallet first');
        }
        
        statusDiv.innerHTML = '<p class="alert alert-info">🔄 Requesting token approval...</p>';
        
        // Request approval from backend
        const approvalData = await PaymentsService.requestBlockchainApproval(courseId);
        
        statusDiv.innerHTML = '<p class="alert alert-info">🔄 Waiting for MetaMask confirmation...</p>';
        
        // Execute token transfer via smart contract
        const receipt = await ContractsService.transferTokens(
            approvalData.spender_address,
            tokenAmount
        );
        
        statusDiv.innerHTML = '<p class="alert alert-info">🔄 Confirming payment on backend...</p>';
        
        // Confirm payment on backend
        await PaymentsService.confirmBlockchainPayment(courseId, receipt.transactionHash);
        
        statusDiv.innerHTML = '<p class="alert alert-success">✅ Payment successful!</p>';
        
        // Close modal and reload
        setTimeout(() => {
            document.querySelector('.modal-overlay')?.remove();
            showAlert('success', 'Successfully enrolled via blockchain!');
            window.location.reload();
        }, 2000);
        
    } catch (error) {
        console.error('Blockchain payment error:', error);
        const statusDiv = document.getElementById('paymentStatus');
        statusDiv.innerHTML = `<p class="alert alert-error">❌ ${error.message}</p>`;
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
