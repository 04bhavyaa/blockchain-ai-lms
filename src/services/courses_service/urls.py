"""
Courses service URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, LessonViewSet, EnrollmentViewSet,
    CourseRatingViewSet, BookmarkViewSet
)

router = DefaultRouter()
router.register(r'', CourseViewSet, basename='courses')
router.register(r'lessons', LessonViewSet, basename='lessons')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollments')
router.register(r'ratings', CourseRatingViewSet, basename='ratings')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmarks')

urlpatterns = [
    path('', include(router.urls)),
]
