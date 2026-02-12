"""
WebSocket consumer for vehicle telemetry.
Accepts JSON messages with vehicle_id or license_plate and telemetry fields;
saves VehicleTelemetry and updates Vehicle.current_mileage and last_telemetry_at.
Optional auth via query string token (TELEMETRY_WS_TOKEN in settings).
"""

import json
import logging
from decimal import Decimal
from datetime import datetime

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone

from .models import Vehicle, VehicleTelemetry
from .services.telemetry_patterns import evaluate_and_save_alerts

logger = logging.getLogger(__name__)


def _get_vehicle(vehicle_id=None, license_plate=None, vin=None):
    """Resolve vehicle by id, license_plate, or vin. Returns None if not found or deleted."""
    qs = Vehicle.objects.filter(is_deleted=False)
    if vehicle_id is not None:
        return qs.filter(pk=vehicle_id).first()
    if license_plate:
        return qs.filter(license_plate=license_plate).first()
    if vin:
        return qs.filter(vin=vin).first()
    return None


def _save_telemetry(vehicle, payload):
    """Create VehicleTelemetry and update Vehicle.current_mileage and last_telemetry_at."""
    ts = payload.get('timestamp')
    if ts is None:
        ts = timezone.now()
    elif isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except Exception:
            ts = timezone.now()
    if timezone.is_naive(ts):
        ts = timezone.make_aware(ts)

    def _decimal(v):
        if v is None:
            return None
        try:
            return Decimal(str(v))
        except Exception:
            return None

    def _int(v):
        if v is None:
            return None
        try:
            return int(v)
        except Exception:
            return None

    def _bool(v):
        if v is None:
            return None
        return bool(v)

    telemetry = VehicleTelemetry(
        vehicle=vehicle,
        timestamp=ts,
        speed_kmh=_decimal(payload.get('speed_kmh')),
        fuel_level_pct=_decimal(payload.get('fuel_level_pct')),
        engine_temperature_c=_decimal(payload.get('engine_temperature_c')),
        latitude=_decimal(payload.get('latitude') or payload.get('lat')),
        longitude=_decimal(payload.get('longitude') or payload.get('lng')),
        rpm=_int(payload.get('rpm')),
        mileage=_int(payload.get('mileage')),
        voltage=_decimal(payload.get('voltage')),
        throttle_pct=_decimal(payload.get('throttle_pct')),
        brake_status=_bool(payload.get('brake_status')),
    )
    telemetry.save()

    # Update vehicle current_mileage and last_telemetry_at
    if telemetry.mileage is not None and telemetry.mileage > vehicle.current_mileage:
        vehicle.current_mileage = telemetry.mileage
    vehicle.last_telemetry_at = ts
    vehicle.save(update_fields=['current_mileage', 'last_telemetry_at', 'updated_at'])

    # Evaluate patterns and persist alerts (FR6, FR7, FR9)
    readings = list(
        VehicleTelemetry.objects.filter(vehicle=vehicle).order_by('-timestamp')[:30]
    )
    evaluate_and_save_alerts(vehicle.pk, readings)
    return telemetry


def _telemetry_payload_for_broadcast(vehicle, payload, ts):
    """Build JSON-serializable dict for WebSocket broadcast (native types only)."""
    def _f(v):
        if v is None:
            return None
        if hasattr(v, '__float__'):
            return float(v)
        return v
    return {
        'vehicle_id': vehicle.pk,
        'timestamp': ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
        'speed_kmh': _f(payload.get('speed_kmh')),
        'fuel_level_pct': _f(payload.get('fuel_level_pct')),
        'engine_temperature_c': _f(payload.get('engine_temperature_c')),
        'latitude': _f(payload.get('latitude') or payload.get('lat')),
        'longitude': _f(payload.get('longitude') or payload.get('lng')),
        'rpm': int(payload.get('rpm')) if payload.get('rpm') is not None else None,
        'mileage': int(payload.get('mileage')) if payload.get('mileage') is not None else None,
        'voltage': _f(payload.get('voltage')),
        'throttle_pct': _f(payload.get('throttle_pct')),
        'brake_status': bool(payload.get('brake_status')) if payload.get('brake_status') is not None else None,
    }


class TelemetryConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for receiving vehicle telemetry JSON messages."""

    async def connect(self):
        self.vehicle = None
        # Optional token auth from query string
        token = None
        qs = self.scope.get('query_string', b'').decode()
        for part in qs.split('&'):
            if '=' in part:
                key, value = part.split('=', 1)
                if key.strip() == 'token' and value.strip():
                    token = value.strip()
                    break
        from django.conf import settings
        expected = getattr(settings, 'TELEMETRY_WS_TOKEN', None)
        if expected and token != expected:
            await self.close(code=4001)
            return
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            await self.send(text_data=json.dumps({'ok': False, 'error': 'Expected JSON text'}))
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            await self.send(text_data=json.dumps({'ok': False, 'error': f'Invalid JSON: {e}'}))
            return

        vehicle_id = data.get('vehicle_id')
        license_plate = data.get('license_plate')
        vin = data.get('vin')
        vehicle = await sync_to_async(_get_vehicle)(
            vehicle_id=vehicle_id,
            license_plate=license_plate,
            vin=vin,
        )
        if not vehicle:
            await self.send(text_data=json.dumps({
                'ok': False,
                'error': 'Vehicle not found or deleted',
                'vehicle_id': vehicle_id,
                'license_plate': license_plate,
            }))
            return

        try:
            telemetry = await sync_to_async(_save_telemetry)(vehicle, data)
        except Exception as e:
            logger.exception('Telemetry save error')
            await self.send(text_data=json.dumps({'ok': False, 'error': str(e)}))
            return

        # Broadcast to subscribers (browser vehicle detail page)
        payload_broadcast = _telemetry_payload_for_broadcast(vehicle, data, telemetry.timestamp)
        group_name = f'telemetry_vehicle_{vehicle.pk}'
        await self.channel_layer.group_send(
            group_name,
            {'type': 'telemetry_update', 'payload': payload_broadcast},
        )
        await self.send(text_data=json.dumps({'ok': True, 'ack': True}))


def _user_can_subscribe_vehicle(user, vehicle_id):
    """Return True if user is authenticated and can access this vehicle (driver sees only assigned)."""
    if not user or not getattr(user, 'is_authenticated', True) or not user.is_authenticated:
        return False
    vehicle = Vehicle.objects.filter(pk=vehicle_id, is_deleted=False).first()
    if not vehicle:
        return False
    if getattr(user, 'is_driver', False):
        return vehicle.assigned_driver_id == user.pk
    return True


class TelemetrySubscribeConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for browser: subscribe to live telemetry for one vehicle."""

    async def connect(self):
        self.vehicle_id = self.scope.get('url_route', {}).get('kwargs', {}).get('vehicle_id')
        user = self.scope.get('user')
        if self.vehicle_id is None:
            await self.close(code=4000)
            return
        can = await sync_to_async(_user_can_subscribe_vehicle)(user, self.vehicle_id)
        if not can:
            await self.close(code=4003)
            return
        self.room_group_name = f'telemetry_vehicle_{self.vehicle_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def telemetry_update(self, event):
        """Called when ingest consumer broadcasts to this group."""
        payload = event.get('payload', {})
        await self.send(text_data=json.dumps(payload))
