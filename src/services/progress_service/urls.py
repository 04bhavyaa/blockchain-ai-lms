from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LessonProgressViewSet, QuizAttemptViewSet,
    CourseProgressViewSet, ProgressSnapshotViewSet, ModuleProgressViewSet
)

router = DefaultRouter()
router.register(r'lessons', LessonProgressViewSet, basename='lesson-progress')
router.register(r'quizzes', QuizAttemptViewSet, basename='quiz-attempts')
router.register(r'courses', CourseProgressViewSet, basename='course-progress')
router.register(r'snapshots', ProgressSnapshotViewSet, basename='progress-snapshots')

urlpatterns = [
    path('', include(router.urls)),
    path('lessons/<int:pk>/blockchain-callback/',
         LessonProgressViewSet.as_view({'post': 'blockchain_callback'}),
         name='lessonprogress-blockchain-callback'),
    path('quizzes/<int:pk>/blockchain-callback/',
         QuizAttemptViewSet.as_view({'post': 'blockchain_callback'}),
         name='quizattempt-blockchain-callback'),
    path('modules/<int:pk>/blockchain-callback/',
         ModuleProgressViewSet.as_view({'post': 'blockchain_callback'}),
         name='moduleprogress-blockchain-callback'),
    path('courses/<int:pk>/blockchain-callback/',
         CourseProgressViewSet.as_view({'post': 'blockchain_callback'}),
         name='courseprogress-blockchain-callback'),
    path('snapshots/<int:pk>/blockchain-callback/',
         ProgressSnapshotViewSet.as_view({'post': 'blockchain_callback'}),
         name='progresssnapshot-blockchain-callback'),
]
