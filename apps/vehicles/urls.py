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
    VehicleHistoryCsvView,
    VehiclesBulkCsvView,
    VehicleTypeListView,
    VehicleTypeCreateView,
    VehicleTypeUpdateView,
    VehicleTypeDeleteView,
    ComplianceListView,
    ComplianceCreateView,
    ComplianceUpdateView,
    ComplianceDeleteView,
    SensorDashboardView,
    SensorManualEntryView,
    SensorCSVUploadView,
    SensorExportCsvView,
    GPSMapView,
    DrivingAnalysisView,
    MileageReportView,
)

app_name = 'vehicles'

urlpatterns = [
    path('', VehicleListView.as_view(), name='vehicle_list'),
    path('export/csv/', VehiclesBulkCsvView.as_view(), name='vehicles_export_csv'),
    path('create/', VehicleCreateView.as_view(), name='vehicle_create'),
    path('types/', VehicleTypeListView.as_view(), name='vehicletype_list'),
    path('types/create/', VehicleTypeCreateView.as_view(), name='vehicletype_create'),
    path('types/<int:pk>/edit/', VehicleTypeUpdateView.as_view(), name='vehicletype_update'),
    path('types/<int:pk>/delete/', VehicleTypeDeleteView.as_view(), name='vehicletype_delete'),
    path('<int:pk>/', VehicleDetailView.as_view(), name='vehicle_detail'),
    path('<int:pk>/edit/', VehicleUpdateView.as_view(), name='vehicle_update'),
    path('<int:pk>/delete/', VehicleDeleteView.as_view(), name='vehicle_delete'),
    path('<int:pk>/history/', VehicleHistoryView.as_view(), name='vehicle_history'),
    path('<int:pk>/history/export/csv/', VehicleHistoryCsvView.as_view(), name='vehicle_history_csv'),
    # FR25 Compliance
    path('compliance/', ComplianceListView.as_view(), name='compliance_list'),
    path('compliance/create/', ComplianceCreateView.as_view(), name='compliance_create'),
    path('compliance/<int:pk>/edit/', ComplianceUpdateView.as_view(), name='compliance_update'),
    path('compliance/<int:pk>/delete/', ComplianceDeleteView.as_view(), name='compliance_delete'),
    # FR18: Sensor Data
    path('<int:pk>/sensors/', SensorDashboardView.as_view(), name='sensor_dashboard'),
    path('<int:pk>/sensors/add/', SensorManualEntryView.as_view(), name='sensor_add'),
    path('<int:pk>/sensors/upload/', SensorCSVUploadView.as_view(), name='sensor_upload'),
    path('<int:pk>/sensors/export/', SensorExportCsvView.as_view(), name='sensor_export'),
    # FR19: GPS and Driving Data
    path('<int:pk>/gps/', GPSMapView.as_view(), name='gps_map'),
    path('<int:pk>/driving/', DrivingAnalysisView.as_view(), name='driving_analysis'),
    path('<int:pk>/mileage/', MileageReportView.as_view(), name='mileage_report'),
]
