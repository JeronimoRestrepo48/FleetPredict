"""
Evaluate telemetry patterns and produce alerts/recommendations (FR6, FR7, FR9).
Thresholds can be overridden in Django settings (TELEMETRY_PATTERNS_*).
"""

from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from apps.vehicles.models import Vehicle, VehicleTelemetry, VehicleAlert
from apps.vehicles.notifications import send_alert_notification_emails
from apps.maintenance.models import MaintenanceTask


# Default thresholds (override in settings.TELEMETRY_PATTERNS_*)
DEFAULTS = {
    'ENGINE_TEMP_HIGH_C': 105,
    'FUEL_DROP_PCT_PER_WINDOW': 8,
    'FUEL_WINDOW_SIZE': 5,
    'SPEED_VARIANCE_HARSH_KMH': 35,
    'SPEED_WINDOW_SIZE': 4,
    'IDLE_MINUTES_THRESHOLD': 10,
    'IDLE_RPM_MAX': 900,
    'IDLE_SPEED_MAX_KMH': 2,
    'MAINTENANCE_KM_BUFFER': 500,
    'MAINTENANCE_DAYS_BUFFER': 7,
    'ANOMALY_STD_MULTIPLIER': 2.5,
    'ANOMALY_WINDOW_SIZE': 20,
}


def _get_setting(key, default):
    return getattr(settings, f'TELEMETRY_PATTERNS_{key}', default)


def get_recent_telemetry(vehicle_id, limit=30):
    """Fetch recent telemetry for vehicle, ordered by timestamp desc."""
    return list(
        VehicleTelemetry.objects.filter(vehicle_id=vehicle_id)
        .order_by('-timestamp')[:limit]
    )


def _decimal(val):
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _int(val):
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def check_high_engine_temp(readings):
    """Alert if engine_temperature_c exceeds threshold."""
    thresh = _get_setting('ENGINE_TEMP_HIGH_C', DEFAULTS['ENGINE_TEMP_HIGH_C'])
    for r in readings[:5]:
        t = _decimal(r.engine_temperature_c)
        if t is not None and t >= thresh:
            return {
                'type': VehicleAlert.AlertType.HIGH_ENGINE_TEMP,
                'severity': VehicleAlert.Severity.CRITICAL if t >= thresh + 10 else VehicleAlert.Severity.HIGH,
                'message': f'Engine temperature high ({t} °C). Recommend inspection.',
                'confidence': Decimal('0.95'),
                'timeframe_text': 'Inmediato',
            }
    return None


def check_anomalous_fuel(readings):
    """Alert if fuel drops too fast in a short window."""
    window = _get_setting('FUEL_WINDOW_SIZE', DEFAULTS['FUEL_WINDOW_SIZE'])
    drop_thresh = _get_setting('FUEL_DROP_PCT_PER_WINDOW', DEFAULTS['FUEL_DROP_PCT_PER_WINDOW'])
    if len(readings) < window:
        return None
    fuels = [_decimal(r.fuel_level_pct) for r in readings[:window] if _decimal(r.fuel_level_pct) is not None]
    if len(fuels) < 2:
        return None
    drop = fuels[0] - fuels[-1]
    if drop >= drop_thresh:
        return {
            'type': VehicleAlert.AlertType.ANOMALOUS_FUEL,
            'severity': VehicleAlert.Severity.HIGH,
            'message': f'Rapid fuel drop ({drop:.1f}% in window). Possible leak or anomaly.',
            'confidence': Decimal('0.75'),
        }
    return None


def check_harsh_driving(readings):
    """Alert on high speed variance in a short window."""
    window = _get_setting('SPEED_WINDOW_SIZE', DEFAULTS['SPEED_WINDOW_SIZE'])
    var_thresh = _get_setting('SPEED_VARIANCE_HARSH_KMH', DEFAULTS['SPEED_VARIANCE_HARSH_KMH'])
    if len(readings) < window:
        return None
    speeds = [_decimal(r.speed_kmh) or 0 for r in readings[:window]]
    if len(speeds) < 2:
        return None
    mean = sum(speeds) / len(speeds)
    variance = sum((s - mean) ** 2 for s in speeds) / len(speeds)
    std = variance ** 0.5
    if std >= var_thresh:
        return {
            'type': VehicleAlert.AlertType.HARSH_DRIVING,
            'severity': VehicleAlert.Severity.MEDIUM,
            'message': 'Harsh acceleration/braking detected. Consider smoother driving.',
            'confidence': Decimal('0.70'),
        }
    return None


def check_prolonged_idle(readings):
    """Alert if low speed and low rpm for many consecutive readings (proxy for idle time)."""
    idle_rpm = _get_setting('IDLE_RPM_MAX', DEFAULTS['IDLE_RPM_MAX'])
    idle_speed = _get_setting('IDLE_SPEED_MAX_KMH', DEFAULTS['IDLE_SPEED_MAX_KMH'])
    min_count = max(5, _get_setting('IDLE_MINUTES_THRESHOLD', DEFAULTS['IDLE_MINUTES_THRESHOLD']) // 2)
    if len(readings) < min_count:
        return None
    idle_count = 0
    for r in readings:
        rpm = _int(r.rpm)
        speed = _decimal(r.speed_kmh) or 0
        if (rpm is not None and rpm <= idle_rpm) and speed <= idle_speed:
            idle_count += 1
        else:
            idle_count = 0
        if idle_count >= min_count:
            return {
                'type': VehicleAlert.AlertType.PROLONGED_IDLE,
                'severity': VehicleAlert.Severity.LOW,
                'message': 'Prolonged idling detected. Consider reducing engine idle time.',
                'confidence': Decimal('0.80'),
            }
    return None


def check_maintenance_mileage(vehicle, readings):
    """Recommend preventive maintenance when mileage approaches interval."""
    vt = vehicle.vehicle_type
    if not vt:
        return None
    buffer = _get_setting('MAINTENANCE_KM_BUFFER', DEFAULTS['MAINTENANCE_KM_BUFFER'])
    interval = vt.maintenance_interval_km
    mileage = vehicle.current_mileage
    if not mileage or not interval:
        return None
    last_maintenance_mileage = None
    last_task = (
        MaintenanceTask.objects.filter(vehicle=vehicle, status=MaintenanceTask.Status.COMPLETED)
        .order_by('-completion_date')
        .first()
    )
    if last_task and last_task.mileage_at_maintenance is not None:
        last_maintenance_mileage = last_task.mileage_at_maintenance
    next_due = (last_maintenance_mileage or 0) + interval
    if mileage >= next_due - buffer:
        km_left = max(0, next_due - mileage)
        return {
            'type': VehicleAlert.AlertType.MAINTENANCE_MILEAGE,
            'severity': VehicleAlert.Severity.MEDIUM,
            'message': f'Preventive maintenance due soon (next due ~{next_due} km, current {mileage} km).',
            'confidence': Decimal('0.90'),
            'timeframe_text': f'En {km_left} km',
        }
    return None


def check_maintenance_time(vehicle):
    """Recommend preventive maintenance when time since last maintenance approaches interval."""
    vt = vehicle.vehicle_type
    if not vt:
        return None
    buffer_days = _get_setting('MAINTENANCE_DAYS_BUFFER', DEFAULTS['MAINTENANCE_DAYS_BUFFER'])
    interval_days = vt.maintenance_interval_days
    last_task = (
        MaintenanceTask.objects.filter(vehicle=vehicle, status=MaintenanceTask.Status.COMPLETED)
        .order_by('-completion_date')
        .first()
    )
    if not last_task or not last_task.completion_date:
        return None
    since = (timezone.now().date() - last_task.completion_date).days
    if since >= interval_days - buffer_days:
        days_left = max(0, interval_days - since)
        return {
            'type': VehicleAlert.AlertType.MAINTENANCE_TIME,
            'severity': VehicleAlert.Severity.MEDIUM,
            'message': f'Preventive maintenance due by time (interval {interval_days} days, {since} days since last).',
            'confidence': Decimal('0.90'),
            'timeframe_text': f'Próximos {days_left} días',
        }
    return None


def check_statistical_anomaly(readings):
    """Alert if temperature or rpm deviates strongly from recent mean."""
    window = _get_setting('ANOMALY_WINDOW_SIZE', DEFAULTS['ANOMALY_WINDOW_SIZE'])
    k = _get_setting('ANOMALY_STD_MULTIPLIER', DEFAULTS['ANOMALY_STD_MULTIPLIER'])
    if len(readings) < window:
        return None
    temps = [_decimal(r.engine_temperature_c) for r in readings[:window] if _decimal(r.engine_temperature_c) is not None]
    rpms = [_int(r.rpm) for r in readings[:window] if _int(r.rpm) is not None]
    latest = readings[0]
    lt = _decimal(latest.engine_temperature_c)
    lr = _int(latest.rpm)
    if temps and len(temps) >= 5:
        mean_t = sum(temps) / len(temps)
        var_t = sum((x - mean_t) ** 2 for x in temps) / len(temps)
        std_t = var_t ** 0.5
        if std_t > 0 and lt is not None and abs(lt - mean_t) >= k * std_t:
            return {
                'type': VehicleAlert.AlertType.STATISTICAL_ANOMALY,
                'severity': VehicleAlert.Severity.MEDIUM,
                'message': f'Engine temperature anomaly ({lt} °C vs recent mean {mean_t:.1f}).',
                'confidence': Decimal('0.65'),
            }
    if rpms and len(rpms) >= 5 and lr is not None:
        mean_r = sum(rpms) / len(rpms)
        var_r = sum((x - mean_r) ** 2 for x in rpms) / len(rpms)
        std_r = var_r ** 0.5
        if std_r > 0 and abs(lr - mean_r) >= k * std_r:
            return {
                'type': VehicleAlert.AlertType.STATISTICAL_ANOMALY,
                'severity': VehicleAlert.Severity.LOW,
                'message': f'RPM anomaly ({lr} vs recent mean {mean_r:.0f}).',
                'confidence': Decimal('0.60'),
            }
    return None


def evaluate_patterns(vehicle_id, readings=None):
    """
    Run all pattern checks and return list of alert dicts (type, severity, message, confidence).
    If readings is None, fetches recent telemetry from DB.
    """
    from apps.vehicles.models import Vehicle
    vehicle = Vehicle.objects.filter(pk=vehicle_id, is_deleted=False).select_related('vehicle_type').first()
    if not vehicle:
        return []
    if readings is None:
        readings = get_recent_telemetry(vehicle_id)
    if not readings:
        return []

    results = []
    r = check_high_engine_temp(readings)
    if r:
        results.append(r)
    r = check_anomalous_fuel(readings)
    if r:
        results.append(r)
    r = check_harsh_driving(readings)
    if r:
        results.append(r)
    r = check_prolonged_idle(readings)
    if r:
        results.append(r)
    r = check_maintenance_mileage(vehicle, readings)
    if r:
        results.append(r)
    r = check_maintenance_time(vehicle)
    if r:
        results.append(r)
    r = check_statistical_anomaly(readings)
    if r:
        results.append(r)

    return results


def evaluate_and_save_alerts(vehicle_id, readings=None):
    """
    Evaluate patterns and persist new alerts to VehicleAlert.
    Returns list of created alert dicts. Does not create duplicate alerts for same type
    within a short cooldown (e.g. 1 hour) to avoid spam.
    """
    cooldown_minutes = 60
    since = timezone.now() - timedelta(minutes=cooldown_minutes)
    existing_types = set(
        VehicleAlert.objects.filter(vehicle_id=vehicle_id, created_at__gte=since).values_list('alert_type', flat=True)
    )
    alerts = evaluate_patterns(vehicle_id, readings)
    created = []
    for a in alerts:
        if a['type'] in existing_types:
            continue
        alert = VehicleAlert.objects.create(
            vehicle_id=vehicle_id,
            alert_type=a['type'],
            severity=a['severity'],
            message=a['message'],
            confidence=a.get('confidence'),
            timeframe_text=a.get('timeframe_text', ''),
        )
        existing_types.add(a['type'])
        created.append(a)
        if a['severity'] in ('high', 'critical'):
            send_alert_notification_emails(alert)
    return created
