"""Tests for vehicle models: get_health_status, is_engine_on, VehicleAlert."""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.users.models import User
from apps.vehicles.models import Vehicle, VehicleType, VehicleAlert, VehicleTelemetry, Runbook
from apps.maintenance.models import MaintenanceTask


class VehicleHealthStatusTest(TestCase):
    """Test Vehicle.get_health_status() and is_engine_on()."""

    def setUp(self):
        self.vt = VehicleType.objects.create(
            name='Sedan',
            maintenance_interval_days=90,
            maintenance_interval_km=10000,
        )
        self.vehicle = Vehicle.objects.create(
            license_plate='TST-001',
            vin='1HGBH41JXMN109999',
            make='Test',
            model='Car',
            year=2022,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
        )

    def test_health_green_when_no_alerts_no_maintenance(self):
        self.assertEqual(self.vehicle.get_health_status(), 'green')

    def test_health_red_critical_unread_alert(self):
        VehicleAlert.objects.create(
            vehicle=self.vehicle,
            alert_type=VehicleAlert.AlertType.HIGH_ENGINE_TEMP,
            severity=VehicleAlert.Severity.CRITICAL,
            message='Critical',
            created_at=timezone.now(),
        )
        self.assertEqual(self.vehicle.get_health_status(), 'red')

    def test_health_red_overdue_maintenance(self):
        MaintenanceTask.objects.create(
            vehicle=self.vehicle,
            title='Oil',
            scheduled_date=timezone.now().date() - timedelta(days=1),
            status='scheduled',
        )
        self.assertEqual(self.vehicle.get_health_status(), 'red')

    def test_health_yellow_high_unread_alert(self):
        VehicleAlert.objects.create(
            vehicle=self.vehicle,
            alert_type=VehicleAlert.AlertType.ANOMALOUS_FUEL,
            severity=VehicleAlert.Severity.HIGH,
            message='High',
            created_at=timezone.now(),
        )
        self.assertEqual(self.vehicle.get_health_status(), 'yellow')

    def test_health_yellow_maintenance_due_soon(self):
        MaintenanceTask.objects.create(
            vehicle=self.vehicle,
            title='Inspection',
            scheduled_date=timezone.now().date() + timedelta(days=7),
            status='scheduled',
        )
        self.assertEqual(self.vehicle.get_health_status(), 'yellow')

    def test_is_engine_on_false_when_no_telemetry(self):
        self.assertFalse(self.vehicle.is_engine_on())

    def test_is_engine_on_true_when_recent_telemetry(self):
        self.vehicle.last_telemetry_at = timezone.now()
        self.vehicle.save()
        self.assertTrue(self.vehicle.is_engine_on(threshold_seconds=90))

    def test_health_status_property(self):
        self.assertEqual(self.vehicle.health_status, 'green')


class VehicleAlertTest(TestCase):
    """Test VehicleAlert model."""

    def setUp(self):
        self.vt = VehicleType.objects.create(name='Van', maintenance_interval_days=90, maintenance_interval_km=10000)
        self.vehicle = Vehicle.objects.create(
            license_plate='TST-002',
            vin='2HGBH41JXMN109998',
            make='Test',
            model='Van',
            year=2021,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
        )

    def test_alert_creation_with_timeframe(self):
        alert = VehicleAlert.objects.create(
            vehicle=self.vehicle,
            alert_type=VehicleAlert.AlertType.MAINTENANCE_MILEAGE,
            severity=VehicleAlert.Severity.HIGH,
            message='Due in 500 km',
            timeframe_text='En 500 km',
        )
        self.assertEqual(alert.timeframe_text, 'En 500 km')
        self.assertIsNone(alert.read_at)


class RunbookExecuteTest(TestCase):
    """Test Runbook.execute() for mark_alert_read and create_maintenance_task."""

    def setUp(self):
        self.vt = VehicleType.objects.create(name='Sedan', maintenance_interval_days=90, maintenance_interval_km=10000)
        self.vehicle = Vehicle.objects.create(
            license_plate='TST-003',
            vin='3HGBH41JXMN109997',
            make='Test',
            model='Car',
            year=2023,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
        )
        self.user = User.objects.create_user(email='runner@test.local', password='TestPass123!', role='fleet_manager')
        self.alert = VehicleAlert.objects.create(
            vehicle=self.vehicle,
            alert_type=VehicleAlert.AlertType.HIGH_ENGINE_TEMP,
            severity=VehicleAlert.Severity.HIGH,
            message='Hot engine',
        )

    def test_mark_alert_read(self):
        runbook = Runbook.objects.create(
            name='Mark read',
            action_type=Runbook.ActionType.MARK_ALERT_READ,
            is_active=True,
        )
        success, msg = runbook.execute(self.alert, self.user)
        self.assertTrue(success)
        self.alert.refresh_from_db()
        self.assertIsNotNone(self.alert.read_at)

    def test_create_maintenance_task(self):
        runbook = Runbook.objects.create(
            name='Create task',
            action_type=Runbook.ActionType.CREATE_MAINTENANCE_TASK,
            params={'title': 'Inspect engine', 'days_ahead': 2},
            is_active=True,
        )
        initial_count = MaintenanceTask.objects.filter(vehicle=self.vehicle).count()
        success, msg = runbook.execute(self.alert, self.user)
        self.assertTrue(success)
        self.assertEqual(MaintenanceTask.objects.filter(vehicle=self.vehicle).count(), initial_count + 1)
        task = MaintenanceTask.objects.filter(vehicle=self.vehicle).order_by('-created_at').first()
        self.assertEqual(task.title, 'Inspect engine')
