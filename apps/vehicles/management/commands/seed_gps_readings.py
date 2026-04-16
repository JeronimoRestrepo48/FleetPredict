"""
Create sample GPSReading rows so the GPS Map (FR19) shows a track.

The telemetry simulator does not insert GPSReading records; this command fills demo data.

Usage:
  python manage.py seed_gps_readings
  python manage.py seed_gps_readings --vehicle-id 3
  python manage.py seed_gps_readings --hours 48 --clear
"""

import math
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.vehicles.models import Vehicle, GPSReading


def _route_point(i: int, n: int, lat0: float, lng0: float) -> tuple[float, float, float]:
    """Small loop path around (lat0, lng0); speed varies slightly."""
    t = (i / max(n - 1, 1)) * 2 * math.pi
    lat = lat0 + 0.012 * math.sin(t)
    lng = lng0 + 0.012 * math.cos(t)
    speed = 25 + 15 * abs(math.sin(t * 2))
    return lat, lng, speed


class Command(BaseCommand):
    help = 'Insert sample GPSReading points for vehicles (demo / FR19 map).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vehicle-id',
            type=int,
            action='append',
            dest='vehicle_ids',
            help='Only this vehicle id (repeat for multiple). Default: all non-deleted vehicles.',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Spread readings over the last N hours (default 24).',
        )
        parser.add_argument(
            '--points',
            type=int,
            default=36,
            help='Number of GPS points per vehicle (default 36).',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing GPSReading for selected vehicles before inserting.',
        )

    def handle(self, *args, **options):
        vehicle_ids = options['vehicle_ids']
        hours = max(1, options['hours'])
        n_points = max(2, options['points'])

        qs = Vehicle.objects.filter(is_deleted=False)
        if vehicle_ids:
            qs = qs.filter(pk__in=vehicle_ids)
        vehicles = list(qs)
        if not vehicles:
            self.stdout.write(self.style.WARNING('No vehicles matched; nothing to do.'))
            return

        start = timezone.now() - timedelta(hours=hours)

        # Default map center (Bogotá area) — matches gps_map.html initial view
        lat0, lng0 = 4.65, -74.05

        total = 0
        for vehicle in vehicles:
            if options['clear']:
                deleted, _ = GPSReading.objects.filter(vehicle=vehicle).delete()
                if deleted:
                    self.stdout.write(f'  Cleared {deleted} GPS row(s) for {vehicle.license_plate}')

            for i in range(n_points):
                frac = i / max(n_points - 1, 1)
                ts = start + timedelta(seconds=frac * hours * 3600)
                lat, lng, speed = _route_point(i, n_points, lat0, lng0)
                GPSReading.objects.create(
                    vehicle=vehicle,
                    latitude=Decimal(str(round(lat, 6))),
                    longitude=Decimal(str(round(lng, 6))),
                    speed_kmh=Decimal(str(round(speed, 2))),
                    heading=Decimal(str(round((i * 17) % 360, 2))),
                    timestamp=ts,
                )
                total += 1

            self.stdout.write(self.style.SUCCESS(
                f'{vehicle.license_plate}: {n_points} points over last {hours}h'
            ))

        self.stdout.write(self.style.SUCCESS(f'Done. Created {total} GPSReading row(s).'))
