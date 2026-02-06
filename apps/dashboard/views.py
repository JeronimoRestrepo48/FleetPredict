"""
Views for Dashboard app.
Implements FR3: Monitoring dashboard with fleet status and key metrics.
Renders HTML templates instead of JSON.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta

from apps.vehicles.models import Vehicle
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

        # Upcoming maintenance (next 7 days)
        upcoming_maintenance = tasks_qs.filter(
            status__in=['scheduled', 'overdue'],
            scheduled_date__gte=today,
            scheduled_date__lte=next_week
        ).order_by('scheduled_date')[:10]

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

        context.update({
            'total_vehicles': total_vehicles,
            'fleet_availability': round(fleet_availability, 1),
            'vehicle_status_dict': vehicle_status_dict,
            'available_vehicles': available_vehicles,
            'tasks_requiring_attention': tasks_requiring_attention,
            'overdue_tasks': overdue_tasks,
            'task_status_dict': task_status_dict,
            'upcoming_maintenance': upcoming_maintenance,
            'recent_completed': recent_completed,
            'monthly_total': float(monthly_costs['total_cost'] or 0),
        })
        return context
