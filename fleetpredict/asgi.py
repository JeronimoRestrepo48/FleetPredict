"""
ASGI config for FleetPredict Pro project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fleetpredict.settings')

application = get_asgi_application()
