"""
Feature extraction for ML failure prediction.
Single contract used by both dataset building and inference.
"""

import numpy as np
from django.conf import settings


# Window size: same for training and inference (from settings or constant)
def _window_size():
    return getattr(settings, 'ML_WINDOW_SIZE', 20)


def _numeric(r, key, default=0.0):
    """Get numeric value from a reading (model instance or dict)."""
    if hasattr(r, key):
        val = getattr(r, key, None)
    elif isinstance(r, dict):
        val = r.get(key)
    else:
        return default
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _timestamp(r):
    """Get timestamp from a reading for time span and trend."""
    if hasattr(r, 'timestamp'):
        ts = getattr(r, 'timestamp', None)
    elif isinstance(r, dict):
        ts = r.get('timestamp')
    else:
        return None
    if ts is None:
        return None
    try:
        return float(ts.timestamp()) if hasattr(ts, 'timestamp') else float(ts)
    except (TypeError, ValueError):
        return None


def _agg(values, fill=0.0):
    """Return (mean, std, min, max) for a list of floats; use fill for empty."""
    arr = np.array(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return fill, fill, fill, fill
    return float(np.mean(arr)), float(np.std(arr)) if arr.size > 1 else 0.0, float(np.min(arr)), float(np.max(arr))


def _slope(x, y):
    """Simple linear slope (y over x). Returns 0 if not enough points."""
    if len(x) < 2 or len(y) < 2 or len(x) != len(y):
        return 0.0
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    finite = np.isfinite(x) & np.isfinite(y)
    if np.sum(finite) < 2:
        return 0.0
    x, y = x[finite], y[finite]
    A = np.vstack([x, np.ones(len(x))]).T
    try:
        slope, _ = np.linalg.lstsq(A, y, rcond=None)[0]
        return float(slope)
    except Exception:
        return 0.0


def extract_features(readings):
    """
    Build a fixed-size feature vector from a window of readings (ordered by timestamp desc).
    Used by both build_ml_dataset and the predictor at inference.
    Input: list of VehicleTelemetry or dicts with same keys (e.g. speed_kmh, fuel_level_pct,
           engine_temperature_c, rpm, timestamp). Only the first ML_WINDOW_SIZE readings are used.
    Output: 1D numpy array of shape (n_features,) with no NaNs (missing values filled with 0).
    """
    W = _window_size()
    window = (readings or [])[:W]
    fill = 0.0

    keys = ['speed_kmh', 'fuel_level_pct', 'engine_temperature_c', 'rpm']
    features = []
    for key in keys:
        values = [_numeric(r, key, None) for r in window]
        values = [v if v is not None else fill for v in values]
        if not values:
            features.extend([fill, fill, fill, fill])
        else:
            mean, std, mn, mx = _agg(values, fill)
            features.extend([mean, std, mn, mx])

    # Time span (seconds between first and last reading) and number of readings
    timestamps = [_timestamp(r) for r in window]
    timestamps = [t for t in timestamps if t is not None]
    if len(timestamps) >= 2:
        time_span = max(timestamps) - min(timestamps)
    else:
        time_span = fill
    features.append(time_span)
    features.append(float(len(window)))

    # Optional: simple trend (slope of temperature and fuel over time)
    if len(timestamps) >= 2 and len(window) >= 2:
        temps = [_numeric(r, 'engine_temperature_c') for r in window]
        fuels = [_numeric(r, 'fuel_level_pct') for r in window]
        # Order by time ascending for slope (window is desc, so reverse)
        ts_asc = timestamps[::-1] if len(timestamps) == len(window) else list(range(len(window)))
        temp_slope = _slope(ts_asc[: len(temps)], temps)
        fuel_slope = _slope(ts_asc[: len(fuels)], fuels)
    else:
        temp_slope = fill
        fuel_slope = fill
    features.append(temp_slope)
    features.append(fuel_slope)

    out = np.array(features, dtype=np.float64)
    np.nan_to_num(out, copy=False, nan=fill, posinf=fill, neginf=fill)
    return out
