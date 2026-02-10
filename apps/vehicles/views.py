"""
Views for Vehicles app.
Implements FR2: Vehicle registry.
Uses Django MVT - template rendering.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.db.models import Q

from .models import Vehicle, VehicleType, VehicleTelemetry
from .forms import VehicleForm, VehicleTypeForm


class CanManageVehiclesMixin(UserPassesTestMixin):
    """Mixin that requires user to be admin or fleet manager."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_vehicles()


# ============== Vehicle Views (FR2) ==============

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
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_manage'] = self.request.user.can_manage_vehicles()
        context['status_choices'] = Vehicle.Status.choices
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
        return context


class VehicleCreateView(LoginRequiredMixin, CanManageVehiclesMixin, CreateView):
    """Create vehicle."""

    model = Vehicle
    form_class = VehicleForm
    template_name = 'vehicles/vehicle_form.html'
    success_url = reverse_lazy('vehicles:vehicle_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Vehicle created successfully.')
        return super().form_valid(form)


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
        messages.success(self.request, 'Vehicle updated successfully.')
        return super().form_valid(form)


class VehicleDeleteView(LoginRequiredMixin, CanManageVehiclesMixin, DeleteView):
    """Soft delete vehicle."""

    model = Vehicle
    template_name = 'vehicles/vehicle_confirm_delete.html'
    context_object_name = 'vehicle'
    success_url = reverse_lazy('vehicles:vehicle_list')

    def get_queryset(self):
        return Vehicle.objects.filter(is_deleted=False)

    def form_valid(self, form):
        self.object.soft_delete()
        messages.success(self.request, 'Vehicle deleted successfully.')
        return redirect(self.success_url)


class VehicleHistoryView(LoginRequiredMixin, DetailView):
    """Vehicle maintenance history (FR5)."""

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
