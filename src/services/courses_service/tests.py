from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Course, CourseCategory, Enrollment

User = get_user_model()

class CoursesServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="student@ex.com",
            username="stud",
            password="testpass123"
        )
        self.cat = CourseCategory.objects.create(
            name="Blockchain", slug="blockchain", description="Test"
        )
        self.course = Course.objects.create(
            title="Intro Chain", slug="intro-chain", description="desc", category=self.cat,
            instructor=self.user, access_type="free", total_enrollments=0,
            created_by=self.user, status="published"
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_course_list(self):
        self.authenticate()
        resp = self.client.get(reverse("course-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data["data"]), 1)

    def test_course_detail(self):
        self.authenticate()
        resp = self.client.get(reverse("course-detail", args=[self.course.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["data"]["title"], "Intro Chain")

    def test_enroll_in_course(self):
        self.authenticate()
        resp = self.client.post(reverse("course-enroll", args=[self.course.id]))
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(
            Enrollment.objects.filter(user=self.user, course=self.course).exists()
        )

    def test_enroll_duplicate(self):
        self.authenticate()
        Enrollment.objects.create(user=self.user, course=self.course)
        resp = self.client.post(reverse("course-enroll", args=[self.course.id]))
        self.assertEqual(resp.status_code, 400)

    def test_rate_course(self):
        self.authenticate()
        Enrollment.objects.create(user=self.user, course=self.course)
        resp = self.client.post(reverse("course-rate", args=[self.course.id]), {
            "rating": 4
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["data"]["rating"], 4)

    def test_bookmark_unbookmark(self):
        self.authenticate()
        resp = self.client.post(reverse("course-bookmark", args=[self.course.id]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.delete(reverse("course-unbookmark", args=[self.course.id]))
        self.assertEqual(resp.status_code, 200)

    def test_blockchain_enrollment_callback(self):
        self.authenticate()
        Enrollment.objects.create(user=self.user, course=self.course, status="pending_blockchain")
        enroll = Enrollment.objects.get(user=self.user, course=self.course)
        url = reverse("enrollment-blockchain-callback", args=[enroll.id])
        resp = self.client.post(url, {"event": "unlock", "tx_hash": "0x123", "message": "Unlocked by chain"})
        self.assertEqual(resp.status_code, 200)
        enroll.refresh_from_db()
        self.assertEqual(enroll.status, "enrolled")
        self.assertEqual(enroll.blockchain_unlock_tx_hash, "0x123")
        self.assertIn("Unlocked by chain", enroll.last_blockchain_status)
