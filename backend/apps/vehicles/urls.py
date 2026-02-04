"""
URL patterns for Vehicles app.
"""

from django.urls import path

from .views import (
    VehicleTypeListCreateView,
    VehicleTypeDetailView,
    VehicleListCreateView,
    VehicleDetailView,
    VehicleHistoryView,
)

urlpatterns = [
    # Vehicle Types
    path('types/', VehicleTypeListCreateView.as_view(), name='vehicletype-list'),
    path('types/<int:pk>/', VehicleTypeDetailView.as_view(), name='vehicletype-detail'),
    
    # Vehicles (FR2)
    path('', VehicleListCreateView.as_view(), name='vehicle-list'),
    path('<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    path('<int:pk>/history/', VehicleHistoryView.as_view(), name='vehicle-history'),
]
