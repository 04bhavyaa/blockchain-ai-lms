/**
 * Course Content Page - View lessons, take quizzes, track progress
 */

let courseId = null;
let courseData = null;
let modulesData = [];
let currentLessonId = null;
let currentLessonData = null;
let userProgress = {};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    courseId = window.utils.getQueryParam('courseId');
    
    if (!courseId) {
        showAlert('error', 'No course ID provided');
        setTimeout(() => window.utils.redirectTo('courses.html'), 2000);
        return;
    }
    
    loadCourseContent();
});

// Load course content
async function loadCourseContent() {
    try {
        // Load course details
        const courseResponse = await window.api.getCourse(courseId);
        if (courseResponse.status === 'success' && courseResponse.data) {
            courseData = courseResponse.data;
            document.getElementById('course-title').textContent = courseData.title || 'Course';
            
            // Load modules and lessons - prioritize from course data if available
            if (courseData.modules && courseData.modules.length > 0) {
                // Use modules from course detail (has full structure with lessons)
                modulesData = courseData.modules;
                console.log('[Course Content] Loaded modules from course data:', modulesData.length);
                renderModulesNav();
                
                // Load first lesson if available
                if (modulesData.length > 0 && modulesData[0].lessons && modulesData[0].lessons.length > 0) {
                    loadLesson(modulesData[0].lessons[0].id);
                }
            } else {
                // Fallback: Fetch lessons separately using by_course endpoint
                await loadAllLessons();
            }
        } else {
            showAlert('error', 'Course not found');
            return;
        }
        
        // Load user progress
        await loadProgress();
    } catch (error) {
        console.error('Error loading course content:', error);
        showAlert('error', error.message || 'Failed to load course content');
    }
}

// Load all lessons for the course
async function loadAllLessons() {
    try {
        const response = await window.api.getLessonsByCourse(courseId);
        if (response.status === 'success' && response.data) {
            // Response structure: [{module_id, module_title, module_order, lessons: [...]}]
            // OR: array of lesson objects with module_id, module_title fields
            
            if (response.data.length > 0 && response.data[0].lessons && Array.isArray(response.data[0].lessons)) {
                // Structure: [{module_id, module_title, module_order, lessons: [...]}]
                modulesData = response.data.map(moduleData => ({
                    id: moduleData.module_id,
                    title: moduleData.module_title,
                    module_title: moduleData.module_title, // Keep both for compatibility
                    order: moduleData.module_order,
                    module_order: moduleData.module_order,
                    lessons: moduleData.lessons || []
                })).sort((a, b) => (a.order || a.module_order || 0) - (b.order || b.module_order || 0));
            } else {
                // Structure: flat array of lessons with module info
                const lessonsByModule = {};
                response.data.forEach(lesson => {
                    const moduleId = lesson.module_id;
                    if (!lessonsByModule[moduleId]) {
                        lessonsByModule[moduleId] = {
                            id: moduleId,
                            title: lesson.module_title,
                            module_title: lesson.module_title,
                            order: lesson.module_order || 0,
                            module_order: lesson.module_order || 0,
                            lessons: []
                        };
                    }
                    lessonsByModule[moduleId].lessons.push(lesson);
                });
                
                modulesData = Object.values(lessonsByModule).sort((a, b) => (a.order || 0) - (b.order || 0));
            }
            
            console.log('[Course Content] Loaded modules from by_course endpoint:', modulesData.length);
            renderModulesNav();
            
            // Load first lesson
            if (modulesData.length > 0 && modulesData[0].lessons && modulesData[0].lessons.length > 0) {
                loadLesson(modulesData[0].lessons[0].id);
            }
        }
    } catch (error) {
        console.error('Error loading lessons:', error);
        showAlert('error', 'Failed to load course modules and lessons');
    }
}

// Load lessons using by_module endpoint
async function loadLessons() {
    try {
        // Try to get lessons from course modules
        if (courseData.modules) {
            for (const module of courseData.modules) {
                const response = await window.api.getLessonsByModule(module.id);
                if (response.status === 'success' && response.data) {
                    module.lessons = response.data;
                }
            }
            modulesData = courseData.modules;
            renderModulesNav();
        }
    } catch (error) {
        console.error('Error loading lessons:', error);
    }
}

// Render modules navigation
function renderModulesNav() {
    const container = document.getElementById('modules-nav');
    if (!container) return;
    
    let html = '';
    modulesData.forEach((module, moduleIndex) => {
        const lessons = module.lessons || [];
        // Try multiple fields for module title
        const moduleTitle = module.title || module.module_title || `Module ${moduleIndex + 1}`;
        
        html += `
            <div class="module-nav-item" onclick="expandModule(${moduleIndex})">
                Module ${moduleIndex + 1}: ${moduleTitle}
            </div>
            <div id="lessons-module-${moduleIndex}" style="display: none;">
                ${lessons.map((lesson, lessonIndex) => {
                    const isCompleted = userProgress[lesson.id]?.status === 'completed';
                    const isActive = currentLessonId === lesson.id;
                    // Ensure lesson title exists
                    const lessonTitle = lesson.title || `Lesson ${lessonIndex + 1}`;
                    return `
                        <div class="lesson-nav-item ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}"
                             onclick="loadLesson(${lesson.id})">
                            ${lessonTitle}
                            ${lesson.duration_minutes ? ` (${parseInt(lesson.duration_minutes) || 0} min)` : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    });
    
    container.innerHTML = html || '<p style="color: var(--text-secondary);">No modules available</p>';
}

// Expand/collapse module
function expandModule(moduleIndex) {
    const lessonsDiv = document.getElementById(`lessons-module-${moduleIndex}`);
    if (lessonsDiv) {
        lessonsDiv.style.display = lessonsDiv.style.display === 'none' ? 'block' : 'none';
    }
}

// Load lesson
async function loadLesson(lessonId) {
    currentLessonId = lessonId;
    
    try {
        const response = await window.api.getLesson(lessonId);
        if (response.status === 'success' && response.data) {
            currentLessonData = response.data;
            renderLesson();
            renderModulesNav(); // Update active state
            
            // Mark lesson as started
            await updateLessonProgress('in_progress');
        }
    } catch (error) {
        console.error('Error loading lesson:', error);
        showAlert('error', error.message || 'Failed to load lesson');
    }
}

// Render lesson content
function renderLesson() {
    const container = document.getElementById('lesson-content-area');
    if (!container || !currentLessonData) return;
    
    const lesson = currentLessonData;
    const progress = userProgress[lesson.id] || { status: 'not_started' };
    
    let html = `
        <div class="lesson-header">
            <h2 class="lesson-title">${lesson.title || 'Untitled Lesson'}</h2>
            <div class="lesson-meta">
                <span>📹 ${lesson.content_type || 'video'}</span>
                <span>⏱️ ${parseInt(lesson.duration_minutes) || 0} minutes</span>
                ${progress.status === 'completed' ? '<span style="color: var(--success);">✓ Completed</span>' : ''}
            </div>
        </div>
        
        <div class="lesson-description">
            ${lesson.description || 'No description available.'}
        </div>
    `;
    
    // Video/Content
    if (lesson.content_url) {
        if (lesson.content_type === 'video') {
            html += `
                <div class="video-container">
                    <iframe 
                        src="${lesson.content_url}" 
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen>
                    </iframe>
                </div>
            `;
        } else {
            html += `
                <div style="padding: var(--spacing-lg); background: var(--bg-tertiary); border-radius: 8px; margin-bottom: var(--spacing-lg);">
                    <a href="${lesson.content_url}" target="_blank" class="btn btn-primary">View Content</a>
                </div>
            `;
        }
    }
    
    // Transcript
    if (lesson.transcript) {
        html += `
            <div style="margin-top: var(--spacing-lg);">
                <h3>Transcript</h3>
                <p style="color: var(--text-secondary); line-height: 1.8;">${lesson.transcript}</p>
            </div>
        `;
    }
    
    // Quiz - check if quiz exists (can be object or just ID)
    console.log('[Course Content] Checking quiz for lesson:', lesson.id, 'Quiz data:', lesson.quiz);
    const quizId = lesson.quiz?.id || lesson.quiz_id || (typeof lesson.quiz === 'number' ? lesson.quiz : null);
    
    if (quizId || (lesson.quiz && typeof lesson.quiz === 'object')) {
        console.log('[Course Content] Quiz found, ID:', quizId);
        html += `
            <div class="quiz-container" style="margin-top: var(--spacing-xl);">
                <h3 style="margin-bottom: var(--spacing-md);">📝 Quiz</h3>
                ${lesson.quiz?.title ? `<h4 style="margin-bottom: var(--spacing-sm);">${lesson.quiz.title}</h4>` : ''}
                ${lesson.quiz?.description ? `<p style="color: var(--text-secondary); margin-bottom: var(--spacing-md);">${lesson.quiz.description}</p>` : ''}
                <div id="quiz-content">
                    <div style="text-align: center; padding: var(--spacing-md); color: var(--text-secondary);">
                        Loading quiz questions...
                    </div>
                </div>
                <button onclick="submitQuiz()" class="btn btn-primary" style="margin-top: var(--spacing-md);" id="submit-quiz-btn" disabled>
                    Submit Quiz
                </button>
            </div>
        `;
        
        // Load quiz questions - pass quiz ID or quiz object
        const quizData = lesson.quiz || { id: quizId };
        setTimeout(() => loadQuiz(quizData), 100);
    } else {
        console.log('[Course Content] No quiz found for lesson:', lesson.id);
    }
    
    // Navigation buttons
    const { prevLesson, nextLesson } = findAdjacentLessons(lesson.id);
    html += `
        <div class="navigation-buttons">
            <button onclick="${prevLesson ? `loadLesson(${prevLesson.id})` : 'goBack()'}" 
                    class="btn btn-secondary" ${!prevLesson ? '' : ''}>
                ${prevLesson ? '← Previous Lesson' : '← Back to Course'}
            </button>
            <button onclick="${lesson.quiz ? 'submitQuiz()' : 'markLessonComplete()'}" 
                    class="btn btn-primary" id="complete-btn">
                ${lesson.quiz ? 'Complete Quiz' : 'Mark as Complete'}
            </button>
            <button onclick="${nextLesson ? `loadLesson(${nextLesson.id})` : ''}" 
                    class="btn btn-secondary" ${nextLesson ? '' : 'style="visibility: hidden;"'}>
                ${nextLesson ? 'Next Lesson →' : ''}
            </button>
        </div>
    `;
    
    container.innerHTML = html;
}

// Find adjacent lessons
function findAdjacentLessons(lessonId) {
    let prevLesson = null;
    let nextLesson = null;
    let found = false;
    
    for (const module of modulesData) {
        const lessons = module.lessons || [];
        for (let i = 0; i < lessons.length; i++) {
            if (lessons[i].id === lessonId) {
                found = true;
                // Previous lesson
                if (i > 0) {
                    prevLesson = lessons[i - 1];
                } else {
                    // Previous module's last lesson
                    const moduleIndex = modulesData.indexOf(module);
                    if (moduleIndex > 0) {
                        const prevModuleLessons = modulesData[moduleIndex - 1].lessons || [];
                        if (prevModuleLessons.length > 0) {
                            prevLesson = prevModuleLessons[prevModuleLessons.length - 1];
                        }
                    }
                }
                // Next lesson
                if (i < lessons.length - 1) {
                    nextLesson = lessons[i + 1];
                } else {
                    // Next module's first lesson
                    const moduleIndex = modulesData.indexOf(module);
                    if (moduleIndex < modulesData.length - 1) {
                        const nextModuleLessons = modulesData[moduleIndex + 1].lessons || [];
                        if (nextModuleLessons.length > 0) {
                            nextLesson = nextModuleLessons[0];
                        }
                    }
                }
                break;
            }
        }
        if (found) break;
    }
    
    return { prevLesson, nextLesson };
}

// Load quiz
async function loadQuiz(quizData) {
    try {
        const quizId = quizData.id || quizData;
        if (!quizId) {
            console.error('No quiz ID provided');
            const quizContent = document.getElementById('quiz-content');
            if (quizContent) {
                quizContent.innerHTML = '<p style="color: var(--text-secondary);">No quiz available for this lesson.</p>';
            }
            return;
        }
        
        const response = await window.api.getQuiz(quizId);
        
        if (response.status === 'success' && response.data) {
            const quiz = response.data;
            const questions = quiz.questions || [];
            
            if (questions.length === 0) {
                const quizContent = document.getElementById('quiz-content');
                if (quizContent) {
                    quizContent.innerHTML = '<p style="color: var(--text-secondary);">No questions available for this quiz.</p>';
                }
                return;
            }
            
            // Store quiz data for submission - ensure currentLessonData has quiz
            if (currentLessonData) {
                if (!currentLessonData.quiz) {
                    currentLessonData.quiz = { id: quizId };
                }
                currentLessonData.quiz.questions = questions;
            }
            
            let html = '';
            questions.forEach((question, index) => {
                const answers = question.answers || [];
                html += `
                    <div class="quiz-question" data-question-id="${question.id}">
                        <h4>Question ${index + 1}: ${question.text || question.question_text || 'Untitled Question'}</h4>
                        ${answers.length > 0 ? `
                            <div class="quiz-options">
                                ${answers.map((answer, answerIndex) => `
                                    <div class="quiz-option" 
                                         onclick="selectAnswer(${question.id}, ${answer.id}, '${String(answer.text || answer.answer_text || '').replace(/'/g, "\\'")}')" 
                                         data-answer-id="${answer.id}"
                                         data-answer-text="${String(answer.text || answer.answer_text || '').replace(/"/g, '&quot;')}">
                                        ${answer.text || answer.answer_text || `Option ${answerIndex + 1}`}
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<p style="color: var(--text-muted);">No answers available</p>'}
                        ${question.explanation ? `<p style="color: var(--text-secondary); margin-top: var(--spacing-sm); font-size: 0.9rem; font-style: italic;">💡 ${question.explanation}</p>` : ''}
                    </div>
                `;
            });
            
            const quizContent = document.getElementById('quiz-content');
            const submitBtn = document.getElementById('submit-quiz-btn');
            if (quizContent) {
                quizContent.innerHTML = html;
            }
            if (submitBtn) {
                submitBtn.disabled = false;
            }
        } else {
            const quizContent = document.getElementById('quiz-content');
            if (quizContent) {
                quizContent.innerHTML = '<p style="color: var(--text-secondary);">Failed to load quiz questions.</p>';
            }
        }
    } catch (error) {
        console.error('Error loading quiz:', error);
        const quizContent = document.getElementById('quiz-content');
        if (quizContent) {
            quizContent.innerHTML = `<p style="color: var(--error);">Error loading quiz: ${error.message || 'Unknown error'}</p>`;
        }
    }
}

// Select quiz answer
function selectAnswer(questionId, answerId, answerText) {
    // Remove previous selection for this question
    const questionDiv = document.querySelector(`[data-question-id="${questionId}"]`);
    if (questionDiv) {
        questionDiv.querySelectorAll('.quiz-option').forEach(opt => {
            opt.classList.remove('selected');
        });
    }
    
    // Mark selected answer
    const answerDiv = document.querySelector(`[data-answer-id="${answerId}"]`);
    if (answerDiv) {
        answerDiv.classList.add('selected');
        answerDiv.setAttribute('data-selected', 'true');
    }
}

// Submit quiz
async function submitQuiz() {
    if (!currentLessonData || !currentLessonData.quiz) return;
    
    const quizContent = document.getElementById('quiz-content');
    if (!quizContent) return;
    
    // Collect answers - ensure question IDs are strings (backend expects string keys)
    const answers = {};
    let unansweredCount = 0;
    quizContent.querySelectorAll('.quiz-question').forEach((questionDiv) => {
        const questionId = String(questionDiv.dataset.questionId); // Ensure string
        const selectedOption = questionDiv.querySelector('.quiz-option.selected');
        if (selectedOption && selectedOption.dataset.answerId) {
            // Backend expects answer_id as the value
            answers[questionId] = parseInt(selectedOption.dataset.answerId) || selectedOption.dataset.answerId;
        } else {
            unansweredCount++;
        }
    });
    
    if (Object.keys(answers).length === 0) {
        showAlert('error', 'Please answer at least one question');
        return;
    }
    
    // Warn if not all questions answered
    if (unansweredCount > 0) {
        const confirmSubmit = confirm(`You have ${unansweredCount} unanswered question(s). Submit anyway?`);
        if (!confirmSubmit) {
            return;
        }
    }
    
    const submitBtn = document.getElementById('submit-quiz-btn');
    window.utils.setLoading(submitBtn, true);
    
    try {
        // Format: {quiz_id: int, responses: {question_id: answer_id}}
        const response = await window.api.submitQuiz(currentLessonData.quiz.id, answers);
        
        if (response.status === 'success') {
            showAlert('success', `Quiz submitted! Score: ${response.data.percentage_score || 0}%`);
            
            // Mark lesson as completed
            await updateLessonProgress('completed');
            
            // Reload progress
            await loadProgress();
            
            // Show results
            renderQuizResults(response.data);
        }
    } catch (error) {
        showAlert('error', error.message || 'Failed to submit quiz');
    } finally {
        window.utils.setLoading(submitBtn, false);
    }
}

// Render quiz results
function renderQuizResults(results) {
    const quizContent = document.getElementById('quiz-content');
    if (!quizContent) return;
    
    let html = `
        <div style="background: var(--bg-tertiary); padding: var(--spacing-lg); border-radius: 8px; margin-bottom: var(--spacing-md);">
            <h3>Quiz Results</h3>
            <p><strong>Score:</strong> ${results.points_earned || 0} / ${results.total_points || 0}</p>
            <p><strong>Percentage:</strong> ${results.percentage_score || 0}%</p>
            <p><strong>Status:</strong> ${results.is_passed ? '<span style="color: var(--success);">Passed ✓</span>' : '<span style="color: var(--error);">Failed</span>'}</p>
        </div>
    `;
    
    quizContent.innerHTML = html + quizContent.innerHTML;
}

// Mark lesson as complete
async function markLessonComplete() {
    if (!currentLessonId) return;
    
    try {
        await updateLessonProgress('completed');
        showAlert('success', 'Lesson marked as complete!');
        await loadProgress();
        renderModulesNav();
    } catch (error) {
        showAlert('error', error.message || 'Failed to update progress');
    }
}

// Update lesson progress
async function updateLessonProgress(status) {
    if (!currentLessonId || !courseId) return;
    
    try {
        const response = await window.api.updateLessonProgress(currentLessonId, {
            status: status,
            course_id: courseId,
            time_spent_minutes: parseInt(currentLessonData?.duration_minutes) || 0
        });
        
        // Update local progress state immediately for UI responsiveness
        if (!userProgress[currentLessonId]) {
            userProgress[currentLessonId] = {};
        }
        userProgress[currentLessonId].status = status;
        
        // Update completion timestamp
        if (status === 'completed') {
            userProgress[currentLessonId].completed_at = new Date().toISOString();
            
            // Show success message first
            if (response.data?.tokens_earned) {
                showAlert('success', `Lesson completed! You earned ${response.data.tokens_earned} tokens.`);
            }
        }
        
        // Update UI immediately
        renderModulesNav();
        
        // Sync with backend (reload to get updated course-level progress)
        // Use a small delay to allow backend to process
        setTimeout(async () => {
            try {
                await loadProgress();
            } catch (error) {
                console.error('Error reloading progress after update:', error);
                // Don't show error to user, local state is already updated
            }
        }, 500);
        
    } catch (error) {
        console.error('Error updating progress:', error);
        // Revert local state on error
        if (userProgress[currentLessonId]) {
            const previousStatus = userProgress[currentLessonId].status || 'not_started';
            userProgress[currentLessonId].status = previousStatus;
        }
        showAlert('error', 'Failed to update progress. Please try again.');
        renderModulesNav(); // Refresh UI
    }
}

// Load user progress
async function loadProgress() {
    try {
        const response = await window.api.getLessonProgress(courseId);
        if (response.status === 'success' && response.data) {
            const progress = response.data;
            
            // Update progress display
            if (progress.completion_percentage !== undefined) {
                document.getElementById('course-progress').textContent = `${Math.round(progress.completion_percentage)}%`;
                document.getElementById('course-progress-bar').style.width = `${progress.completion_percentage}%`;
            }
            
            if (progress.lessons_completed !== undefined) {
                document.getElementById('lessons-completed').textContent = progress.lessons_completed;
            }
            
            // Store individual lesson progress
            if (progress.lessons && Array.isArray(progress.lessons)) {
                progress.lessons.forEach(lesson => {
                    userProgress[lesson.lesson_id] = {
                        status: lesson.status,
                        completed_at: lesson.completed_at
                    };
                });
            }
            
            renderModulesNav();
        }
    } catch (error) {
        console.error('Error loading progress:', error);
        // Set defaults on error
        document.getElementById('course-progress').textContent = '0%';
        document.getElementById('course-progress-bar').style.width = '0%';
        document.getElementById('lessons-completed').textContent = '0';
    }
}

// Go back to course detail
function goBack() {
    window.utils.redirectTo(`course-detail.html?id=${courseId}`);
}

// Show alert - use centralized utility
function showAlert(type, message) {
    if (window.utils && window.utils.showAlert) {
        window.utils.showAlert(type, message);
    }
}

// Make functions available globally
window.expandModule = expandModule;
window.loadLesson = loadLesson;
window.selectAnswer = selectAnswer;
window.submitQuiz = submitQuiz;
window.markLessonComplete = markLessonComplete;
window.goBack = goBack;

