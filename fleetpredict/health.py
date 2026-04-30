"""Operational health/readiness endpoints."""

import os
import socket
from urllib.parse import urlparse
from django.http import JsonResponse
from django.db import connection
from channels.layers import get_channel_layer


def healthz(_request):
    return JsonResponse({"status": "ok"})


def readyz(_request):
    db_ok = True
    channel_layer_ok = True
    redis_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        db_ok = False
    try:
        channel_layer = get_channel_layer()
        channel_layer_ok = channel_layer is not None
    except Exception:
        channel_layer_ok = False
    if os.environ.get('CHANNEL_LAYERS_USE_REDIS', '').lower() in ('1', 'true', 'yes'):
        redis_url = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
        parsed = urlparse(redis_url)
        try:
            with socket.create_connection((parsed.hostname or '127.0.0.1', parsed.port or 6379), timeout=2):
                redis_ok = True
        except OSError:
            redis_ok = False

    status = 200 if db_ok and channel_layer_ok and redis_ok else 503
    return JsonResponse(
        {
            "status": "ok" if status == 200 else "degraded",
            "database": db_ok,
            "channel_layer": channel_layer_ok,
            "redis": redis_ok,
        },
        status=status,
    )
