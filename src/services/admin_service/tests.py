from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import AdminDashboardLog

User = get_user_model()

class AdminServiceTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(email="admin@lms.com", is_staff=True, is_superuser=True)
    def test_create_log(self):
        log = AdminDashboardLog.objects.create(
            admin_user=self.admin,
            action_type="user_created",
            description="Test log entry"
        )
        self.assertIsNotNone(log.id)
