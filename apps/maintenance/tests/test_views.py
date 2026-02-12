"""Basic view access tests for maintenance (task list requires login)."""
from django.test import TestCase, Client
from django.urls import reverse

from apps.users.models import User
from apps.vehicles.models import Vehicle, VehicleType
from apps.maintenance.models import MaintenanceTask, MaintenanceTemplate, WorkOrder


class MaintenanceViewAccessTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_task_list_requires_login(self):
        resp = self.client.get(reverse('maintenance:task_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url or resp.get('Location', ''))

    def test_template_list_requires_can_manage_maintenance(self):
        driver = User.objects.create_user(
            email='maintdriver@test.local',
            password='TestPass123!',
            role=User.Role.DRIVER,
        )
        self.client.force_login(driver)
        resp = self.client.get(reverse('maintenance:template_list'))
        self.assertEqual(resp.status_code, 403)

    def test_template_list_ok_for_manager(self):
        manager = User.objects.create_user(
            email='maintmanager@test.local',
            password='TestPass123!',
            role=User.Role.FLEET_MANAGER,
        )
        self.client.force_login(manager)
        resp = self.client.get(reverse('maintenance:template_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('templates', resp.context)

    def test_workorder_list_ok_for_manager(self):
        manager = User.objects.create_user(
            email='womanager@test.local',
            password='TestPass123!',
            role=User.Role.FLEET_MANAGER,
        )
        self.client.force_login(manager)
        resp = self.client.get(reverse('maintenance:workorder_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('work_orders', resp.context)

    def test_maintenance_export_csv_requires_can_manage(self):
        driver = User.objects.create_user(
            email='csvdriver@test.local',
            password='TestPass123!',
            role=User.Role.DRIVER,
        )
        self.client.force_login(driver)
        resp = self.client.get(reverse('maintenance:maintenance_export_csv'))
        self.assertEqual(resp.status_code, 403)
