import { API_ENDPOINTS } from '../config/api.js';
import { AuthService } from './auth.js';
import { showAlert } from '../utils/utils.js';

export const CoursesService = {
    // Get all courses
    async getCourses(params = {}) {
        try {
            const queryString = new URLSearchParams(params).toString();
            const url = `${API_ENDPOINTS.COURSES.LIST}${queryString ? '?' + queryString : ''}`;

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch courses');
            }

            return data;
        } catch (error) {
            console.error('Get courses error:', error);
            throw error;
        }
    },

    // Get single course details
    async getCourseDetail(courseId) {
        try {
            const response = await fetch(API_ENDPOINTS.COURSES.DETAIL(courseId), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch course details');
            }

            return data.data;
        } catch (error) {
            console.error('Get course detail error:', error);
            throw error;
        }
    },

    // Enroll in course
    async enrollCourse(courseId) {
        try {
            const token = AuthService.getToken();
            const response = await fetch(API_ENDPOINTS.COURSES.ENROLL(courseId), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to enroll in course');
            }

            showAlert('success', 'Successfully enrolled in course!');
            return data.data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },

    // Unenroll from course
    async unenrollCourse(courseId) {
        try {
            const token = AuthService.getToken();
            const response = await fetch(API_ENDPOINTS.COURSES.UNENROLL(courseId), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to unenroll from course');
            }

            showAlert('success', 'Successfully unenrolled from course');
            return data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },

    // Get course lessons
    async getCourseLessons(courseId) {
        try {
            const token = AuthService.getToken();
            const response = await fetch(API_ENDPOINTS.COURSES.LESSONS(courseId), {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch lessons');
            }

            return data.data;
        } catch (error) {
            console.error('Get lessons error:', error);
            throw error;
        }
    },

    // Get lesson detail
    async getLessonDetail(courseId, lessonId) {
        try {
            const token = AuthService.getToken();
            const response = await fetch(API_ENDPOINTS.COURSES.LESSON_DETAIL(courseId, lessonId), {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch lesson');
            }

            return data.data;
        } catch (error) {
            console.error('Get lesson detail error:', error);
            throw error;
        }
    },

    // Mark lesson as complete
    async markLessonComplete(courseId, lessonId) {
        try {
            const token = AuthService.getToken();
            const response = await fetch(API_ENDPOINTS.COURSES.MARK_COMPLETE(courseId, lessonId), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to mark lesson complete');
            }

            showAlert('success', 'Lesson marked as complete! Tokens earned.');
            return data.data;
        } catch (error) {
            showAlert('error', error.message);
            throw error;
        }
    },

    // Get user's enrolled courses
    async getMyCourses() {
        try {
            const token = AuthService.getToken();
            const response = await fetch(API_ENDPOINTS.COURSES.MY_COURSES, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch your courses');
            }

            return data.data;
        } catch (error) {
            console.error('Get my courses error:', error);
            throw error;
        }
    },

    // Get course categories
    async getCategories() {
        try {
            const response = await fetch(API_ENDPOINTS.COURSES.CATEGORIES, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Failed to fetch categories');
            }

            return data.data;
        } catch (error) {
            console.error('Get categories error:', error);
            throw error;
        }
    },
};
