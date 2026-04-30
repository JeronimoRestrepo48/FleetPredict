"""
Views for PDF report export (FR5 reportes) and FR12–15 (trends, cost, comparison).
Restricted to users with can_view_reports().
"""

import csv
from datetime import datetime
from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django.db.models import Count, Sum

from apps.vehicles.models import Vehicle, VehicleAlert, SensorReading, GPSReading
from apps.vehicles.visibility import visible_vehicle_ids, visible_vehicle_queryset
from apps.maintenance.models import MaintenanceTask
from apps.inventory.models import SparePart, Supplier
from apps.dashboard.models import AuditLog
from apps.dashboard.audit import log_audit
from .models import ReportSchedule, ExportJob
from .pdf_utils import generate_vehicle_pdf, generate_fleet_pdf


def _user_vehicle_ids(user):
    return visible_vehicle_ids(user)


class CanViewReportsMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_view_reports()


class VehicleReportPDFView(LoginRequiredMixin, CanViewReportsMixin, View):
    """Export vehicle maintenance report as PDF. User must have access to the vehicle."""

    def get(self, request, vehicle_id):
        vehicle_ids = _user_vehicle_ids(request.user)
        if vehicle_id not in vehicle_ids:
            return HttpResponse('Forbidden', status=403)
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
        pdf_bytes = generate_vehicle_pdf(vehicle)
        if not pdf_bytes:
            return HttpResponse('Error generating PDF. Is pdflatex installed?', status=500)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f'reporte_{vehicle.license_plate.replace(" ", "_")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class FleetReportPDFView(LoginRequiredMixin, CanViewReportsMixin, View):
    """Export fleet summary report as PDF."""

    def get(self, request):
        user = request.user
        qs = visible_vehicle_queryset(user)
        vehicles = list(qs.order_by('license_plate'))
        if not vehicles:
            return HttpResponse('No vehicles to report.', status=404)
        pdf_bytes = generate_fleet_pdf(vehicles)
        if not pdf_bytes:
            return HttpResponse('Error generating PDF. Is pdflatex installed?', status=500)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_flota.pdf"'
        return response


class ReportsIndexView(LoginRequiredMixin, CanViewReportsMixin, TemplateView):
    """Reports landing: fleet PDF download and link to vehicle reports."""
    template_name = 'reports/reports_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schedules'] = ReportSchedule.objects.filter(created_by=self.request.user)[:10]
        context['vehicles'] = visible_vehicle_queryset(self.request.user).order_by('license_plate')
        return context


class ReportScheduleCreateView(LoginRequiredMixin, CanViewReportsMixin, View):
    http_method_names = ['post']

    def post(self, request):
        name = request.POST.get('name', '').strip()
        report_type = request.POST.get('report_type', '').strip()
        frequency = request.POST.get('frequency', 'weekly')
        if not name or report_type not in {'fleet', 'trends', 'cost', 'comparison'}:
            messages.error(request, 'Report schedule requires a name and report type.')
            return redirect('reports:index')
        schedule = ReportSchedule.objects.create(
            name=name,
            report_type=report_type,
            frequency=frequency if frequency in {'weekly', 'monthly'} else 'weekly',
            recipients=request.POST.get('recipients', '').strip(),
            filters={
                'vehicle': request.POST.get('vehicle', ''),
                'start': request.POST.get('start', ''),
                'end': request.POST.get('end', ''),
            },
            created_by=request.user,
        )
        log_audit(request, 'create', 'ReportSchedule', schedule.pk, f'Created report schedule {schedule.name}')
        messages.success(request, 'Report schedule saved.')
        return redirect('reports:index')


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _tasks_queryset(user, request=None):
    qs = MaintenanceTask.objects.filter(status='completed').select_related('vehicle')
    if user.is_driver:
        qs = qs.filter(vehicle__assigned_driver=user)
    if request:
        start = _parse_date(request.GET.get('start'))
        end = _parse_date(request.GET.get('end'))
        vehicle = request.GET.get('vehicle')
        status = request.GET.get('status')
        if start:
            qs = qs.filter(completion_date__gte=start)
        if end:
            qs = qs.filter(completion_date__lte=end)
        if vehicle:
            qs = qs.filter(vehicle_id=vehicle)
        if status:
            qs = qs.filter(status=status)
    return qs


class MaintenanceTrendsView(LoginRequiredMixin, CanViewReportsMixin, TemplateView):
    """FR12: Maintenance trends - completed tasks over time."""
    template_name = 'reports/trends.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = _tasks_queryset(self.request.user, self.request)
        today = timezone.now().date()
        last_90 = today - timedelta(days=90)
        by_month = (
            tasks.filter(completion_date__gte=last_90)
            .values('completion_date__year', 'completion_date__month')
            .annotate(count=Count('id'))
            .order_by('completion_date__year', 'completion_date__month')
        )
        context['by_month'] = list(by_month)
        context['total_completed'] = tasks.filter(completion_date__gte=last_90).count()
        context['vehicles'] = visible_vehicle_queryset(self.request.user).order_by('license_plate')
        return context


class CostReportView(LoginRequiredMixin, CanViewReportsMixin, TemplateView):
    """FR13: Cost report - costs by vehicle and total."""
    template_name = 'reports/cost_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = _tasks_queryset(self.request.user, self.request)
        by_vehicle = (
            tasks.values('vehicle__id', 'vehicle__license_plate', 'vehicle__make', 'vehicle__model')
            .annotate(total=Sum('actual_cost'), count=Count('id'))
            .order_by('-total')
        )
        context['by_vehicle'] = list(by_vehicle)
        context['grand_total'] = tasks.aggregate(s=Sum('actual_cost'))['s'] or 0
        context['vehicles'] = visible_vehicle_queryset(self.request.user).order_by('license_plate')
        return context


class ComparisonReportView(LoginRequiredMixin, CanViewReportsMixin, TemplateView):
    """FR14/15: Comparison - vehicles by maintenance count and cost."""
    template_name = 'reports/comparison.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = _tasks_queryset(self.request.user, self.request)
        by_vehicle = (
            tasks.values('vehicle__id', 'vehicle__license_plate', 'vehicle__make', 'vehicle__model')
            .annotate(total_cost=Sum('actual_cost'), task_count=Count('id'))
            .order_by('-task_count')
        )
        context['by_vehicle'] = list(by_vehicle)
        context['vehicles'] = visible_vehicle_queryset(self.request.user).order_by('license_plate')
        return context


class ExportCenterView(LoginRequiredMixin, CanViewReportsMixin, TemplateView):
    """FR16: centralized export UI and export history."""

    template_name = 'reports/export_center.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['datasets'] = ExportJob.DATASETS
        context['formats'] = ExportJob.FORMATS
        context['vehicles'] = visible_vehicle_queryset(self.request.user).order_by('license_plate')
        context['jobs'] = ExportJob.objects.filter(requested_by=self.request.user)[:20]
        return context

    def post(self, request):
        dataset = request.POST.get('dataset')
        export_format = request.POST.get('export_format', 'csv')
        if dataset not in dict(ExportJob.DATASETS):
            messages.error(request, 'Invalid export dataset.')
            return redirect('reports:export_center')
        if dataset == 'audit' and not request.user.can_manage_platform():
            return HttpResponse('Forbidden', status=403)

        rows, headers = self._build_rows(request, dataset)
        filename = f'{dataset}_export.csv'
        job = ExportJob.objects.create(
            requested_by=request.user,
            dataset=dataset,
            export_format=export_format if export_format in dict(ExportJob.FORMATS) else 'csv',
            filters={k: v for k, v in request.POST.items() if k not in {'csrfmiddlewaretoken'}},
            row_count=len(rows),
            filename=filename,
            expires_at=timezone.now() + timedelta(days=7),
        )
        log_audit(
            request,
            'export',
            'ExportJob',
            job.pk,
            f'Exported {dataset}',
            new_values={'dataset': dataset, 'rows': len(rows), 'format': job.export_format},
        )
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerows(rows)
        return response

    def _build_rows(self, request, dataset):
        vehicle_ids = visible_vehicle_ids(request.user)
        vehicle_filter = request.POST.get('vehicle')
        if vehicle_filter:
            try:
                requested_vehicle = int(vehicle_filter)
            except ValueError:
                requested_vehicle = None
            vehicle_ids = {requested_vehicle} if requested_vehicle in vehicle_ids else set()

        if dataset == 'vehicles':
            qs = visible_vehicle_queryset(request.user).order_by('license_plate')
            return (
                [[v.license_plate, v.vin, v.make, v.model, v.year, v.status, v.current_mileage] for v in qs],
                ['license_plate', 'vin', 'make', 'model', 'year', 'status', 'current_mileage'],
            )
        if dataset == 'maintenance':
            qs = MaintenanceTask.objects.filter(vehicle_id__in=vehicle_ids).select_related('vehicle')
            return (
                [[t.vehicle.license_plate, t.title, t.maintenance_type, t.status, t.scheduled_date, t.completion_date, t.actual_cost] for t in qs],
                ['vehicle', 'title', 'type', 'status', 'scheduled_date', 'completion_date', 'actual_cost'],
            )
        if dataset == 'predictions':
            qs = VehicleAlert.objects.filter(vehicle_id__in=vehicle_ids).select_related('vehicle')
            return (
                [[a.vehicle.license_plate, a.alert_type, a.severity, a.confidence, a.timeframe_text, a.message, a.created_at] for a in qs],
                ['vehicle', 'type', 'severity', 'confidence', 'timeframe', 'message', 'created_at'],
            )
        if dataset == 'inventory':
            qs = SparePart.objects.all()
            return (
                [[p.part_number, p.name, p.category, p.current_stock, p.reorder_point, p.unit_cost] for p in qs],
                ['part_number', 'name', 'category', 'current_stock', 'reorder_point', 'unit_cost'],
            )
        if dataset == 'suppliers':
            qs = Supplier.objects.all()
            return (
                [[s.name, s.contact_name, s.email, s.phone, s.delivery_terms, s.rating_avg, s.rating_count] for s in qs],
                ['name', 'contact', 'email', 'phone', 'delivery_terms', 'rating_avg', 'rating_count'],
            )
        if dataset == 'sensors':
            qs = SensorReading.objects.filter(vehicle_id__in=vehicle_ids).select_related('vehicle')
            return (
                [[r.vehicle.license_plate, r.sensor_type, r.value, r.timestamp, r.source] for r in qs],
                ['vehicle', 'sensor_type', 'value', 'timestamp', 'source'],
            )
        if dataset == 'gps':
            qs = GPSReading.objects.filter(vehicle_id__in=vehicle_ids).select_related('vehicle')
            return (
                [[r.vehicle.license_plate, r.latitude, r.longitude, r.speed_kmh, r.timestamp] for r in qs],
                ['vehicle', 'latitude', 'longitude', 'speed_kmh', 'timestamp'],
            )
        qs = AuditLog.objects.select_related('user')
        return (
            [[e.created_at, e.user.email if e.user else '', e.action, e.model_name, e.object_id, e.message, e.ip_address] for e in qs],
            ['created_at', 'user', 'action', 'model', 'object_id', 'message', 'ip_address'],
        )
