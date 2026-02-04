"""
Views for Dashboard app.
Implements FR3: Monitoring dashboard with fleet status and key metrics.
"""

from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta

from apps.vehicles.models import Vehicle
from apps.maintenance.models import MaintenanceTask
from apps.users.models import User


class DashboardSummaryView(views.APIView):
    """
    API endpoint for dashboard summary data.
    FR3: Single view showing fleet status in near real-time.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
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

        # ============== Vehicle Statistics ==============
        total_vehicles = vehicles_qs.count()
        vehicles_by_status = vehicles_qs.values('status').annotate(
            count=Count('id')
        )
        
        vehicle_status_dict = {
            'active': 0,
            'inactive': 0,
            'under_maintenance': 0,
            'retired': 0,
        }
        for item in vehicles_by_status:
            vehicle_status_dict[item['status']] = item['count']

        # Fleet availability percentage
        available_vehicles = vehicle_status_dict['active']
        fleet_availability = (
            (available_vehicles / total_vehicles * 100)
            if total_vehicles > 0 else 0
        )

        # ============== Maintenance Statistics ==============
        # Upcoming maintenance (next 7 days)
        upcoming_maintenance = tasks_qs.filter(
            status__in=['scheduled', 'overdue'],
            scheduled_date__gte=today,
            scheduled_date__lte=next_week
        ).order_by('scheduled_date')[:10]

        upcoming_maintenance_data = [
            {
                'id': task.id,
                'title': task.title,
                'vehicle': task.vehicle.display_name,
                'vehicle_id': task.vehicle.id,
                'license_plate': task.vehicle.license_plate,
                'scheduled_date': task.scheduled_date,
                'priority': task.priority,
                'status': task.status,
            }
            for task in upcoming_maintenance
        ]

        # Task counts by status
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

        # Overdue tasks count
        overdue_tasks = tasks_qs.filter(
            status='scheduled',
            scheduled_date__lt=today
        ).count()
        task_status_dict['overdue'] = overdue_tasks

        # Tasks requiring attention (overdue + high/critical priority scheduled)
        tasks_requiring_attention = tasks_qs.filter(
            Q(status='overdue') |
            Q(
                status='scheduled',
                scheduled_date__lt=today
            ) |
            Q(
                status='scheduled',
                priority__in=['high', 'critical'],
                scheduled_date__lte=next_week
            )
        ).count()

        # ============== Recent Activity ==============
        # Recently completed tasks
        recent_completed = tasks_qs.filter(
            status='completed'
        ).order_by('-completion_date')[:5]

        recent_completed_data = [
            {
                'id': task.id,
                'title': task.title,
                'vehicle': task.vehicle.display_name,
                'completion_date': task.completion_date,
                'actual_cost': float(task.actual_cost) if task.actual_cost else None,
            }
            for task in recent_completed
        ]

        # ============== Cost Summary ==============
        # Monthly costs (current month)
        first_day_of_month = today.replace(day=1)
        monthly_costs = tasks_qs.filter(
            status='completed',
            completion_date__gte=first_day_of_month
        ).aggregate(
            total_cost=Sum('actual_cost')
        )

        # ============== Build Response ==============
        dashboard_data = {
            'summary': {
                'total_vehicles': total_vehicles,
                'fleet_availability': round(fleet_availability, 1),
                'vehicles_requiring_attention': (
                    vehicle_status_dict['under_maintenance'] +
                    vehicles_qs.filter(status='active').count() -
                    available_vehicles
                ),
                'tasks_requiring_attention': tasks_requiring_attention,
                'overdue_tasks': overdue_tasks,
            },
            'vehicles': {
                'total': total_vehicles,
                'by_status': vehicle_status_dict,
            },
            'maintenance': {
                'by_status': task_status_dict,
                'upcoming': upcoming_maintenance_data,
                'upcoming_count': len(upcoming_maintenance_data),
            },
            'recent_activity': {
                'completed_tasks': recent_completed_data,
            },
            'costs': {
                'monthly_total': float(monthly_costs['total_cost'] or 0),
            },
        }

        # Add user-specific data for drivers
        if user.is_driver:
            dashboard_data['user_context'] = {
                'role': user.role,
                'assigned_vehicles': total_vehicles,
            }

        return Response(dashboard_data)


class DashboardStatsView(views.APIView):
    """
    API endpoint for quick statistics refresh.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()

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

        stats = {
            'total_vehicles': vehicles_qs.count(),
            'active_vehicles': vehicles_qs.filter(status='active').count(),
            'scheduled_tasks': tasks_qs.filter(status='scheduled').count(),
            'in_progress_tasks': tasks_qs.filter(status='in_progress').count(),
            'overdue_tasks': tasks_qs.filter(
                status='scheduled',
                scheduled_date__lt=today
            ).count(),
        }

        return Response(stats)
