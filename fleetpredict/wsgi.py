"""
WSGI config for FleetPredict Pro project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fleetpredict.settings')

application = get_wsgi_application()
