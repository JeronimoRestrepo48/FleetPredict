"""Operational health/readiness endpoints."""

from django.http import JsonResponse
from django.db import connection
from channels.layers import get_channel_layer


def healthz(_request):
    return JsonResponse({"status": "ok"})


def readyz(_request):
    db_ok = True
    channel_layer_ok = True
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

    status = 200 if db_ok and channel_layer_ok else 503
    return JsonResponse(
        {
            "status": "ok" if status == 200 else "degraded",
            "database": db_ok,
            "channel_layer": channel_layer_ok,
        },
        status=status,
    )
