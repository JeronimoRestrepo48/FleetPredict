"""Tests for dashboard views: index, execute_runbook, predictions, alerts by role."""
from django.test import TestCase, Client
from django.urls import reverse

from apps.users.models import User
from apps.vehicles.models import Vehicle, VehicleType, VehicleAlert, Runbook


class DashboardAccessTest(TestCase):
    """Dashboard and alerts: driver sees only their vehicles."""

    def setUp(self):
        self.client = Client()
        self.vt = VehicleType.objects.create(name='Sedan', maintenance_interval_days=90, maintenance_interval_km=10000)
        self.driver = User.objects.create_user(
            email='dashdriver@test.local',
            password='TestPass123!',
            role=User.Role.DRIVER,
        )
        self.manager = User.objects.create_user(
            email='dashmanager@test.local',
            password='TestPass123!',
            role=User.Role.FLEET_MANAGER,
        )
        self.vehicle = Vehicle.objects.create(
            license_plate='DASH-1',
            vin='1HGBH41JXMN200001',
            make='A',
            model='B',
            year=2022,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
            assigned_driver=self.driver,
        )
        self.alert = VehicleAlert.objects.create(
            vehicle=self.vehicle,
            alert_type=VehicleAlert.AlertType.HIGH_ENGINE_TEMP,
            severity=VehicleAlert.Severity.HIGH,
            message='Test alert',
        )
        self.runbook = Runbook.objects.create(
            name='Mark read',
            action_type=Runbook.ActionType.MARK_ALERT_READ,
            is_active=True,
        )

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resp.status_code, 302)

    def test_dashboard_driver_sees_own_vehicle(self):
        self.client.force_login(self.driver)
        resp = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('vehicle_health_counts', resp.context)

    def test_alerts_list_driver_sees_own_alerts(self):
        self.client.force_login(self.driver)
        resp = self.client.get(reverse('dashboard:alerts'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('alerts', resp.context)

    def test_predictions_requires_can_view_reports(self):
        self.client.force_login(self.driver)
        resp = self.client.get(reverse('dashboard:predictions'))
        self.assertEqual(resp.status_code, 403)

    def test_predictions_ok_for_manager(self):
        self.client.force_login(self.manager)
        resp = self.client.get(reverse('dashboard:predictions'))
        self.assertEqual(resp.status_code, 200)

    def test_execute_runbook_mark_read(self):
        self.client.force_login(self.driver)
        get_resp = self.client.get(reverse('dashboard:index'))
        csrf = get_resp.cookies.get('csrftoken')
        csrf_token = csrf.value if csrf else ''
        resp = self.client.post(reverse('dashboard:execute_runbook'), data={
            'alert_id': self.alert.pk,
            'runbook_id': self.runbook.pk,
            'csrfmiddlewaretoken': csrf_token,
        }, follow=False)
        self.assertIn(resp.status_code, [200, 302])
        self.alert.refresh_from_db()
        self.assertIsNotNone(self.alert.read_at)

    def test_suggested_maintenance_requires_can_view_reports(self):
        self.client.force_login(self.driver)
        resp = self.client.get(reverse('dashboard:suggested_maintenance'))
        self.assertEqual(resp.status_code, 403)

    def test_suggested_maintenance_ok_for_manager(self):
        self.client.force_login(self.manager)
        resp = self.client.get(reverse('dashboard:suggested_maintenance'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('suggestions', resp.context)

    def test_audit_log_requires_administrator(self):
        self.client.force_login(self.manager)
        resp = self.client.get(reverse('dashboard:auditlog_list'))
        self.assertEqual(resp.status_code, 403)

    def test_audit_log_ok_for_administrator(self):
        admin = User.objects.create_user(
            email='admin@test.local',
            password='TestPass123!',
            role=User.Role.ADMINISTRATOR,
        )
        self.client.force_login(admin)
        resp = self.client.get(reverse('dashboard:auditlog_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('audit_logs', resp.context)
