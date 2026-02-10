"""Tests for consumer sync helpers: _get_vehicle, _save_telemetry, _telemetry_payload_for_broadcast."""
import unittest
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.vehicles.models import Vehicle, VehicleType, VehicleTelemetry

try:
    from apps.vehicles.consumers import _get_vehicle, _save_telemetry, _telemetry_payload_for_broadcast
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False
    _get_vehicle = _save_telemetry = _telemetry_payload_for_broadcast = None


@unittest.skipUnless(CHANNELS_AVAILABLE, 'channels not installed')
class ConsumerHelpersTest(TestCase):
    def setUp(self):
        self.vt = VehicleType.objects.create(name='Sedan', maintenance_interval_days=90, maintenance_interval_km=10000)
        self.vehicle = Vehicle.objects.create(
            license_plate='CON-001',
            vin='1HGBH41JXMN300001',
            make='Test',
            model='Car',
            year=2022,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
        )

    def test_get_vehicle_by_id(self):
        v = _get_vehicle(vehicle_id=self.vehicle.pk)
        self.assertIsNotNone(v)
        self.assertEqual(v.pk, self.vehicle.pk)

    def test_get_vehicle_by_license_plate(self):
        v = _get_vehicle(license_plate='CON-001')
        self.assertIsNotNone(v)
        self.assertEqual(v.license_plate, 'CON-001')

    def test_get_vehicle_returns_none_for_deleted(self):
        self.vehicle.is_deleted = True
        self.vehicle.save()
        v = _get_vehicle(vehicle_id=self.vehicle.pk)
        self.assertIsNone(v)

    @patch('apps.vehicles.consumers.evaluate_and_save_alerts')
    def test_save_telemetry_creates_reading_and_updates_vehicle(self, mock_eval):
        mock_eval.return_value = []
        payload = {
            'speed_kmh': 60,
            'fuel_level_pct': 80,
            'engine_temperature_c': 90,
            'mileage': 10050,
        }
        telem = _save_telemetry(self.vehicle, payload)
        self.assertIsNotNone(telem.pk)
        self.assertEqual(telem.vehicle_id, self.vehicle.pk)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.current_mileage, 10050)
        self.assertIsNotNone(self.vehicle.last_telemetry_at)

    def test_telemetry_payload_for_broadcast(self):
        ts = timezone.now()
        payload = {'speed_kmh': 50, 'fuel_level_pct': 75, 'engine_temperature_c': 88, 'mileage': 10000}
        out = _telemetry_payload_for_broadcast(self.vehicle, payload, ts)
        self.assertEqual(out['vehicle_id'], self.vehicle.pk)
        self.assertEqual(out['speed_kmh'], 50)
        self.assertEqual(out['mileage'], 10000)
