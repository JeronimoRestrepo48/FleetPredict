"""
ASGI routing: WebSocket URLs.
"""

from django.urls import path
from apps.vehicles.consumers import TelemetryConsumer, TelemetrySubscribeConsumer

websocket_urlpatterns = [
    path('ws/telemetry/', TelemetryConsumer.as_asgi()),
    path('ws/telemetry/subscribe/<int:vehicle_id>/', TelemetrySubscribeConsumer.as_asgi()),
]
