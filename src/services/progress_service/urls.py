"""
Progress service URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LessonProgressViewSet, QuizAttemptViewSet,
    CourseProgressViewSet, ProgressSnapshotViewSet
)

router = DefaultRouter()
router.register(r'lessons', LessonProgressViewSet, basename='lesson-progress')
router.register(r'quizzes', QuizAttemptViewSet, basename='quiz-attempts')
router.register(r'courses', CourseProgressViewSet, basename='course-progress')
router.register(r'snapshots', ProgressSnapshotViewSet, basename='progress-snapshots')

urlpatterns = [
    path('', include(router.urls)),
]
