import { AuthService } from '../services/auth.js';
import { CoursesService } from '../services/courses.js';
import { showAlert, showLoading, hideLoading, getQueryParam, calculateProgress } from '../utils/utils.js';

let currentCourse = null;
let lessons = [];
let currentLessonIndex = 0;

// Initialize course content page
async function initCourseContent() {
    if (!AuthService.requireAuth()) return;

    const courseId = getQueryParam('id');
    
    if (!courseId) {
        showAlert('error', 'Course ID not found');
        window.location.href = '/pages/courses/courses.html';
        return;
    }

    try {
        showLoading(document.getElementById('lessonContent'));

        // Load course and lessons
        currentCourse = await CoursesService.getCourseDetail(courseId);
        lessons = await CoursesService.getCourseLessons(courseId);

        // Check if enrolled
        if (!currentCourse.is_enrolled) {
            showAlert('error', 'You are not enrolled in this course');
            window.location.href = `/pages/courses/course-detail.html?id=${courseId}`;
            return;
        }

        // Render sidebar
        renderSidebar();

        // Load first lesson or last accessed
        const lessonId = getQueryParam('lesson');
        if (lessonId) {
            const lessonIndex = lessons.findIndex(l => l.id == lessonId);
            if (lessonIndex !== -1) {
                currentLessonIndex = lessonIndex;
            }
        }

        await loadLesson(currentLessonIndex);

        hideLoading();
    } catch (error) {
        console.error('Course content initialization error:', error);
        showAlert('error', 'Failed to load course content');
        hideLoading();
    }
}

// Render sidebar with lessons
function renderSidebar() {
    const sidebar = document.getElementById('lessonsSidebar');
    const completedCount = lessons.filter(l => l.is_completed).length;
    const progress = calculateProgress(completedCount, lessons.length);

    sidebar.innerHTML = `
        <div class="course-sidebar">
            <h3>${currentCourse.title}</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
            <p>${progress}% Complete (${completedCount}/${lessons.length} lessons)</p>
            
            <div class="lessons-list mt-lg">
                ${lessons.map((lesson, index) => `
                    <div class="lesson-item ${index === currentLessonIndex ? 'active' : ''} ${lesson.is_completed ? 'completed' : ''}"
                         onclick="loadLessonByIndex(${index})">
                        <div class="lesson-number">${index + 1}</div>
                        <div class="lesson-info">
                            <h4>${lesson.title}</h4>
                            ${lesson.is_completed ? '<span class="badge badge-success">✓</span>' : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Load lesson by index
window.loadLessonByIndex = async function(index) {
    currentLessonIndex = index;
    await loadLesson(index);
    renderSidebar(); // Update active state
};

// Load lesson
async function loadLesson(index) {
    try {
        const lesson = lessons[index];
        const lessonDetail = await CoursesService.getLessonDetail(currentCourse.id, lesson.id);

        renderLesson(lessonDetail);
        updateNavigationButtons();
    } catch (error) {
        console.error('Load lesson error:', error);
        showAlert('error', 'Failed to load lesson');
    }
}

// Render lesson content
function renderLesson(lesson) {
    const container = document.getElementById('lessonContent');

    container.innerHTML = `
        <div class="lesson-header">
            <h2>${lesson.title}</h2>
            <span class="badge badge-${lesson.is_completed ? 'success' : 'warning'}">
                ${lesson.is_completed ? 'Completed' : 'In Progress'}
            </span>
        </div>

        <div class="lesson-body mt-lg">
            ${lesson.video_url ? `
                <div class="video-container">
                    <video controls>
                        <source src="${lesson.video_url}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>
            ` : ''}

            <div class="lesson-description mt-lg">
                <h3>Lesson Overview</h3>
                <p>${lesson.description || 'No description available'}</p>
            </div>

            <div class="lesson-content mt-lg">
                <h3>Content</h3>
                <div>${lesson.content || 'No content available'}</div>
            </div>

            ${lesson.resources && lesson.resources.length > 0 ? `
                <div class="lesson-resources mt-lg">
                    <h3>Resources</h3>
                    <ul>
                        ${lesson.resources.map(res => `
                            <li><a href="${res.url}" target="_blank">${res.title}</a></li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>

        <div class="lesson-footer mt-xl">
            ${!lesson.is_completed ? `
                <button class="btn btn-success" onclick="markAsComplete()">
                    Mark as Complete & Earn Tokens
                </button>
            ` : `
                <p class="alert alert-success">✓ You've completed this lesson!</p>
            `}
        </div>
    `;
}

// Update navigation buttons
function updateNavigationButtons() {
    const prevBtn = document.getElementById('prevLessonBtn');
    const nextBtn = document.getElementById('nextLessonBtn');

    if (prevBtn) {
        prevBtn.disabled = currentLessonIndex === 0;
        prevBtn.onclick = () => loadLessonByIndex(currentLessonIndex - 1);
    }

    if (nextBtn) {
        nextBtn.disabled = currentLessonIndex === lessons.length - 1;
        nextBtn.onclick = () => loadLessonByIndex(currentLessonIndex + 1);
    }
}

// Mark lesson as complete
window.markAsComplete = async function() {
    try {
        const lesson = lessons[currentLessonIndex];
        const result = await CoursesService.markLessonComplete(currentCourse.id, lesson.id);

        // Update lesson status
        lessons[currentLessonIndex].is_completed = true;

        showAlert('success', `Lesson completed! You earned ${result.tokens_earned || 0} tokens.`);

        // Refresh sidebar and lesson content
        renderSidebar();
        await loadLesson(currentLessonIndex);

        // Auto-advance to next lesson after 2 seconds
        if (currentLessonIndex < lessons.length - 1) {
            setTimeout(() => {
                loadLessonByIndex(currentLessonIndex + 1);
            }, 2000);
        } else {
            // Course completed
            showAlert('success', 'Congratulations! You completed the course! 🎉');
        }
    } catch (error) {
        console.error('Mark complete error:', error);
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', initCourseContent);
