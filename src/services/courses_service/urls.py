"""
Courses service URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, LessonViewSet, EnrollmentViewSet,
    CourseRatingViewSet, BookmarkViewSet, QuizViewSet
)

router = DefaultRouter()
router.register(r'', CourseViewSet, basename='course')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'ratings', CourseRatingViewSet, basename='rating')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')

urlpatterns = [
    # Custom action endpoints (must be before router.urls catch-all)
    path('my-courses/', CourseViewSet.as_view({'get': 'my_courses'}), name='my-courses'),
    path('categories/', CourseViewSet.as_view({'get': 'categories'}), name='course-categories'),
    
    # Enrollment custom blockchain callback endpoint
    path('enrollments/<int:pk>/blockchain-callback/', 
         EnrollmentViewSet.as_view({'post': 'block_callback'}),
         name='enrollment-blockchain-callback'),
    
    # Router URLs (catch-all - must be last)
    path('', include(router.urls)),
]