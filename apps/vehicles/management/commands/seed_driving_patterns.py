"""
Create sample DrivingPattern rows for the Driving Analysis and Mileage pages (FR19).

Nothing in the app aggregates GPS into patterns automatically yet; this seeds demo rows.

Usage:
  python manage.py seed_driving_patterns
  python manage.py seed_driving_patterns --vehicle-id 5 --weeks 12 --clear
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.vehicles.models import Vehicle, DrivingPattern


class Command(BaseCommand):
    help = 'Insert sample DrivingPattern periods per vehicle (demo / FR19 driving analysis).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vehicle-id',
            type=int,
            action='append',
            dest='vehicle_ids',
            help='Only this vehicle id (repeat for multiple). Default: all non-deleted vehicles.',
        )
        parser.add_argument(
            '--weeks',
            type=int,
            default=8,
            help='Number of consecutive weekly periods to create (default 8).',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing DrivingPattern for selected vehicles before inserting.',
        )

    def handle(self, *args, **options):
        vehicle_ids = options['vehicle_ids']
        n_weeks = max(1, min(52, options['weeks']))

        qs = Vehicle.objects.filter(is_deleted=False)
        if vehicle_ids:
            qs = qs.filter(pk__in=vehicle_ids)
        vehicles = list(qs)
        if not vehicles:
            self.stdout.write(self.style.WARNING('No vehicles matched; nothing to do.'))
            return

        now = timezone.now()
        total = 0
        rng = random.Random(42)

        for vehicle in vehicles:
            if options['clear']:
                deleted, _ = DrivingPattern.objects.filter(vehicle=vehicle).delete()
                if deleted:
                    self.stdout.write(f'  Cleared {deleted} driving pattern(s) for {vehicle.license_plate}')

            # Weekly periods ending "now", going backwards (most recent week ends at now)
            for w in range(n_weeks):
                period_end = now - timedelta(weeks=w)
                period_start = period_end - timedelta(days=7)
                base_km = 120 + (hash(vehicle.pk * 31 + w) % 200)
                km = Decimal(str(round(base_km + rng.uniform(-15, 25), 2)))
                driving_h = Decimal(str(round(rng.uniform(18, 42), 2)))
                idle_h = Decimal(str(round(rng.uniform(4, 14), 2)))
                avg_s = Decimal(str(round(rng.uniform(28, 55), 2)))
                max_s = Decimal(str(round(float(avg_s) + rng.uniform(15, 45), 2)))
                aggressive = rng.randint(0, 8)

                DrivingPattern.objects.create(
                    vehicle=vehicle,
                    period_start=period_start,
                    period_end=period_end,
                    total_km=km,
                    driving_hours=driving_h,
                    idle_hours=idle_h,
                    avg_speed_kmh=avg_s,
                    max_speed_kmh=max_s,
                    aggressive_events=aggressive,
                )
                total += 1

            self.stdout.write(self.style.SUCCESS(
                f'{vehicle.license_plate}: {n_weeks} weekly pattern(s)'
            ))

        self.stdout.write(self.style.SUCCESS(f'Done. Created {total} DrivingPattern row(s).'))
