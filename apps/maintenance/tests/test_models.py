"""Tests for MaintenanceTask: states, is_overdue, soft delete (vehicle is_deleted)."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.users.models import User
from apps.vehicles.models import Vehicle, VehicleType
from apps.maintenance.models import MaintenanceTask


class MaintenanceTaskTest(TestCase):
    def setUp(self):
        self.vt = VehicleType.objects.create(name='Sedan', maintenance_interval_days=90, maintenance_interval_km=10000)
        self.vehicle = Vehicle.objects.create(
            license_plate='MNT-001',
            vin='1HGBH41JXMN109000',
            make='Test',
            model='Car',
            year=2022,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
        )
        self.user = User.objects.create_user(email='mec@test.local', password='TestPass123!', role=User.Role.MECHANIC)

    def test_is_overdue_true_when_scheduled_past(self):
        task = MaintenanceTask.objects.create(
            vehicle=self.vehicle,
            title='Oil change',
            scheduled_date=timezone.now().date() - timedelta(days=1),
            status=MaintenanceTask.Status.SCHEDULED,
        )
        self.assertTrue(task.is_overdue)

    def test_is_overdue_false_when_completed(self):
        task = MaintenanceTask.objects.create(
            vehicle=self.vehicle,
            title='Inspection',
            scheduled_date=timezone.now().date() - timedelta(days=1),
            status=MaintenanceTask.Status.COMPLETED,
            completion_date=timezone.now().date(),
        )
        self.assertFalse(task.is_overdue)

    def test_mark_completed_sets_fields(self):
        task = MaintenanceTask.objects.create(
            vehicle=self.vehicle,
            title='Brake check',
            scheduled_date=timezone.now().date(),
            status=MaintenanceTask.Status.SCHEDULED,
        )
        task.mark_completed(completion_notes='OK', actual_cost=50, mileage=10000)
        task.refresh_from_db()
        self.assertEqual(task.status, MaintenanceTask.Status.COMPLETED)
        self.assertIsNotNone(task.completion_date)
        self.assertEqual(task.actual_cost, 50)
        self.assertEqual(task.mileage_at_maintenance, 10000)
