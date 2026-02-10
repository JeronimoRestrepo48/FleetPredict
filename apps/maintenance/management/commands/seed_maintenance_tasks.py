"""
Seed example maintenance tasks for simulated vehicles (SIM-001 … SIM-010).
Run: python manage.py seed_maintenance_tasks
Use --clear to remove only tasks created by this seed (title starts with "[Seed] ").
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.vehicles.models import Vehicle
from apps.maintenance.models import MaintenanceTask

SEED_TITLE_PREFIX = '[Seed] '


def make_tasks_for_vehicle(vehicle, today):
    """Return list of task dicts (title, description, type, scheduled_date, status, etc.) for one vehicle."""
    tasks = []
    # Completed: past dates
    tasks.append({
        'title': f'{SEED_TITLE_PREFIX}Oil change',
        'description': 'Routine oil and filter replacement.',
        'maintenance_type': MaintenanceTask.Type.PREVENTIVE,
        'scheduled_date': today - timedelta(days=45),
        'status': MaintenanceTask.Status.COMPLETED,
        'completion_date': today - timedelta(days=45),
        'actual_cost': Decimal('85.00'),
        'mileage_at_maintenance': max(0, (vehicle.current_mileage or 0) - 1200),
        'completion_notes': 'Done.',
        'priority': MaintenanceTask.Priority.MEDIUM,
    })
    tasks.append({
        'title': f'{SEED_TITLE_PREFIX}Brake inspection',
        'description': 'Visual and wear inspection of brakes.',
        'maintenance_type': MaintenanceTask.Type.INSPECTION,
        'scheduled_date': today - timedelta(days=90),
        'status': MaintenanceTask.Status.COMPLETED,
        'completion_date': today - timedelta(days=88),
        'actual_cost': Decimal('0.00'),
        'mileage_at_maintenance': max(0, (vehicle.current_mileage or 0) - 3500),
        'completion_notes': 'No action required.',
        'priority': MaintenanceTask.Priority.LOW,
    })
    # Scheduled: future
    tasks.append({
        'title': f'{SEED_TITLE_PREFIX}Tire rotation',
        'description': 'Rotate tires and check pressure.',
        'maintenance_type': MaintenanceTask.Type.PREVENTIVE,
        'scheduled_date': today + timedelta(days=14),
        'status': MaintenanceTask.Status.SCHEDULED,
        'estimated_duration': 45,
        'estimated_cost': Decimal('50.00'),
        'priority': MaintenanceTask.Priority.MEDIUM,
    })
    return tasks


class Command(BaseCommand):
    help = 'Create example maintenance tasks for simulated vehicles (SIM-001 … SIM-010). Use --clear to remove seed tasks.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete only maintenance tasks whose title starts with "[Seed] ".',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = MaintenanceTask.objects.filter(title__startswith=SEED_TITLE_PREFIX).delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} seed maintenance task(s).'))
            return

        today = timezone.now().date()
        vehicles = list(Vehicle.objects.filter(license_plate__startswith='SIM-', is_deleted=False).order_by('license_plate'))
        if not vehicles:
            self.stdout.write(self.style.WARNING('No simulated vehicles (SIM-*) found. Run seed_simulated_fleet first.'))
            return

        created = 0
        for vehicle in vehicles:
            for t in make_tasks_for_vehicle(vehicle, today):
                _, was_created = MaintenanceTask.objects.get_or_create(
                    vehicle=vehicle,
                    title=t['title'],
                    defaults={
                        'description': t.get('description', ''),
                        'maintenance_type': t['maintenance_type'],
                        'scheduled_date': t['scheduled_date'],
                        'status': t['status'],
                        'priority': t.get('priority', MaintenanceTask.Priority.MEDIUM),
                        'estimated_duration': t.get('estimated_duration'),
                        'estimated_cost': t.get('estimated_cost'),
                        'completion_date': t.get('completion_date'),
                        'actual_cost': t.get('actual_cost'),
                        'mileage_at_maintenance': t.get('mileage_at_maintenance'),
                        'completion_notes': t.get('completion_notes', ''),
                    },
                )
                if was_created:
                    created += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created} new seed maintenance task(s) for {len(vehicles)} vehicle(s).'))
