"""
Views for PDF report export (FR5 reportes).
Restricted to users with can_view_reports().
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView

from apps.vehicles.models import Vehicle
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
