"""
ML failure prediction: feature extraction and predictor (optional Scikit-learn model).
"""

from apps.vehicles.ml.features import extract_features
from apps.vehicles.ml.predictor import load_model, predict_alert_types

__all__ = ['extract_features', 'load_model', 'predict_alert_types']
