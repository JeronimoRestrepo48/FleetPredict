"""
Views for PDF report export (FR5 reportes) and FR12–15 (trends, cost, comparison).
Restricted to users with can_view_reports().
"""

from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django.db.models import Count, Sum

from apps.vehicles.models import Vehicle
from apps.maintenance.models import MaintenanceTask
from .pdf_utils import generate_vehicle_pdf, generate_fleet_pdf


def _user_vehicle_ids(user):
    qs = Vehicle.objects.filter(is_deleted=False)
    if user.is_driver:
        qs = qs.filter(assigned_driver=user)
    return set(qs.values_list('id', flat=True))


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
        qs = Vehicle.objects.filter(is_deleted=False)
        if user.is_driver:
            qs = qs.filter(assigned_driver=user)
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


def _tasks_queryset(user):
    qs = MaintenanceTask.objects.filter(status='completed').select_related('vehicle')
    if user.is_driver:
        qs = qs.filter(vehicle__assigned_driver=user)
    return qs


class MaintenanceTrendsView(LoginRequiredMixin, CanViewReportsMixin, TemplateView):
    """FR12: Maintenance trends - completed tasks over time."""
    template_name = 'reports/trends.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = _tasks_queryset(self.request.user)
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
        return context


class CostReportView(LoginRequiredMixin, CanViewReportsMixin, TemplateView):
    """FR13: Cost report - costs by vehicle and total."""
    template_name = 'reports/cost_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = _tasks_queryset(self.request.user)
        by_vehicle = (
            tasks.values('vehicle__id', 'vehicle__license_plate', 'vehicle__make', 'vehicle__model')
            .annotate(total=Sum('actual_cost'), count=Count('id'))
            .order_by('-total')
        )
        context['by_vehicle'] = list(by_vehicle)
        context['grand_total'] = tasks.aggregate(s=Sum('actual_cost'))['s'] or 0
        return context


class ComparisonReportView(LoginRequiredMixin, CanViewReportsMixin, TemplateView):
    """FR14/15: Comparison - vehicles by maintenance count and cost."""
    template_name = 'reports/comparison.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = _tasks_queryset(self.request.user)
        by_vehicle = (
            tasks.values('vehicle__id', 'vehicle__license_plate', 'vehicle__make', 'vehicle__model')
            .annotate(total_cost=Sum('actual_cost'), task_count=Count('id'))
            .order_by('-task_count')
        )
        context['by_vehicle'] = list(by_vehicle)
        return context
