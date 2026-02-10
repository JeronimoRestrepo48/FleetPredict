"""Tests for vehicle views: list/detail access by role (driver sees only assigned)."""
from django.test import TestCase, Client
from django.urls import reverse

from apps.users.models import User
from apps.vehicles.models import Vehicle, VehicleType


class VehicleListAccessTest(TestCase):
    """Driver sees only assigned vehicles; others see all."""

    def setUp(self):
        self.client = Client()
        self.vt = VehicleType.objects.create(name='Sedan', maintenance_interval_days=90, maintenance_interval_km=10000)
        self.driver = User.objects.create_user(
            email='driver@test.local',
            password='TestPass123!',
            role=User.Role.DRIVER,
        )
        self.manager = User.objects.create_user(
            email='manager@test.local',
            password='TestPass123!',
            role=User.Role.FLEET_MANAGER,
        )
        self.v1 = Vehicle.objects.create(
            license_plate='V1',
            vin='1HGBH41JXMN100001',
            make='A',
            model='B',
            year=2022,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
            assigned_driver=self.driver,
        )
        self.v2 = Vehicle.objects.create(
            license_plate='V2',
            vin='2HGBH41JXMN100002',
            make='C',
            model='D',
            year=2023,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
            assigned_driver=None,
        )

    def test_driver_sees_only_assigned_vehicle(self):
        self.client.force_login(self.driver)
        resp = self.client.get(reverse('vehicles:vehicle_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'V1')
        self.assertNotContains(resp, 'V2')

    def test_manager_sees_all_vehicles(self):
        self.client.force_login(self.manager)
        resp = self.client.get(reverse('vehicles:vehicle_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'V1')
        self.assertContains(resp, 'V2')

    def test_vehicle_detail_driver_forbidden_other_vehicle(self):
        self.client.force_login(self.driver)
        resp = self.client.get(reverse('vehicles:vehicle_detail', args=[self.v2.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_vehicle_detail_driver_ok_own_vehicle(self):
        self.client.force_login(self.driver)
        resp = self.client.get(reverse('vehicles:vehicle_detail', args=[self.v1.pk]))
        self.assertEqual(resp.status_code, 200)


class VehicleHistoryAccessTest(TestCase):
    """History view: driver only for assigned vehicle."""

    def setUp(self):
        self.client = Client()
        self.vt = VehicleType.objects.create(name='Sedan', maintenance_interval_days=90, maintenance_interval_km=10000)
        self.driver = User.objects.create_user(
            email='driver2@test.local',
            password='TestPass123!',
            role=User.Role.DRIVER,
        )
        self.vehicle = Vehicle.objects.create(
            license_plate='VH',
            vin='3HGBH41JXMN100003',
            make='X',
            model='Y',
            year=2022,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
            assigned_driver=self.driver,
        )

    def test_history_returns_200_and_context(self):
        self.client.force_login(self.driver)
        resp = self.client.get(reverse('vehicles:vehicle_history', args=[self.vehicle.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('history', resp.context)
