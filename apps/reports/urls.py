from django.urls import path
from .views import (
    VehicleReportPDFView,
    FleetReportPDFView,
    ReportsIndexView,
    ReportScheduleCreateView,
    MaintenanceTrendsView,
    CostReportView,
    ComparisonReportView,
    ExportCenterView,
)

app_name = 'reports'

urlpatterns = [
    path('', ReportsIndexView.as_view(), name='index'),
    path('vehicle/<int:vehicle_id>/', VehicleReportPDFView.as_view(), name='vehicle_pdf'),
    path('fleet/', FleetReportPDFView.as_view(), name='fleet_pdf'),
    path('schedules/create/', ReportScheduleCreateView.as_view(), name='schedule_create'),
    path('trends/', MaintenanceTrendsView.as_view(), name='trends'),
    path('cost/', CostReportView.as_view(), name='cost'),
    path('comparison/', ComparisonReportView.as_view(), name='comparison'),
    path('exports/', ExportCenterView.as_view(), name='export_center'),
]
