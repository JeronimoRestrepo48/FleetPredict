"""
URL configuration for FleetPredict Pro project.
"""

from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from fleetpredict.health import healthz, readyz

urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz/', healthz, name='healthz'),
    path('readyz/', readyz, name='readyz'),
    
    # MVT routes
    path('', include('apps.dashboard.urls')),
    path('', include('apps.users.urls')),
    path('vehicles/', include('apps.vehicles.urls')),
    path('maintenance/', include('apps.maintenance.urls')),
    path('reports/', include('apps.reports.urls')),
    path('routes/', include('apps.routes.urls')),
    path('inventory/', include('apps.inventory.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
