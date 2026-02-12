"""Tests for reports views: index, trends, cost, comparison require can_view_reports."""
from django.test import TestCase, Client
from django.urls import reverse

from apps.users.models import User


class ReportsViewAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.driver = User.objects.create_user(
            email='reportdriver@test.local',
            password='TestPass123!',
            role=User.Role.DRIVER,
        )
        self.manager = User.objects.create_user(
            email='reportmanager@test.local',
            password='TestPass123!',
            role=User.Role.FLEET_MANAGER,
        )

    def test_reports_index_requires_login(self):
        resp = self.client.get(reverse('reports:index'))
        self.assertEqual(resp.status_code, 302)

    def test_reports_index_ok_for_manager(self):
        self.client.force_login(self.manager)
        resp = self.client.get(reverse('reports:index'))
        self.assertEqual(resp.status_code, 200)

    def test_trends_requires_can_view_reports(self):
        self.client.force_login(self.driver)
        resp = self.client.get(reverse('reports:trends'))
        self.assertEqual(resp.status_code, 403)

    def test_trends_ok_for_manager(self):
        self.client.force_login(self.manager)
        resp = self.client.get(reverse('reports:trends'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('by_month', resp.context)

    def test_cost_ok_for_manager(self):
        self.client.force_login(self.manager)
        resp = self.client.get(reverse('reports:cost'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('by_vehicle', resp.context)

    def test_comparison_ok_for_manager(self):
        self.client.force_login(self.manager)
        resp = self.client.get(reverse('reports:comparison'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('by_vehicle', resp.context)
