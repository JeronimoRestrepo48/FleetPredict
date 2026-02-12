"""
ASGI config for FleetPredict Pro project.
HTTP and WebSocket routing.
WebSocket: no AllowedHostsOriginValidator so simulator and scripts can connect without Origin;
protect ingest in production with TELEMETRY_WS_TOKEN if needed.
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fleetpredict.settings')

django_asgi_app = get_asgi_application()

from fleetpredict.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
