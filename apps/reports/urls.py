from django.urls import path
from .views import VehicleReportPDFView, FleetReportPDFView, ReportsIndexView

app_name = 'reports'

urlpatterns = [
    path('', ReportsIndexView.as_view(), name='index'),
    path('vehicle/<int:vehicle_id>/', VehicleReportPDFView.as_view(), name='vehicle_pdf'),
    path('fleet/', FleetReportPDFView.as_view(), name='fleet_pdf'),
]
