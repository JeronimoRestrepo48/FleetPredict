"""Tests for telemetry_patterns: evaluate_patterns, evaluate_and_save_alerts."""
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.vehicles.models import Vehicle, VehicleType, VehicleTelemetry, VehicleAlert
from apps.maintenance.models import MaintenanceTask
from apps.vehicles.services.telemetry_patterns import (
    evaluate_patterns,
    evaluate_and_save_alerts,
    check_high_engine_temp,
    get_recent_telemetry,
)


class CheckHighEngineTempTest(TestCase):
    """Test high engine temperature pattern."""

    def setUp(self):
        self.vt = VehicleType.objects.create(name='Sedan', maintenance_interval_days=90, maintenance_interval_km=10000)
        self.vehicle = Vehicle.objects.create(
            license_plate='TST-TMP',
            vin='1HGBH41JXMN109001',
            make='Test',
            model='Car',
            year=2022,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
        )

    def test_high_temp_returns_alert(self):
        class Reading:
            engine_temperature_c = Decimal('110')
        readings = [Reading()]
        r = check_high_engine_temp(readings)
        self.assertIsNotNone(r)
        self.assertEqual(r['type'], VehicleAlert.AlertType.HIGH_ENGINE_TEMP)
        self.assertIn(r['severity'], [VehicleAlert.Severity.HIGH, VehicleAlert.Severity.CRITICAL])

    def test_normal_temp_returns_none(self):
        class Reading:
            engine_temperature_c = Decimal('85')
        readings = [Reading()]
        self.assertIsNone(check_high_engine_temp(readings))


class EvaluatePatternsTest(TestCase):
    """Test evaluate_patterns and get_recent_telemetry."""

    def setUp(self):
        self.vt = VehicleType.objects.create(name='Van', maintenance_interval_days=90, maintenance_interval_km=10000)
        self.vehicle = Vehicle.objects.create(
            license_plate='TST-EVAL',
            vin='2HGBH41JXMN109002',
            make='Test',
            model='Van',
            year=2021,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
            current_mileage=5000,
        )

    def test_evaluate_patterns_empty_without_readings(self):
        result = evaluate_patterns(self.vehicle.pk, [])
        self.assertEqual(result, [])

    def test_evaluate_patterns_high_temp(self):
        ts = timezone.now()
        for i in range(3):
            VehicleTelemetry.objects.create(
                vehicle=self.vehicle,
                timestamp=ts,
                engine_temperature_c=Decimal('108'),
            )
        readings = get_recent_telemetry(self.vehicle.pk, limit=10)
        result = evaluate_patterns(self.vehicle.pk, readings)
        self.assertGreater(len(result), 0)
        types = [r['type'] for r in result]
        self.assertIn(VehicleAlert.AlertType.HIGH_ENGINE_TEMP, types)


class EvaluateAndSaveAlertsTest(TestCase):
    """Test evaluate_and_save_alerts: creates alerts, cooldown, timeframe."""

    def setUp(self):
        self.vt = VehicleType.objects.create(name='Sedan', maintenance_interval_days=90, maintenance_interval_km=10000)
        self.vehicle = Vehicle.objects.create(
            license_plate='TST-SAVE',
            vin='3HGBH41JXMN109003',
            make='Test',
            model='Car',
            year=2023,
            vehicle_type=self.vt,
            status='active',
            is_deleted=False,
        )
        self.ts = timezone.now()

    def _add_hot_readings(self):
        for _ in range(3):
            VehicleTelemetry.objects.create(
                vehicle=self.vehicle,
                timestamp=self.ts,
                engine_temperature_c=Decimal('110'),
            )

    @patch('apps.vehicles.services.telemetry_patterns.send_alert_notification_emails')
    def test_creates_alert_and_saves_timeframe(self, mock_email):
        self._add_hot_readings()
        readings = list(VehicleTelemetry.objects.filter(vehicle=self.vehicle).order_by('-timestamp')[:30])
        created = evaluate_and_save_alerts(self.vehicle.pk, readings)
        self.assertGreater(len(created), 0)
        alert = VehicleAlert.objects.filter(vehicle=self.vehicle).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, VehicleAlert.AlertType.HIGH_ENGINE_TEMP)
        self.assertTrue(alert.timeframe_text in ('Inmediato', '') or 'Inmediato' in str(alert.timeframe_text))

    @patch('apps.vehicles.services.telemetry_patterns.send_alert_notification_emails')
    def test_cooldown_prevents_duplicate_same_type(self, mock_email):
        self._add_hot_readings()
        readings = list(VehicleTelemetry.objects.filter(vehicle=self.vehicle).order_by('-timestamp')[:30])
        created1 = evaluate_and_save_alerts(self.vehicle.pk, readings)
        created2 = evaluate_and_save_alerts(self.vehicle.pk, readings)
        self.assertGreater(len(created1), 0)
        self.assertEqual(len(created2), 0)
        self.assertEqual(VehicleAlert.objects.filter(vehicle=self.vehicle).count(), 1)
