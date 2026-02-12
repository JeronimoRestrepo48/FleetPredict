"""
ML failure predictor: load joblib pipeline and predict alert types from telemetry window.
"""

from django.conf import settings

from apps.vehicles.ml.features import extract_features


_CACHED_MODEL = None


def load_model():
    """
    Load the failure predictor pipeline from ML_FAILURE_PREDICTOR_PATH.
    Returns the pipeline (scaler + classifier) or None if file missing/invalid.
    """
    global _CACHED_MODEL
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL
    path = getattr(settings, 'ML_FAILURE_PREDICTOR_PATH', None)
    if not path:
        return None
    try:
        import joblib
        import os
        if not os.path.isfile(path):
            return None
        _CACHED_MODEL = joblib.load(path)
        return _CACHED_MODEL
    except Exception:
        return None


def predict_alert_types(readings):
    """
    Run the loaded model on a window of readings. Returns list of (alert_type, confidence)
    for classes above ML_PREDICTION_CONFIDENCE_THRESHOLD, excluding "normal", sorted by probability desc.
    If no model is loaded, returns [].
    """
    model = load_model()
    if model is None:
        return []
    threshold = getattr(settings, 'ML_PREDICTION_CONFIDENCE_THRESHOLD', 0.5)
    x = extract_features(readings).reshape(1, -1)
    try:
        proba = model.predict_proba(x)[0]
        classes = model.classes_
    except Exception:
        return []
    out = []
    for i, cls in enumerate(classes):
        if str(cls).lower() == 'normal':
            continue
        p = float(proba[i])
        if p >= threshold:
            out.append((cls, p))
    out.sort(key=lambda t: -t[1])
    return out
