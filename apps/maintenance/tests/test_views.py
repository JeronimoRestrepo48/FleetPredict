"""Basic view access tests for maintenance (task list requires login)."""
from django.test import TestCase, Client
from django.urls import reverse


class MaintenanceViewAccessTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_task_list_requires_login(self):
        resp = self.client.get(reverse('maintenance:task_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url or resp.get('Location', ''))
