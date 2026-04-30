"""
Views for Dashboard app.
Implements FR3: Monitoring dashboard with fleet status and key metrics.
Renders HTML templates instead of JSON.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, View, ListView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django import forms
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Sum
from datetime import datetime, timedelta
from collections import OrderedDict
import math
import csv

from apps.vehicles.models import Vehicle, VehicleAlert, VehicleType, Playbook, Runbook, ComplianceRequirement, GPSReading
from apps.vehicles.visibility import visible_vehicle_queryset
from apps.maintenance.models import MaintenanceTask
from django.contrib.auth import get_user_model
from .models import AlertRule, AlertThreshold, AuditLog, DashboardLayout
from .audit import log_audit

User = get_user_model()

SOC_LOCATION_HUBS = [
    ('Bogota', 4.7110, -74.0721),
    ('Medellin', 6.2442, -75.5812),
    ('Cali', 3.4516, -76.5320),
    ('Barranquilla', 10.9685, -74.7813),
    ('Cartagena', 10.3910, -75.4794),
    ('Bucaramanga', 7.1193, -73.1227),
    ('Santa Marta', 11.2408, -74.1990),
    ('Pereira', 4.8143, -75.6946),
]


def _nearest_city_label(lat, lng):
    if lat is None or lng is None:
        return 'Unknown'
    best_name = 'Unknown'
    best_dist = float('inf')
    for city, c_lat, c_lng in SOC_LOCATION_HUBS:
        dist = math.dist([float(lat), float(lng)], [c_lat, c_lng])
        if dist < best_dist:
            best_dist = dist
            best_name = city
    return best_name


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view - role-specific content.
    FR3: Administrator sees platform stats; Fleet Manager/Driver see fleet ops; Mechanic sees assigned tasks.
    """

    def get_template_names(self):
        user = self.request.user
        if user.is_administrator:
            return ['dashboard/dashboard_admin.html']
        if user.is_mechanic:
            return ['dashboard/dashboard_mechanic.html']
        return ['dashboard/dashboard.html']  # Fleet Manager and Driver

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_administrator:
            ctx = self._get_admin_context(context)
        elif user.is_mechanic:
            ctx = self._get_mechanic_context(context)
        elif user.is_fleet_manager:
            ctx = self._get_fleet_manager_context(context)
        else:
            ctx = self._get_driver_context(context)
        try:
            layout = DashboardLayout.objects.get(user=user)
            ctx['custom_layout'] = layout.layout
        except DashboardLayout.DoesNotExist:
            ctx['custom_layout'] = DashboardLayout.get_default_layout()
        ctx['widget_choices'] = DashboardLayout.WIDGET_CHOICES
        return ctx

    def _get_admin_context(self, context):
        """Platform management dashboard: users, roles, vehicle types, audit."""
        user = self.request.user
        today = timezone.now().date()
        total_users = User.objects.count()
        users_by_role = dict(
            User.objects.values('role').annotate(count=Count('id')).values_list('role', 'count')
        )
        role_counts = {
            'administrator': users_by_role.get('administrator', 0),
            'fleet_manager': users_by_role.get('fleet_manager', 0),
            'mechanic': users_by_role.get('mechanic', 0),
            'driver': users_by_role.get('driver', 0),
        }
        vehicle_types_count = VehicleType.objects.count()
        recent_audit = AuditLog.objects.select_related('user').order_by('-created_at')[:15]
        total_vehicles = Vehicle.objects.filter(is_deleted=False).count()
        active_vehicles = Vehicle.objects.filter(is_deleted=False, status='active').count()
        fleet_availability = (
            (active_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0
        )
        summary = (
            f"Platform overview: {total_users} users, {vehicle_types_count} vehicle types, "
            f"{total_vehicles} vehicles ({fleet_availability:.0f}% availability)."
        )
        context.update({
            'executive_summary': summary,
            'total_users': total_users,
            'role_counts': role_counts,
            'vehicle_types_count': vehicle_types_count,
            'recent_audit': recent_audit,
            'total_vehicles': total_vehicles,
            'fleet_availability': round(fleet_availability, 1),
        })
        return context

    def _get_mechanic_context(self, context):
        """Mechanic dashboard: assigned tasks, unassigned tasks, recent completions."""
        user = self.request.user
        today = timezone.now().date()
        due_days = AlertRule.get_maintenance_due_days()
        next_week = today + timedelta(days=due_days)
        tasks_qs = MaintenanceTask.objects.filter(
            Q(assignee=user) | Q(assignee__isnull=True)
        ).select_related('vehicle', 'assignee')
        my_assigned = tasks_qs.filter(assignee=user)
        unassigned = tasks_qs.filter(assignee__isnull=True)
        tasks_needing_attention = my_assigned.filter(
            Q(status='overdue') |
            Q(status='scheduled', scheduled_date__lt=today) |
            Q(status='scheduled', priority__in=['high', 'critical'], scheduled_date__lte=next_week)
        ).count()
        task_status_counts = tasks_qs.values('status').annotate(count=Count('id'))
        task_status_dict = {
            'scheduled': 0, 'in_progress': 0, 'completed': 0, 'cancelled': 0, 'overdue': 0,
        }
        for item in task_status_counts:
            task_status_dict[item['status']] = item['count']
        overdue_count = tasks_qs.filter(
            status='scheduled', scheduled_date__lt=today
        ).count()
        task_status_dict['overdue'] = overdue_count
        priority_counts = tasks_qs.filter(
            status__in=['scheduled', 'overdue', 'in_progress']
        ).values('priority').annotate(count=Count('id'))
        task_priority_dict = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for item in priority_counts:
            task_priority_dict[item['priority']] = item['count']
        upcoming_maintenance = list(tasks_qs.filter(
            status__in=['scheduled', 'overdue'],
            scheduled_date__gte=today,
            scheduled_date__lte=next_week
        ).order_by('scheduled_date')[:10])
        recent_completed = list(
            tasks_qs.filter(status='completed', assignee=user)
            .order_by('-completion_date')[:5]
        )
        summary = (
            f"{my_assigned.count()} tasks assigned to you, {unassigned.count()} unassigned. "
            f"{tasks_needing_attention} need attention."
        )
        context.update({
            'executive_summary': summary,
            'my_assigned_count': my_assigned.count(),
            'unassigned_count': unassigned.count(),
            'tasks_needing_attention': tasks_needing_attention,
            'task_status_dict': task_status_dict,
            'task_priority_dict': task_priority_dict,
            'upcoming_maintenance': upcoming_maintenance,
            'recent_completed': recent_completed,
            'period': '7d',
            'vehicle_status_dict': {},
            'vehicle_health_counts': {'green': 0, 'yellow': 0, 'red': 0},
            'vehicles_with_health': [],
            'soc_alerts': [],
            'soc_alerts_with_playbook': [],
            'runbooks_list': [],
            'total_vehicles': 0,
            'fleet_availability': 0,
            'available_vehicles': 0,
            'overdue_tasks': overdue_count,
            'upcoming_count': len(upcoming_maintenance),
            'monthly_total': 0,
            'costs_by_day': OrderedDict(),
            'completed_by_day': OrderedDict(),
            'compliance_expired': 0,
            'compliance_expiring': 0,
        })
        return context

    def _get_fleet_manager_context(self, context):
        """Full fleet operations dashboard (current behavior)."""
        return self._get_fleet_or_driver_context(context, fleet_scope=True)

    def _get_driver_context(self, context):
        """Driver dashboard - scoped to assigned vehicles."""
        return self._get_fleet_or_driver_context(context, fleet_scope=False)

    def _get_fleet_or_driver_context(self, context, fleet_scope):
        """Shared logic for Fleet Manager (full fleet) and Driver (assigned only)."""
        user = self.request.user
        today = timezone.now().date()
        due_days = AlertRule.get_maintenance_due_days()
        next_week = today + timedelta(days=due_days)

        # Period filter: 7d, 30d, month (default 7d for charts)
        period = self.request.GET.get('period', '7d')
        if period == '30d':
            chart_start = today - timedelta(days=30)
        elif period == 'month':
            chart_start = today.replace(day=1)
        else:
            period = '7d'
            chart_start = today - timedelta(days=6)

        if fleet_scope:
            vehicles_qs = visible_vehicle_queryset(user)
            tasks_qs = MaintenanceTask.objects.all()
        else:
            vehicles_qs = visible_vehicle_queryset(user)
            tasks_qs = MaintenanceTask.objects.filter(
                vehicle__assigned_driver=user
            )

        # Vehicle statistics
        total_vehicles = vehicles_qs.count()
        vehicles_by_status = vehicles_qs.values('status').annotate(count=Count('id'))
        vehicle_status_dict = {
            'active': 0,
            'inactive': 0,
            'under_maintenance': 0,
            'retired': 0,
        }
        for item in vehicles_by_status:
            vehicle_status_dict[item['status']] = item['count']

        available_vehicles = vehicle_status_dict['active']
        fleet_availability = (
            (available_vehicles / total_vehicles * 100)
            if total_vehicles > 0 else 0
        )

        # FR6: Vehicle health counts (green, yellow, red)
        vehicles_list = list(vehicles_qs)
        vehicle_health_counts = {'green': 0, 'yellow': 0, 'red': 0}
        for v in vehicles_list:
            vehicle_health_counts[v.health_status] = vehicle_health_counts.get(v.health_status, 0) + 1

        # Upcoming maintenance (next N days, FR8 configurable)
        upcoming_qs = tasks_qs.filter(
            status__in=['scheduled', 'overdue'],
            scheduled_date__gte=today,
            scheduled_date__lte=next_week
        ).order_by('scheduled_date')
        upcoming_count = upcoming_qs.count()
        upcoming_maintenance = list(upcoming_qs[:10])

        # Task counts
        task_status_counts = tasks_qs.values('status').annotate(count=Count('id'))
        task_status_dict = {
            'scheduled': 0,
            'in_progress': 0,
            'completed': 0,
            'cancelled': 0,
            'overdue': 0,
        }
        for item in task_status_counts:
            task_status_dict[item['status']] = item['count']
        overdue_tasks = tasks_qs.filter(
            status='scheduled',
            scheduled_date__lt=today
        ).count()
        task_status_dict['overdue'] = overdue_tasks

        tasks_requiring_attention = tasks_qs.filter(
            Q(status='overdue') |
            Q(status='scheduled', scheduled_date__lt=today) |
            Q(status='scheduled', priority__in=['high', 'critical'], scheduled_date__lte=next_week)
        ).count()

        # Recent completed tasks
        recent_completed = tasks_qs.filter(status='completed').order_by('-completion_date')[:5]

        # Monthly costs
        first_day_of_month = today.replace(day=1)
        monthly_costs = tasks_qs.filter(
            status='completed',
            completion_date__gte=first_day_of_month
        ).aggregate(total_cost=Sum('actual_cost'))
        monthly_total = float(monthly_costs['total_cost'] or 0)

        # Tasks by priority (for bar chart)
        priority_counts = tasks_qs.filter(
            status__in=['scheduled', 'overdue', 'in_progress']
        ).values('priority').annotate(count=Count('id'))
        task_priority_dict = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for item in priority_counts:
            task_priority_dict[item['priority']] = item['count']

        # Completed tasks / cost by day (for line chart) - based on period
        if period == '30d':
            num_days = 30
        elif period == 'month':
            from datetime import date
            num_days = (today - chart_start).days + 1
            num_days = min(max(num_days, 1), 31)
        else:
            num_days = 7
        costs_by_day = OrderedDict()
        completed_by_day = OrderedDict()
        for i in range(num_days):
            d = chart_start + timedelta(days=i)
            if d > today:
                break
            costs_by_day[d.isoformat()] = float(
                tasks_qs.filter(
                    status='completed',
                    completion_date=d
                ).aggregate(s=Sum('actual_cost'))['s'] or 0
            )
            completed_by_day[d.isoformat()] = tasks_qs.filter(
                status='completed',
                completion_date=d
            ).count()

        # Executive summary (1-2 sentences)
        if total_vehicles == 0:
            summary = "No vehicles in the fleet yet. Add vehicles to start tracking."
        else:
            parts = [
                f"{available_vehicles} of {total_vehicles} vehicles active",
                f"{fleet_availability:.0f}% availability",
            ]
            if upcoming_count > 0:
                parts.append(f"{upcoming_count} upcoming in 7 days")
            if tasks_requiring_attention > 0:
                parts.append(f"{tasks_requiring_attention} tasks need attention")
            summary = " · ".join(parts) + "."

        # SOC: high/critical alerts (unread), playbooks and runbooks
        soc_days = int(self.request.GET.get('soc_days', '7'))
        soc_vehicle = self.request.GET.get('soc_vehicle', '').strip()
        soc_reason = self.request.GET.get('soc_reason', '').strip()
        soc_place = self.request.GET.get('soc_place', '').strip()
        soc_search = self.request.GET.get('soc_search', '').strip()
        soc_limit = int(self.request.GET.get('soc_limit', '20'))
        soc_days = soc_days if soc_days in (1, 7, 30) else 7
        soc_limit = soc_limit if soc_limit in (20, 50, 100) else 20
        soc_since = timezone.now() - timedelta(days=soc_days)

        vehicle_ids = list(vehicles_qs.values_list('id', flat=True))
        soc_alerts_qs = VehicleAlert.objects.filter(
            vehicle_id__in=vehicle_ids,
            severity__in=[VehicleAlert.Severity.HIGH, VehicleAlert.Severity.CRITICAL],
            read_at__isnull=True,
            created_at__gte=soc_since,
        ).select_related('vehicle').order_by('-created_at')
        if soc_vehicle:
            soc_alerts_qs = soc_alerts_qs.filter(vehicle_id=soc_vehicle)
        if soc_reason:
            soc_alerts_qs = soc_alerts_qs.filter(alert_type=soc_reason)
        if soc_search:
            soc_alerts_qs = soc_alerts_qs.filter(message__icontains=soc_search)

        soc_alerts = list(soc_alerts_qs[:300])
        soc_vehicle_ids = sorted({a.vehicle_id for a in soc_alerts})
        latest_location_by_vehicle = {}
        if soc_vehicle_ids:
            gps_rows = (
                GPSReading.objects.filter(vehicle_id__in=soc_vehicle_ids)
                .order_by('vehicle_id', '-timestamp')
                .values('vehicle_id', 'latitude', 'longitude')
            )
            for row in gps_rows:
                if row['vehicle_id'] not in latest_location_by_vehicle:
                    latest_location_by_vehicle[row['vehicle_id']] = _nearest_city_label(
                        row['latitude'],
                        row['longitude'],
                    )
        for alert in soc_alerts:
            alert.location_label = latest_location_by_vehicle.get(alert.vehicle_id, 'Unknown')
        if soc_place:
            soc_alerts = [a for a in soc_alerts if a.location_label == soc_place]
        soc_place_options = sorted({a.location_label for a in soc_alerts if a.location_label})
        soc_total_count = len(soc_alerts)
        soc_alerts = soc_alerts[:soc_limit]
        playbooks_by_type = {pb.alert_type: pb for pb in Playbook.objects.all()}
        soc_alerts_with_playbook = [(a, playbooks_by_type.get(a.alert_type)) for a in soc_alerts]
        runbooks_list = list(Runbook.objects.filter(is_active=True).order_by('name'))

        # FR25: Compliance expiration alerts (for vehicles user can see)
        vehicle_ids = list(vehicles_qs.values_list('id', flat=True))
        compliance_expired = ComplianceRequirement.objects.filter(
            vehicle_id__in=vehicle_ids,
            expiration_date__lt=today,
        ).count() if vehicle_ids else 0
        # Compliance expiring window is configurable via AlertRule (default 30 days)
        compliance_window_days = AlertRule.get_compliance_expiring_days()
        compliance_expiring = ComplianceRequirement.objects.filter(
            vehicle_id__in=vehicle_ids,
            expiration_date__gte=today,
            expiration_date__lte=today + timedelta(days=compliance_window_days),
        ).count() if vehicle_ids else 0

        context.update({
            'vehicle_health_counts': vehicle_health_counts,
            'vehicles_with_health': vehicles_list[:15],
            'soc_alerts': soc_alerts,
            'soc_alerts_with_playbook': soc_alerts_with_playbook,
            'runbooks_list': runbooks_list,
            'soc_filter_days': soc_days,
            'soc_filter_vehicle': soc_vehicle,
            'soc_filter_reason': soc_reason,
            'soc_filter_place': soc_place,
            'soc_filter_search': soc_search,
            'soc_filter_limit': soc_limit,
            'soc_vehicle_options': list(vehicles_qs.order_by('license_plate')),
            'soc_reason_options': VehicleAlert.AlertType.choices,
            'soc_place_options': soc_place_options,
            'soc_total_count': soc_total_count,
            'total_vehicles': total_vehicles,
            'fleet_availability': round(fleet_availability, 1),
            'vehicle_status_dict': vehicle_status_dict,
            'available_vehicles': available_vehicles,
            'tasks_requiring_attention': tasks_requiring_attention,
            'overdue_tasks': overdue_tasks,
            'task_status_dict': task_status_dict,
            'task_priority_dict': task_priority_dict,
            'upcoming_maintenance': upcoming_maintenance,
            'upcoming_count': upcoming_count,
            'recent_completed': recent_completed,
            'monthly_total': monthly_total,
            'executive_summary': summary,
            'period': period,
            'costs_by_day': costs_by_day,
            'completed_by_day': completed_by_day,
            'compliance_expired': compliance_expired,
            'compliance_expiring': compliance_expiring,
            'compliance_window_days': compliance_window_days,
        })
        return context


class HelpCenterView(LoginRequiredMixin, TemplateView):
    """Global help and usability guide page."""

    template_name = 'dashboard/help_center.html'


class ExecuteRunbookView(LoginRequiredMixin, View):
    """POST: execute a runbook for an alert (SOC)."""
    http_method_names = ['post']

    def post(self, request):
        alert_id = request.POST.get('alert_id')
        runbook_id = request.POST.get('runbook_id')
        if not alert_id or not runbook_id:
            messages.error(request, 'Missing alert or runbook.')
            return redirect('dashboard:index')
        user = request.user
        vehicle_ids = Vehicle.objects.filter(is_deleted=False)
        if user.is_driver:
            vehicle_ids = vehicle_ids.filter(assigned_driver=user)
        vehicle_ids = set(vehicle_ids.values_list('id', flat=True))
        alert = get_object_or_404(VehicleAlert, pk=alert_id)
        if alert.vehicle_id not in vehicle_ids:
            messages.error(request, 'You do not have access to this alert.')
            return redirect('dashboard:index')
        runbook = get_object_or_404(Runbook, pk=runbook_id, is_active=True)
        if runbook.alert_type and runbook.alert_type != alert.alert_type:
            messages.error(request, 'This runbook does not apply to this alert type.')
            return redirect('dashboard:index')
        success, msg = runbook.execute(alert, user)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg or 'Action failed.')
        next_url = request.POST.get('next', '')
        if next_url == 'predictions':
            return redirect('dashboard:predictions')
        if next_url == 'alerts':
            return redirect('dashboard:alerts')
        return redirect('dashboard:index')


class PredictionsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """FR9: Failure prediction engine - list recommendations (vehicle, type, confidence, timeframe)."""
    model = VehicleAlert
    template_name = 'dashboard/predictions.html'
    context_object_name = 'alerts'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_view_reports()

    def get_queryset(self):
        user = self.request.user
        vehicle_ids = Vehicle.objects.filter(is_deleted=False)
        if user.is_driver:
            vehicle_ids = vehicle_ids.filter(assigned_driver=user)
        vehicle_ids = vehicle_ids.values_list('id', flat=True)
        qs = (
            VehicleAlert.objects.filter(vehicle_id__in=vehicle_ids)
            .select_related('vehicle')
        )
        severity = self.request.GET.get('severity')
        if severity and severity in dict(VehicleAlert.Severity.choices):
            qs = qs.filter(severity=severity)
        sort = self.request.GET.get('sort')
        severity_order = {
            VehicleAlert.Severity.CRITICAL: 0,
            VehicleAlert.Severity.HIGH: 1,
            VehicleAlert.Severity.MEDIUM: 2,
            VehicleAlert.Severity.LOW: 3,
        }
        rows = list(qs.order_by('-created_at')[:300])
        for alert in rows:
            if not alert.criticality_reason:
                alert.criticality_reason = alert.build_criticality_reason()
        if sort == 'criticality':
            rows.sort(key=lambda a: (severity_order.get(a.severity, 9), -a.created_at.timestamp()))
        return rows
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['runbooks_list'] = list(Runbook.objects.filter(is_active=True).order_by('name'))
        context['severity_choices'] = VehicleAlert.Severity.choices
        context['sort'] = self.request.GET.get('sort', '')
        return context


class OverrideCriticalityView(LoginRequiredMixin, UserPassesTestMixin, View):
    """FR10: controlled severity override with audit trail."""
    http_method_names = ['post']

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_maintenance()

    def post(self, request):
        alert = get_object_or_404(VehicleAlert, pk=request.POST.get('alert_id'))
        new_severity = request.POST.get('severity')
        reason = request.POST.get('reason', '').strip()
        if new_severity not in dict(VehicleAlert.Severity.choices):
            messages.error(request, 'Invalid criticality level.')
            return redirect('dashboard:predictions')
        if not reason:
            messages.error(request, 'A reason is required to override criticality.')
            return redirect('dashboard:predictions')
        old_values = {'severity': alert.severity, 'criticality_reason': alert.criticality_reason}
        alert.severity = new_severity
        alert.criticality_reason = f'Overridden by {request.user.get_full_name() or request.user.email}: {reason}'
        alert.severity_overridden_by = request.user
        alert.severity_override_reason = reason
        alert.severity_overridden_at = timezone.now()
        alert.save(update_fields=[
            'severity', 'criticality_reason', 'severity_overridden_by',
            'severity_override_reason', 'severity_overridden_at',
        ])
        log_audit(
            request,
            'override',
            'VehicleAlert',
            alert.pk,
            f'Criticality overridden for {alert.vehicle.display_name}',
            old_values=old_values,
            new_values={'severity': alert.severity, 'criticality_reason': alert.criticality_reason},
        )
        messages.success(request, 'Criticality updated and audited.')
        return redirect('dashboard:predictions')


class SuggestedMaintenanceView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """FR11: Suggested maintenance - list pending suggestions with Accept / Dismiss."""
    model = VehicleAlert
    template_name = 'dashboard/suggested_maintenance.html'
    context_object_name = 'suggestions'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_view_reports()

    def get_queryset(self):
        user = self.request.user
        vehicle_ids = Vehicle.objects.filter(is_deleted=False)
        if user.is_driver:
            vehicle_ids = vehicle_ids.filter(assigned_driver=user)
        vehicle_ids = vehicle_ids.values_list('id', flat=True)
        suggestions = list(
            VehicleAlert.objects.filter(
                vehicle_id__in=vehicle_ids,
            )
            .filter(Q(suggestion_status__isnull=True) | Q(suggestion_status='pending'))
            .select_related('vehicle')
            .order_by('-created_at')[:300]
        )
        for suggestion in suggestions:
            if not suggestion.criticality_reason:
                suggestion.criticality_reason = suggestion.build_criticality_reason()
            if not suggestion.suggestion_scheduled_date:
                days = 3 if suggestion.severity == VehicleAlert.Severity.CRITICAL else 7
                suggestion.suggestion_scheduled_date = (timezone.now() + timedelta(days=days)).date()
            if not suggestion.suggestion_priority:
                suggestion.suggestion_priority = 'critical' if suggestion.severity == VehicleAlert.Severity.CRITICAL else 'high'
        return suggestions


class AcceptSuggestionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """FR11: Accept suggested maintenance - create task and mark accepted."""
    http_method_names = ['post']

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_maintenance()

    def post(self, request):
        from apps.maintenance.models import MaintenanceTask
        alert_id = request.POST.get('alert_id')
        if not alert_id:
            messages.error(request, 'Missing alert.')
            return redirect('dashboard:suggested_maintenance')
        user = request.user
        vehicle_ids = set(Vehicle.objects.filter(is_deleted=False).values_list('id', flat=True))
        if user.is_driver:
            vehicle_ids = set(Vehicle.objects.filter(is_deleted=False, assigned_driver=user).values_list('id', flat=True))
        alert = get_object_or_404(VehicleAlert, pk=alert_id)
        if alert.vehicle_id not in vehicle_ids:
            messages.error(request, 'Not allowed.')
            return redirect('dashboard:suggested_maintenance')
        if alert.suggestion_status not in (None, 'pending'):
            messages.warning(request, 'Suggestion already handled.')
            return redirect('dashboard:suggested_maintenance')
        scheduled_date_raw = request.POST.get('scheduled_date')
        priority = request.POST.get('priority') or ('critical' if alert.severity == 'critical' else 'high')
        title = request.POST.get('title') or f"Suggested: {alert.get_alert_type_display()}"
        description = request.POST.get('description') or alert.message
        try:
            scheduled_date = datetime.strptime(scheduled_date_raw, '%Y-%m-%d').date() if scheduled_date_raw else (timezone.now() + timedelta(days=7)).date()
        except ValueError:
            scheduled_date = (timezone.now() + timedelta(days=7)).date()
        task = MaintenanceTask.objects.create(
            vehicle=alert.vehicle,
            title=title,
            description=description,
            maintenance_type='preventive',
            scheduled_date=scheduled_date,
            status=MaintenanceTask.Status.SCHEDULED,
            priority=priority,
            created_by=user,
        )
        alert.suggestion_status = 'accepted'
        alert.suggestion_scheduled_date = scheduled_date
        alert.suggestion_priority = priority
        alert.suggestion_handled_at = timezone.now()
        alert.save(update_fields=['suggestion_status', 'suggestion_scheduled_date', 'suggestion_priority', 'suggestion_handled_at'])
        log_audit(
            request,
            'create',
            'MaintenanceTask',
            task.pk,
            f'Accepted suggestion from alert {alert.pk}',
            new_values={'scheduled_date': scheduled_date.isoformat(), 'priority': priority, 'source_alert': alert.pk},
        )
        messages.success(request, f'Maintenance task created: {task.title}')
        return redirect('dashboard:suggested_maintenance')


class DismissSuggestionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """FR11: Dismiss suggested maintenance."""
    http_method_names = ['post']

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_view_reports()

    def post(self, request):
        alert_id = request.POST.get('alert_id')
        if not alert_id:
            messages.error(request, 'Missing alert.')
            return redirect('dashboard:suggested_maintenance')
        user = request.user
        vehicle_ids = set(Vehicle.objects.filter(is_deleted=False).values_list('id', flat=True))
        if user.is_driver:
            vehicle_ids = set(Vehicle.objects.filter(is_deleted=False, assigned_driver=user).values_list('id', flat=True))
        alert = get_object_or_404(VehicleAlert, pk=alert_id)
        if alert.vehicle_id not in vehicle_ids:
            messages.error(request, 'Not allowed.')
            return redirect('dashboard:suggested_maintenance')
        if alert.suggestion_status not in (None, 'pending'):
            messages.warning(request, 'Suggestion already handled.')
            return redirect('dashboard:suggested_maintenance')
        reason = request.POST.get('dismiss_reason', '').strip()
        alert.suggestion_status = 'dismissed'
        alert.suggestion_dismiss_reason = reason
        alert.suggestion_handled_at = timezone.now()
        alert.save(update_fields=['suggestion_status', 'suggestion_dismiss_reason', 'suggestion_handled_at'])
        log_audit(
            request,
            'update',
            'VehicleAlert',
            alert.pk,
            'Dismissed maintenance suggestion',
            new_values={'suggestion_status': 'dismissed', 'reason': reason},
        )
        messages.success(request, 'Suggestion dismissed.')
        return redirect('dashboard:suggested_maintenance')


class AlertsView(LoginRequiredMixin, ListView):
    """FR7: Notification center - list alerts for user's vehicles with filters and runbook actions."""
    model = VehicleAlert
    template_name = 'dashboard/alerts.html'
    context_object_name = 'alerts'
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user
        vehicle_ids = Vehicle.objects.filter(is_deleted=False)
        if user.is_driver:
            vehicle_ids = vehicle_ids.filter(assigned_driver=user)
        vehicle_ids = vehicle_ids.values_list('id', flat=True)
        qs = (
            VehicleAlert.objects.filter(vehicle_id__in=vehicle_ids)
            .select_related('vehicle')
            .order_by('-created_at')
        )
        severity = self.request.GET.get('severity')
        if severity and severity in dict(VehicleAlert.Severity.choices):
            qs = qs.filter(severity=severity)
        read_filter = self.request.GET.get('read')
        if read_filter == 'unread':
            qs = qs.filter(read_at__isnull=True)
        elif read_filter == 'read':
            qs = qs.exclude(read_at__isnull=True)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['runbooks_list'] = list(Runbook.objects.filter(is_active=True).order_by('name'))
        context['severity_choices'] = VehicleAlert.Severity.choices
        return context


# ============== FR8: Alert rules (configurable thresholds) ==============

class AlertRuleForm(forms.ModelForm):
    class Meta:
        model = AlertRule
        fields = ('value_int', 'enabled')
        widgets = {
            'value_int': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 365}),
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AlertRuleCreateForm(forms.ModelForm):
    """Form to create a new alert rule (choose from rule types not yet configured)."""
    class Meta:
        model = AlertRule
        fields = ('name', 'value_int', 'enabled')
        widgets = {
            'name': forms.Select(attrs={'class': 'form-select'}),
            'value_int': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 365}),
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show rule types that don't have a rule yet
        existing = set(AlertRule.objects.values_list('name', flat=True))
        choices = [(k, v) for k, v in AlertRule.RULE_TYPES if k not in existing]
        self.fields['name'].choices = choices
        if not choices:
            self.fields['name'].choices = [('', '— All rule types are configured —')]


class AlertRuleListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List alert rules. Admin or Fleet Manager only."""
    model = AlertRule
    template_name = 'dashboard/alertrule_list.html'
    context_object_name = 'rules'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_vehicles()

    def get_queryset(self):
        # Ensure default rules exist
        AlertRule.objects.get_or_create(
            name='maintenance_due_days',
            defaults={'value_int': 7, 'enabled': True},
        )
        AlertRule.objects.get_or_create(
            name='maintenance_overdue',
            defaults={'value_int': 1, 'enabled': True},
        )
        AlertRule.objects.get_or_create(
            name='compliance_expiring_days',
            defaults={'value_int': 30, 'enabled': True},
        )
        AlertRule.objects.get_or_create(
            name='workorder_due_days',
            defaults={'value_int': 7, 'enabled': True},
        )
        return AlertRule.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        existing = set(AlertRule.objects.values_list('name', flat=True))
        context['available_rule_types'] = [
            (k, v) for k, v in AlertRule.RULE_TYPES if k not in existing
        ]
        return context

    def post(self, request, *args, **kwargs):
        """Handle inline configuration (save rule from list page)."""
        rule_id = request.POST.get('rule_id')
        if not rule_id:
            return self.get(request, *args, **kwargs)
        try:
            rule = AlertRule.objects.get(pk=rule_id)
        except AlertRule.DoesNotExist:
            messages.error(request, 'Rule not found.')
            return self.get(request, *args, **kwargs)
        value_raw = request.POST.get('value_int')
        enabled = request.POST.get('enabled') == 'on'
        if value_raw is not None and value_raw != '':
            try:
                rule.value_int = max(1, min(365, int(value_raw)))
            except ValueError:
                rule.value_int = 7
        rule.enabled = enabled
        rule.save()
        messages.success(request, f'Alert rule "{rule.get_name_display()}" updated.')
        return self.get(request, *args, **kwargs)


class AlertRuleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new alert rule (choose from types not yet configured)."""
    model = AlertRule
    form_class = AlertRuleCreateForm
    template_name = 'dashboard/alertrule_create.html'
    success_url = reverse_lazy('dashboard:alertrule_list')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_vehicles()

    def form_valid(self, form):
        messages.success(self.request, 'Alert rule created.')
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        existing = set(AlertRule.objects.values_list('name', flat=True))
        if len(existing) >= len(AlertRule.RULE_TYPES):
            messages.info(request, 'All alert rule types are already configured.')
            return redirect(reverse_lazy('dashboard:alertrule_list'))
        return super().get(request, *args, **kwargs)


class AlertRuleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit one alert rule."""
    model = AlertRule
    form_class = AlertRuleForm
    template_name = 'dashboard/alertrule_form.html'
    context_object_name = 'rule'
    success_url = reverse_lazy('dashboard:alertrule_list')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_vehicles()

    def form_valid(self, form):
        messages.success(self.request, 'Alert rule updated.')
        return super().form_valid(form)


# ============== Alert thresholds (telemetry triggers) ==============

class AlertThresholdForm(forms.ModelForm):
    class Meta:
        model = AlertThreshold
        fields = ('attribute', 'operator', 'value_float', 'severity', 'description', 'enabled')
        widgets = {
            'attribute': forms.Select(attrs={'class': 'form-select'}),
            'operator': forms.Select(attrs={'class': 'form-select'}),
            'value_float': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional label'}),
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AlertThresholdListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List telemetry thresholds (triggers)."""
    model = AlertThreshold
    template_name = 'dashboard/alertthreshold_list.html'
    context_object_name = 'thresholds'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_vehicles()

    def get_queryset(self):
        return AlertThreshold.objects.all().order_by('attribute', 'value_float')


class AlertThresholdCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new telemetry threshold trigger."""
    model = AlertThreshold
    form_class = AlertThresholdForm
    template_name = 'dashboard/alertthreshold_form.html'
    success_url = reverse_lazy('dashboard:alertthreshold_list')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_vehicles()

    def form_valid(self, form):
        messages.success(self.request, 'Threshold created.')
        return super().form_valid(form)


class AlertThresholdUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit a telemetry threshold."""
    model = AlertThreshold
    form_class = AlertThresholdForm
    template_name = 'dashboard/alertthreshold_form.html'
    context_object_name = 'threshold'
    success_url = reverse_lazy('dashboard:alertthreshold_list')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_vehicles()

    def form_valid(self, form):
        messages.success(self.request, 'Threshold updated.')
        return super().form_valid(form)


class AlertThresholdDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a telemetry threshold."""
    model = AlertThreshold
    success_url = reverse_lazy('dashboard:alertthreshold_list')
    template_name = 'dashboard/alertthreshold_confirm_delete.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_vehicles()

    def form_valid(self, form):
        messages.success(self.request, 'Threshold deleted.')
        return super().form_valid(form)


# ============== FR27: Audit log ==============

class AuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List audit log entries. Admin only."""
    model = AuditLog
    template_name = 'dashboard/auditlog_list.html'
    context_object_name = 'audit_logs'
    paginate_by = 50

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_platform()

    def get_queryset(self):
        qs = AuditLog.objects.select_related('user').order_by('-created_at')
        action = self.request.GET.get('action')
        if action and action in dict(AuditLog.ACTION_CHOICES):
            qs = qs.filter(action=action)
        model_name = self.request.GET.get('model')
        if model_name:
            qs = qs.filter(model_name__icontains=model_name)
        user_query = self.request.GET.get('user')
        if user_query:
            qs = qs.filter(Q(user__email__icontains=user_query) | Q(user__first_name__icontains=user_query) | Q(user__last_name__icontains=user_query))
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(Q(message__icontains=search) | Q(object_id__icontains=search) | Q(model_name__icontains=search))
        start = self.request.GET.get('start')
        end = self.request.GET.get('end')
        if start:
            qs = qs.filter(created_at__date__gte=start)
        if end:
            qs = qs.filter(created_at__date__lte=end)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_choices'] = AuditLog.ACTION_CHOICES
        return context


class AuditLogExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    """FR27: export filtered audit log as CSV."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_platform()

    def get(self, request):
        view = AuditLogListView()
        view.request = request
        qs = view.get_queryset()
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="audit_log.csv"'
        writer = csv.writer(response)
        writer.writerow(['created_at', 'user', 'action', 'model', 'object_id', 'message', 'old_values', 'new_values', 'ip'])
        for entry in qs:
            writer.writerow([
                entry.created_at.isoformat(),
                entry.user.email if entry.user else '',
                entry.action,
                entry.model_name,
                entry.object_id,
                entry.message,
                entry.old_values,
                entry.new_values,
                entry.ip_address or '',
            ])
        log_audit(request, 'export', 'AuditLog', '', 'Exported audit log', metadata={'rows': qs.count()})
        return response


# ============== FR28: Dashboard Customization ==============

class DashboardCustomizeView(LoginRequiredMixin, View):
    def get(self, request):
        from django.template.response import TemplateResponse
        layout_obj, _ = DashboardLayout.objects.get_or_create(
            user=request.user,
            defaults={'layout': DashboardLayout.get_default_layout()},
        )
        import json
        return TemplateResponse(request, 'dashboard/customize.html', {
            'layout_json': json.dumps(layout_obj.layout),
            'widget_choices': DashboardLayout.WIDGET_CHOICES,
            'size_choices': DashboardLayout.SIZE_CHOICES,
        })

    def post(self, request):
        import json
        try:
            new_layout = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            from django.http import JsonResponse
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        valid_types = {c[0] for c in DashboardLayout.WIDGET_CHOICES}
        valid_sizes = {c[0] for c in DashboardLayout.SIZE_CHOICES}
        cleaned = []
        for i, w in enumerate(new_layout):
            wt = w.get('widget_type', '')
            sz = w.get('size', 'sm')
            if wt in valid_types and sz in valid_sizes:
                cleaned.append({'widget_type': wt, 'position': i, 'size': sz})
        layout_obj, _ = DashboardLayout.objects.get_or_create(
            user=request.user,
            defaults={'layout': cleaned},
        )
        layout_obj.layout = cleaned
        layout_obj.save(update_fields=['layout', 'updated_at'])
        from django.http import JsonResponse
        return JsonResponse({'ok': True, 'count': len(cleaned)})


class DashboardResetView(LoginRequiredMixin, View):
    def post(self, request):
        DashboardLayout.objects.filter(user=request.user).update(
            layout=DashboardLayout.get_default_layout()
        )
        messages.success(request, 'Dashboard reset to default layout.')
        return redirect('dashboard:index')
