"""
URL patterns for Vehicles app.
"""

from django.urls import path

from .views import (
    VehicleListView,
    VehicleDetailView,
    VehicleCreateView,
    VehicleUpdateView,
    VehicleDeleteView,
    VehicleHistoryView,
)

app_name = 'vehicles'

urlpatterns = [
    path('', VehicleListView.as_view(), name='vehicle_list'),
    path('create/', VehicleCreateView.as_view(), name='vehicle_create'),
    path('<int:pk>/', VehicleDetailView.as_view(), name='vehicle_detail'),
    path('<int:pk>/edit/', VehicleUpdateView.as_view(), name='vehicle_update'),
    path('<int:pk>/delete/', VehicleDeleteView.as_view(), name='vehicle_delete'),
    path('<int:pk>/history/', VehicleHistoryView.as_view(), name='vehicle_history'),
]
