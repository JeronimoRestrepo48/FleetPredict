from django.urls import path
from .views import (
    VehicleReportPDFView,
    FleetReportPDFView,
    ReportsIndexView,
    MaintenanceTrendsView,
    CostReportView,
    ComparisonReportView,
)

app_name = 'reports'

urlpatterns = [
    path('', ReportsIndexView.as_view(), name='index'),
    path('vehicle/<int:vehicle_id>/', VehicleReportPDFView.as_view(), name='vehicle_pdf'),
    path('fleet/', FleetReportPDFView.as_view(), name='fleet_pdf'),
    path('trends/', MaintenanceTrendsView.as_view(), name='trends'),
    path('cost/', CostReportView.as_view(), name='cost'),
    path('comparison/', ComparisonReportView.as_view(), name='comparison'),
]
