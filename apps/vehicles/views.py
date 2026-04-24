"""
Views for Vehicles app.
Implements FR2: Vehicle registry.
Uses Django MVT - template rendering.
"""

import csv
import io

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
)
from django.db.models import Q

from apps.dashboard.audit import log_audit
from .models import (
    Vehicle, VehicleType, VehicleTelemetry, ComplianceRequirement,
    SensorReading, GPSReading, DrivingPattern,
)
from .forms import (
    VehicleForm, VehicleTypeForm, ComplianceRequirementForm,
    SensorReadingForm, SensorCSVUploadForm,
)


class CanManageVehiclesMixin(UserPassesTestMixin):
    """Mixin that requires user to be admin or fleet manager."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_vehicles()


class AdminRequiredMixin(UserPassesTestMixin):
    """FR22: Only administrators can manage vehicle types."""

    def test_func(self):
        return self.request.user.is_authenticated and getattr(
            self.request.user, 'role', None
        ) == 'administrator'


# ============== Vehicle Views ==============

class VehicleListView(LoginRequiredMixin, ListView):
    """List vehicles with filters and pagination."""

    model = Vehicle
    template_name = 'vehicles/vehicle_list.html'
    context_object_name = 'vehicles'
    paginate_by = 20

    def get_paginate_by(self, queryset):
        per = self.request.GET.get('per_page', '20')
        if per in ('10', '20', '50'):
            return int(per)
        return 20

    def get_queryset(self):
        user = self.request.user
        queryset = Vehicle.objects.filter(is_deleted=False)
        if user.is_driver:
            queryset = queryset.filter(assigned_driver=user)
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(license_plate__icontains=search) |
                Q(vin__icontains=search) |
                Q(make__icontains=search) |
                Q(model__icontains=search)
            )
        queryset = queryset.order_by('-created_at')
        # FR6: filter by health (green/yellow/red) - health is computed per vehicle
        health_filter = self.request.GET.get('health')
        if health_filter and health_filter in ('green', 'yellow', 'red'):
            matching_ids = [v.id for v in queryset if v.get_health_status() == health_filter]
            queryset = queryset.filter(id__in=matching_ids)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_manage'] = self.request.user.can_manage_vehicles()
        context['status_choices'] = Vehicle.Status.choices
        context['health_choices'] = [('green', 'Buena'), ('yellow', 'Precaución'), ('red', 'Crítica')]
        return context


class VehicleDetailView(LoginRequiredMixin, DetailView):
    """Vehicle detail view."""

    model = Vehicle
    template_name = 'vehicles/vehicle_detail.html'
    context_object_name = 'vehicle'

    def get_queryset(self):
        user = self.request.user
        queryset = Vehicle.objects.filter(is_deleted=False)
        if user.is_driver:
            queryset = queryset.filter(assigned_driver=user)
        return queryset

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        context = super().get_context_data(**kwargs)
        context['can_manage'] = self.request.user.can_manage_vehicles()
        last = (
            VehicleTelemetry.objects.filter(vehicle=self.object)
            .order_by('-timestamp')
            .first()
        )
        context['last_telemetry'] = last
        # Initial engine on/off: telemetry in last 90s and (speed>0 or rpm>0)
        if last and last.timestamp:
            delta_sec = (timezone.now() - last.timestamp).total_seconds()
            speed = float(last.speed_kmh or 0)
            rpm = int(last.rpm or 0)
            context['vehicle_engine_on_initial'] = delta_sec < 90 and (speed > 0 or rpm > 0)
        else:
            context['vehicle_engine_on_initial'] = False
        status, reasons = self.object.get_health_status_reasons()
        context['health_status'] = status
        context['health_reasons'] = reasons
        context['compliance_requirements'] = self.object.compliance_requirements.all().order_by('expiration_date')
        return context


class VehicleCreateView(LoginRequiredMixin, CanManageVehiclesMixin, CreateView):
    """Create vehicle."""

    model = Vehicle
    form_class = VehicleForm
    template_name = 'vehicles/vehicle_form.html'
    success_url = reverse_lazy('vehicles:vehicle_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        log_audit(self.request, 'create', 'Vehicle', self.object.pk, f'Vehicle {self.object.license_plate} created')
        messages.success(self.request, 'Vehicle created successfully.')
        return response


class VehicleUpdateView(LoginRequiredMixin, CanManageVehiclesMixin, UpdateView):
    """Update vehicle."""

    model = Vehicle
    form_class = VehicleForm
    template_name = 'vehicles/vehicle_form.html'
    context_object_name = 'vehicle'

    def get_queryset(self):
        return Vehicle.objects.filter(is_deleted=False)

    def get_success_url(self):
        return reverse_lazy('vehicles:vehicle_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit(self.request, 'update', 'Vehicle', self.object.pk, f'Vehicle {self.object.license_plate} updated')
        messages.success(self.request, 'Vehicle updated successfully.')
        return response


class VehicleDeleteView(LoginRequiredMixin, CanManageVehiclesMixin, DeleteView):
    """Soft delete vehicle."""

    model = Vehicle
    template_name = 'vehicles/vehicle_confirm_delete.html'
    context_object_name = 'vehicle'
    success_url = reverse_lazy('vehicles:vehicle_list')

    def get_queryset(self):
        return Vehicle.objects.filter(is_deleted=False)

    def form_valid(self, form):
        log_audit(self.request, 'delete', 'Vehicle', self.object.pk, f'Vehicle {self.object.license_plate} deleted')
        self.object.soft_delete()
        messages.success(self.request, 'Vehicle deleted successfully.')
        return redirect(self.success_url)


class VehicleHistoryView(LoginRequiredMixin, DetailView):
    """Vehicle maintenance history."""

    model = Vehicle
    template_name = 'vehicles/vehicle_history.html'
    context_object_name = 'vehicle'

    def get_queryset(self):
        user = self.request.user
        queryset = Vehicle.objects.filter(is_deleted=False)
        if user.is_driver:
            queryset = queryset.filter(assigned_driver=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.maintenance_tasks.filter(
            status='completed'
        ).order_by('-completion_date')
        return context


class VehiclesBulkCsvView(LoginRequiredMixin, CanManageVehiclesMixin, View):
    """FR16: Bulk export vehicles as CSV."""

    def get(self, request):
        user = request.user
        qs = Vehicle.objects.filter(is_deleted=False)
        if user.is_driver:
            qs = qs.filter(assigned_driver=user)
        qs = qs.select_related('vehicle_type', 'assigned_driver').order_by('license_plate')
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            'License plate', 'VIN', 'Make', 'Model', 'Year', 'Type', 'Status',
            'Current mileage', 'Fuel type', 'Assigned driver',
        ])
        for v in qs:
            writer.writerow([
                v.license_plate,
                v.vin,
                v.make,
                v.model,
                v.year,
                v.vehicle_type.name if v.vehicle_type else '',
                v.get_status_display(),
                v.current_mileage or '',
                v.fuel_type or '',
                v.assigned_driver.get_full_name() if v.assigned_driver else '',
            ])
        response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="vehicles_export.csv"'
        return response


class VehicleHistoryCsvView(LoginRequiredMixin, View):
    """Export vehicle maintenance history as CSV. Same access as VehicleHistoryView."""

    def get(self, request, pk):
        user = request.user
        queryset = Vehicle.objects.filter(is_deleted=False)
        if user.is_driver:
            queryset = queryset.filter(assigned_driver=user)
        vehicle = get_object_or_404(queryset, pk=pk)
        tasks = vehicle.maintenance_tasks.filter(
            status='completed'
        ).order_by('-completion_date')
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            'Task', 'Type', 'Scheduled date', 'Completed date', 'Cost', 'Mileage', 'Notes'
        ])
        for t in tasks:
            writer.writerow([
                t.title,
                t.get_maintenance_type_display() if t.maintenance_type else '',
                t.scheduled_date.isoformat() if t.scheduled_date else '',
                t.completion_date.isoformat() if t.completion_date else '',
                str(t.actual_cost) if t.actual_cost is not None else '',
                str(t.mileage_at_maintenance) if t.mileage_at_maintenance is not None else '',
                (t.completion_notes or '')[:500],
            ])
        response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
        filename = f'history_{vehicle.license_plate.replace(" ", "_")}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ============== Vehicle Type Views ==============

class VehicleTypeListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List vehicle types. Admin only."""

    model = VehicleType
    template_name = 'vehicles/vehicletype_list.html'
    context_object_name = 'vehicle_types'


class VehicleTypeCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Create vehicle type. Admin only."""

    model = VehicleType
    form_class = VehicleTypeForm
    template_name = 'vehicles/vehicletype_form.html'
    success_url = reverse_lazy('vehicles:vehicletype_list')

    def form_valid(self, form):
        messages.success(self.request, 'Vehicle type created successfully.')
        return super().form_valid(form)


class VehicleTypeUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Edit vehicle type. Admin only."""

    model = VehicleType
    form_class = VehicleTypeForm
    template_name = 'vehicles/vehicletype_form.html'
    context_object_name = 'vehicle_type'
    success_url = reverse_lazy('vehicles:vehicletype_list')

    def form_valid(self, form):
        messages.success(self.request, 'Vehicle type updated successfully.')
        return super().form_valid(form)


class VehicleTypeDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete vehicle type. Admin only. Fails if vehicles use this type."""

    model = VehicleType
    template_name = 'vehicles/vehicletype_confirm_delete.html'
    context_object_name = 'vehicle_type'
    success_url = reverse_lazy('vehicles:vehicletype_list')

    def form_valid(self, form):
        if self.object.vehicles.exists():
            messages.error(
                self.request,
                'Cannot delete: some vehicles use this type. Reassign them first.',
            )
            return redirect('vehicles:vehicletype_list')
        messages.success(self.request, 'Vehicle type deleted.')
        return super().form_valid(form)


# ============== Compliance Requirements ==============

class ComplianceListView(LoginRequiredMixin, CanManageVehiclesMixin, ListView):
    """Fleet-wide compliance list with filters (type, status)."""

    model = ComplianceRequirement
    template_name = 'vehicles/compliance_list.html'
    context_object_name = 'compliance_list'
    paginate_by = 25

    def get_queryset(self):
        from datetime import timedelta
        from django.utils import timezone
        qs = ComplianceRequirement.objects.select_related('vehicle').order_by('expiration_date')
        req_type = self.request.GET.get('type')
        if req_type:
            qs = qs.filter(requirement_type=req_type)
        status = self.request.GET.get('status')
        today = timezone.now().date()
        if status == 'expired':
            qs = qs.filter(expiration_date__lt=today)
        elif status == 'expiring':
            qs = qs.filter(
                expiration_date__gte=today,
                expiration_date__lte=today + timedelta(days=30),
            )
        elif status == 'ok':
            qs = qs.filter(expiration_date__gt=today + timedelta(days=30))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_choices'] = ComplianceRequirement.Type.choices
        return context


class ComplianceCreateView(LoginRequiredMixin, CanManageVehiclesMixin, CreateView):
    """Create compliance requirement. Supports ?vehicle=<pk>."""

    model = ComplianceRequirement
    form_class = ComplianceRequirementForm
    template_name = 'vehicles/compliance_form.html'
    success_url = reverse_lazy('vehicles:compliance_list')

    def get_initial(self):
        initial = super().get_initial()
        vehicle_id = self.request.GET.get('vehicle')
        if vehicle_id:
            initial['vehicle'] = vehicle_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Compliance requirement added.')
        return super().form_valid(form)


class ComplianceUpdateView(LoginRequiredMixin, CanManageVehiclesMixin, UpdateView):
    """Edit compliance requirement."""

    model = ComplianceRequirement
    form_class = ComplianceRequirementForm
    template_name = 'vehicles/compliance_form.html'
    context_object_name = 'compliance'
    success_url = reverse_lazy('vehicles:compliance_list')

    def form_valid(self, form):
        messages.success(self.request, 'Compliance requirement updated.')
        return super().form_valid(form)


class ComplianceDeleteView(LoginRequiredMixin, CanManageVehiclesMixin, DeleteView):
    """Delete compliance requirement."""

    model = ComplianceRequirement
    template_name = 'vehicles/compliance_confirm_delete.html'
    context_object_name = 'compliance'
    success_url = reverse_lazy('vehicles:compliance_list')

    def form_valid(self, form):
        messages.success(self.request, 'Compliance requirement removed.')
        return super().form_valid(form)


# ============== FR18: Sensor Data Integration ==============

class SensorDashboardView(LoginRequiredMixin, DetailView):
    model = Vehicle
    template_name = 'vehicles/sensor_dashboard.html'
    context_object_name = 'vehicle'

    def get_queryset(self):
        qs = Vehicle.objects.filter(is_deleted=False)
        if self.request.user.is_driver:
            qs = qs.filter(assigned_driver=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        from datetime import timedelta
        import json
        ctx = super().get_context_data(**kwargs)
        days = int(self.request.GET.get('days', 7))
        since = timezone.now() - timedelta(days=days)
        sensor_type = self.request.GET.get('sensor_type', '')
        qs = self.object.sensor_readings.filter(timestamp__gte=since)
        if sensor_type:
            qs = qs.filter(sensor_type=sensor_type)
        readings = list(qs.order_by('timestamp').values('sensor_type', 'value', 'timestamp'))
        chart_data = {}
        for r in readings:
            st = r['sensor_type']
            chart_data.setdefault(st, {'labels': [], 'values': []})
            chart_data[st]['labels'].append(r['timestamp'].strftime('%Y-%m-%d %H:%M'))
            chart_data[st]['values'].append(float(r['value']))
        ctx['chart_data_json'] = json.dumps(chart_data)
        ctx['sensor_types'] = SensorReading.SensorType.choices
        ctx['selected_days'] = days
        ctx['selected_sensor_type'] = sensor_type
        return ctx


class SensorManualEntryView(LoginRequiredMixin, CanManageVehiclesMixin, CreateView):
    model = SensorReading
    form_class = SensorReadingForm
    template_name = 'vehicles/sensor_form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['vehicle'] = self.kwargs.get('pk')
        initial['source'] = 'manual'
        return initial

    def form_valid(self, form):
        form.instance.source = 'manual'
        messages.success(self.request, 'Sensor reading added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('vehicles:sensor_dashboard', kwargs={'pk': self.object.vehicle_id})


class SensorCSVUploadView(LoginRequiredMixin, CanManageVehiclesMixin, View):
    def get(self, request, pk):
        vehicle = get_object_or_404(Vehicle.objects.filter(is_deleted=False), pk=pk)
        form = SensorCSVUploadForm(initial={'vehicle': vehicle.pk})
        return self._render(request, form, vehicle)

    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle.objects.filter(is_deleted=False), pk=pk)
        form = SensorCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            decoded = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            count = 0
            from django.utils.dateparse import parse_datetime
            for row in reader:
                ts = parse_datetime(row.get('timestamp', ''))
                if ts and row.get('sensor_type') and row.get('value'):
                    SensorReading.objects.create(
                        vehicle=vehicle,
                        sensor_type=row['sensor_type'].strip(),
                        value=row['value'].strip(),
                        timestamp=ts,
                        source='csv',
                    )
                    count += 1
            messages.success(request, f'{count} sensor readings imported.')
            return redirect('vehicles:sensor_dashboard', pk=vehicle.pk)
        return self._render(request, form, vehicle)

    def _render(self, request, form, vehicle):
        from django.template.response import TemplateResponse
        return TemplateResponse(request, 'vehicles/sensor_upload.html', {
            'form': form, 'vehicle': vehicle,
        })


class SensorExportCsvView(LoginRequiredMixin, View):
    def get(self, request, pk):
        vehicle = get_object_or_404(Vehicle.objects.filter(is_deleted=False), pk=pk)
        readings = vehicle.sensor_readings.order_by('timestamp')
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['sensor_type', 'value', 'timestamp', 'source'])
        for r in readings:
            writer.writerow([r.sensor_type, r.value, r.timestamp.isoformat(), r.source])
        response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="sensors_{vehicle.license_plate}.csv"'
        return response


# ============== FR19: GPS and Driving Data ==============

class GPSMapView(LoginRequiredMixin, DetailView):
    model = Vehicle
    template_name = 'vehicles/gps_map.html'
    context_object_name = 'vehicle'

    def get_queryset(self):
        qs = Vehicle.objects.filter(is_deleted=False)
        if self.request.user.is_driver:
            qs = qs.filter(assigned_driver=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        from datetime import timedelta
        import json
        import math
        ctx = super().get_context_data(**kwargs)
        days = int(self.request.GET.get('days', 1))
        since = timezone.now() - timedelta(days=days)
        readings = list(
            self.object.gps_readings.filter(timestamp__gte=since)
            .order_by('timestamp')
            .values('latitude', 'longitude', 'speed_kmh', 'timestamp')
        )
        points = []
        prev_pair = None
        distance_km = 0.0
        for r in readings:
            lat = float(r['latitude'])
            lng = float(r['longitude'])
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                continue
            pair = (round(lat, 6), round(lng, 6))
            if pair == prev_pair:
                continue
            if prev_pair is not None:
                dx = pair[0] - prev_pair[0]
                dy = pair[1] - prev_pair[1]
                distance_km += math.sqrt((dx * 111.0) ** 2 + (dy * 111.0) ** 2)
            points.append({
                'lat': lat,
                'lng': lng,
                'speed': float(r['speed_kmh'] or 0),
                'time': r['timestamp'].strftime('%Y-%m-%d %H:%M'),
                'iso_time': r['timestamp'].isoformat(),
            })
            prev_pair = pair
        ctx['gps_points_json'] = json.dumps(points)
        ctx['selected_days'] = days
        ctx['gps_summary'] = {
            'points': len(points),
            'distance_km': round(distance_km, 1),
            'last_seen': points[-1]['time'] if points else None,
        }
        return ctx


class DrivingAnalysisView(LoginRequiredMixin, DetailView):
    model = Vehicle
    template_name = 'vehicles/driving_analysis.html'
    context_object_name = 'vehicle'

    def get_queryset(self):
        qs = Vehicle.objects.filter(is_deleted=False)
        if self.request.user.is_driver:
            qs = qs.filter(assigned_driver=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        patterns = self.object.driving_patterns.all()[:30]
        ctx['patterns'] = patterns
        if patterns:
            from django.db.models import Avg, Max, Sum
            agg = self.object.driving_patterns.aggregate(
                avg_speed=Avg('avg_speed_kmh'),
                max_speed=Max('max_speed_kmh'),
                total_km=Sum('total_km'),
                total_driving=Sum('driving_hours'),
                total_idle=Sum('idle_hours'),
                total_aggressive=Sum('aggressive_events'),
            )
            ctx['stats'] = agg
        return ctx


class MileageReportView(LoginRequiredMixin, DetailView):
    model = Vehicle
    template_name = 'vehicles/mileage_report.html'
    context_object_name = 'vehicle'

    def get_queryset(self):
        qs = Vehicle.objects.filter(is_deleted=False)
        if self.request.user.is_driver:
            qs = qs.filter(assigned_driver=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        import json
        ctx = super().get_context_data(**kwargs)
        patterns = list(
            self.object.driving_patterns.order_by('period_start')
            .values('period_start', 'total_km')[:60]
        )
        labels = [p['period_start'].strftime('%Y-%m-%d') for p in patterns]
        values = [float(p['total_km']) for p in patterns]
        ctx['mileage_json'] = json.dumps({'labels': labels, 'values': values})
        ctx['current_mileage'] = self.object.current_mileage
        return ctx
