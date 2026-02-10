"""
Views for Dashboard app.
Implements FR3: Monitoring dashboard with fleet status and key metrics.
Renders HTML templates instead of JSON.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, View, ListView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Sum
from datetime import timedelta
from collections import OrderedDict

from apps.vehicles.models import Vehicle, VehicleAlert, Playbook, Runbook
from apps.maintenance.models import MaintenanceTask


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view - fleet status, metrics, upcoming maintenance.
    FR3: Single view showing fleet status in near real-time.
    """

    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        next_week = today + timedelta(days=7)

        # Period filter: 7d, 30d, month (default 7d for charts)
        period = self.request.GET.get('period', '7d')
        if period == '30d':
            chart_start = today - timedelta(days=30)
        elif period == 'month':
            chart_start = today.replace(day=1)
        else:
            period = '7d'
            chart_start = today - timedelta(days=6)

        # Get base querysets based on user role
        if user.is_driver:
            vehicles_qs = Vehicle.objects.filter(
                is_deleted=False,
                assigned_driver=user
            )
            tasks_qs = MaintenanceTask.objects.filter(
                vehicle__assigned_driver=user
            )
        else:
            vehicles_qs = Vehicle.objects.filter(is_deleted=False)
            tasks_qs = MaintenanceTask.objects.all()

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

        # Upcoming maintenance (next 7 days)
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
        vehicle_ids = vehicles_qs.values_list('id', flat=True)
        soc_alerts_qs = VehicleAlert.objects.filter(
            vehicle_id__in=vehicle_ids,
            severity__in=[VehicleAlert.Severity.HIGH, VehicleAlert.Severity.CRITICAL],
            read_at__isnull=True,
        ).select_related('vehicle').order_by('-created_at')[:50]
        soc_alerts = list(soc_alerts_qs)
        playbooks_by_type = {pb.alert_type: pb for pb in Playbook.objects.all()}
        soc_alerts_with_playbook = [(a, playbooks_by_type.get(a.alert_type)) for a in soc_alerts]
        runbooks_list = list(Runbook.objects.filter(is_active=True).order_by('name'))

        context.update({
            'vehicle_health_counts': vehicle_health_counts,
            'vehicles_with_health': vehicles_list[:15],
            'soc_alerts': soc_alerts,
            'soc_alerts_with_playbook': soc_alerts_with_playbook,
            'runbooks_list': runbooks_list,
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
        })
        return context


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
        return (
            VehicleAlert.objects.filter(vehicle_id__in=vehicle_ids)
            .select_related('vehicle')
            .order_by('-created_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['runbooks_list'] = list(Runbook.objects.filter(is_active=True).order_by('name'))
        return context


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
