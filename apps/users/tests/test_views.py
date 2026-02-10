"""Basic user view tests: profile requires login, redirects."""
from django.test import TestCase, Client
from django.urls import reverse


class UserViewAccessTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_profile_requires_login(self):
        resp = self.client.get(reverse('users:profile'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('login', resp.url or resp.get('Location', ''))
