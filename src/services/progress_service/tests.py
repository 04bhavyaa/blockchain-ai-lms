from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import (
    LessonProgress, QuizAttempt, ModuleProgress,
    CourseProgress, ProgressSnapshot
)

User = get_user_model()

class ProgressServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="progress@edu.com", username="progressor", password="pw123456")
        self.lesson = LessonProgress.objects.create(
            user=self.user, lesson_id=101, lesson_title="Intro Lesson", course_id=10, module_id=2, status="in_progress"
        )
        self.quiz = QuizAttempt.objects.create(
            user=self.user, lesson_id=101, quiz_id=999, quiz_title="Quiz One", course_id=10,
            status="submitted", total_points=5, points_earned=3, percentage_score=60
        )
        self.module = ModuleProgress.objects.create(
            user=self.user, module_id=2, module_title="Basics", course_id=10, total_lessons=5, lessons_completed=2
        )
        self.course = CourseProgress.objects.create(
            user=self.user, course_id=10, course_title="Blockchain Course", status="in_progress", total_modules=3, modules_completed=1
        )
        self.snapshot = ProgressSnapshot.objects.create(
            user=self.user, course_id=10, lessons_completed=2, quizzes_passed=1, completion_percentage=50
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_lesson_progress_crud(self):
        self.authenticate()
        url = reverse("lesson-progress-detail", args=[self.lesson.id])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["lesson_title"], "Intro Lesson")
        r2 = self.client.patch(url, {"status": "completed", "video_watched_percentage": 100})
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], "completed")

    def test_lesson_blockchain_callback(self):
        self.authenticate()
        url = reverse("lessonprogress-blockchain-callback", args=[self.lesson.id])
        r = self.client.post(url, {"tx_hash": "0xlesson", "message": "Lesson event"})
        self.assertEqual(r.status_code, 200)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.blockchain_event_tx_hash, "0xlesson")

    def test_quiz_blockchain_callback(self):
        self.authenticate()
        url = reverse("quizattempt-blockchain-callback", args=[self.quiz.id])
        r = self.client.post(url, {"tx_hash": "0xquiz", "message": "Quiz event"})
        self.assertEqual(r.status_code, 200)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.blockchain_event_tx_hash, "0xquiz")

    def test_module_blockchain_callback(self):
        self.authenticate()
        url = reverse("moduleprogress-blockchain-callback", args=[self.module.id])
        r = self.client.post(url, {"tx_hash": "0xmodule", "message": "Module event"})
        self.assertEqual(r.status_code, 200)
        self.module.refresh_from_db()
        self.assertEqual(self.module.blockchain_event_tx_hash, "0xmodule")

    def test_course_blockchain_callback_and_complete(self):
        self.authenticate()
        url_cb = reverse("courseprogress-blockchain-callback", args=[self.course.id])
        r_cb = self.client.post(url_cb, {"tx_hash": "0xcourse", "message": "Course event"})
        self.assertEqual(r_cb.status_code, 200)
        self.course.refresh_from_db()
        self.assertEqual(self.course.blockchain_event_tx_hash, "0xcourse")
        url_comp = reverse("courseprogress-mark-complete", args=[self.course.id])
        r_comp = self.client.post(url_comp)
        self.assertEqual(r_comp.status_code, 200)
        self.course.refresh_from_db()
        self.assertTrue(self.course.certificate_issued)

    def test_snapshot_blockchain_callback(self):
        self.authenticate()
        url = reverse("progresssnapshot-blockchain-callback", args=[self.snapshot.id])
        r = self.client.post(url, {"tx_hash": "0xsnap", "message": "Snap event"})
        self.assertEqual(r.status_code, 200)
        self.snapshot.refresh_from_db()
        self.assertEqual(self.snapshot.blockchain_event_tx_hash, "0xsnap")
