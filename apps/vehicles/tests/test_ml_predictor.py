"""Tests for ML failure predictor: feature extraction, load_model, predict_alert_types."""
import numpy as np
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from apps.vehicles.ml.features import extract_features
from apps.vehicles.ml.predictor import load_model, predict_alert_types


class ExtractFeaturesTest(TestCase):
    """Test extract_features returns fixed-size vector and no NaNs."""

    def test_empty_readings_returns_fixed_size_no_nan(self):
        out = extract_features([])
        self.assertIsInstance(out, np.ndarray)
        self.assertEqual(out.ndim, 1)
        self.assertGreater(out.size, 0)
        self.assertFalse(np.any(np.isnan(out)), 'output must not contain NaN')
        self.assertFalse(np.any(np.isinf(out)), 'output must not contain inf')

    def test_mock_readings_returns_expected_length(self):
        # One reading as dict (same keys as VehicleTelemetry)
        readings = [
            {
                'speed_kmh': 50.0,
                'fuel_level_pct': 80.0,
                'engine_temperature_c': 90.0,
                'rpm': 2000,
                'timestamp': None,
            }
        ]
        out = extract_features(readings)
        self.assertIsInstance(out, np.ndarray)
        self.assertEqual(out.ndim, 1)
        self.assertFalse(np.any(np.isnan(out)))
        # Feature count: 4 keys * 4 stats + time_span + n_readings + 2 slopes = 20
        self.assertEqual(out.size, 20)

    def test_object_readings_same_length(self):
        class R:
            def __init__(self, speed=0, fuel=0, temp=0, rpm=0, ts=None):
                self.speed_kmh = speed
                self.fuel_level_pct = fuel
                self.engine_temperature_c = temp
                self.rpm = rpm
                self.timestamp = ts
        readings = [R(50, 80, 90, 2000, None) for _ in range(5)]
        out = extract_features(readings)
        self.assertEqual(out.size, 20)
        self.assertFalse(np.any(np.isnan(out)))


class LoadModelTest(TestCase):
    """Test load_model returns None when file missing."""

    def test_missing_file_returns_none(self):
        with override_settings(ML_FAILURE_PREDICTOR_PATH='/nonexistent/path/model.joblib'):
            # Clear cache so we actually load
            import apps.vehicles.ml.predictor as pred_mod
            pred_mod._CACHED_MODEL = None
            result = load_model()
        self.assertIsNone(result)

    def test_missing_file_no_exception(self):
        with override_settings(ML_FAILURE_PREDICTOR_PATH='/nonexistent/path/model.joblib'):
            import apps.vehicles.ml.predictor as pred_mod
            pred_mod._CACHED_MODEL = None
            try:
                load_model()
            except Exception as e:
                self.fail(f'load_model must not raise when file missing: {e}')


class PredictAlertTypesTest(TestCase):
    """Test predict_alert_types with a mock model."""

    def test_no_model_returns_empty_list(self):
        with patch('apps.vehicles.ml.predictor.load_model', return_value=None):
            result = predict_alert_types([{'speed_kmh': 50}])
        self.assertEqual(result, [])

    def test_mock_model_returns_alert_above_threshold(self):
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])  # normal, high_engine_temp
        mock_model.classes_ = np.array(['normal', 'high_engine_temp'])
        with patch('apps.vehicles.ml.predictor.load_model', return_value=mock_model):
            result = predict_alert_types([{'speed_kmh': 50, 'fuel_level_pct': 80, 'engine_temperature_c': 95, 'rpm': 1500}])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'high_engine_temp')
        self.assertAlmostEqual(result[0][1], 0.8)
        # "normal" must not appear in the list (excluded by design)
        labels = [r[0] for r in result]
        self.assertNotIn('normal', labels)
