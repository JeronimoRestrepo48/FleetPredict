"""
Management command to create VehicleTypes and 10 simulated vehicles for telemetry testing.
Run: python manage.py seed_simulated_fleet
Use --clear to remove existing simulated vehicles (license_plate starting with SIM-) and re-seed.

Vehicles and types are scoped to organization slug ``simulated-fleet`` (created if missing).
Telemetry ingest should send ``organization_id`` with ``license_plate`` / ``vin`` when multiple tenants exist.
"""

import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.users.models import Organization
from apps.vehicles.models import Vehicle, VehicleType

User = get_user_model()
DRIVER_PASSWORD = 'DriverPass123!'
FM_SIM_EMAIL = 'sim-fleet-manager@fleetpredict.local'
FM_SIM_PASSWORD = 'SimFleet123!'
SIM_ORG_SLUG = 'simulated-fleet'
SIM_ORG_NAME = 'Simulated telemetry fleet'


# Vehicle type definitions: name, description, interval_days, interval_km
VEHICLE_TYPES = [
    ('Sedan', 'Passenger sedan', 90, 10000),
    ('Van', 'Cargo/passenger van', 90, 12000),
    ('Pickup', 'Light-duty pickup', 90, 10000),
    ('Box Truck', 'Medium box truck', 60, 8000),
    ('Bus', 'Passenger bus', 60, 15000),
    ('Cargo Truck', 'Heavy cargo truck', 45, 7500),
    ('Motorcycle', 'Motorcycle / courier', 30, 5000),
    ('Taxi', 'Taxi / ride-hail', 60, 12000),
    ('Delivery Van', 'Last-mile delivery van', 60, 10000),
    ('Ambulance', 'Emergency / service vehicle', 30, 6000),
]

# 10 vehicles: (license_plate_suffix, vin_suffix, make, model, year, color, type_name, fuel_type, fuel_capacity, start_mileage)
SIMULATED_VEHICLES = [
    ('SIM-001', '1HGBH41JXMN109001', 'Toyota', 'Camry', 2022, 'Silver', 'Sedan', 'Gasoline', 60),
    ('SIM-002', '2HGBH41JXMN109002', 'Ford', 'Transit', 2021, 'White', 'Van', 'Diesel', 80),
    ('SIM-003', '3HGBH41JXMN109003', 'Chevrolet', 'Silverado', 2023, 'Black', 'Pickup', 'Gasoline', 98),
    ('SIM-004', '4HGBH41JXMN109004', 'Mercedes-Benz', 'Sprinter', 2022, 'White', 'Box Truck', 'Diesel', 75),
    ('SIM-005', '5HGBH41JXMN109005', 'Freightliner', 'M2 Bus', 2020, 'Yellow', 'Bus', 'Diesel', 200),
    ('SIM-006', '6HGBH41JXMN109006', 'Volvo', 'VNL', 2021, 'Red', 'Cargo Truck', 'Diesel', 500),
    ('SIM-007', '7HGBH41JXMN109007', 'Honda', 'CB500X', 2023, 'Blue', 'Motorcycle', 'Gasoline', 17),
    ('SIM-008', '8HGBH41JXMN109008', 'Hyundai', 'Sonata', 2022, 'Gray', 'Taxi', 'Gasoline', 55),
    ('SIM-009', '9HGBH41JXMN109009', 'Ram', 'ProMaster', 2022, 'White', 'Delivery Van', 'Gasoline', 76),
    ('SIM-010', '0HGBH41JXMN109010', 'Ford', 'F-450 Ambulance', 2021, 'White', 'Ambulance', 'Diesel', 132),
]


def vin_check_digit(vin17):
    """Return a valid VIN check digit for 16-char prefix (last char is check digit)."""
    translit = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'J': 1, 'K': 2,
                'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9, 'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6,
                'X': 7, 'Y': 8, 'Z': 9, '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
                '7': 7, '8': 8, '9': 9}
    weight = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
    s = 0
    for i, c in enumerate(vin17[:17]):
        val = translit.get(c.upper(), 0)
        s += val * weight[i]
    rem = s % 11
    return 'X' if rem == 10 else str(rem)


class Command(BaseCommand):
    help = 'Create VehicleTypes and 10 simulated vehicles (license_plate SIM-001 ... SIM-010) for one org.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing simulated vehicles (SIM-*) before creating new ones.',
        )

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(
            slug=SIM_ORG_SLUG,
            defaults={'name': SIM_ORG_NAME},
        )

        if not User.objects.filter(
            organization=org,
            role=User.Role.FLEET_MANAGER,
        ).exists():
            User.objects.create_user(
                email=FM_SIM_EMAIL,
                password=FM_SIM_PASSWORD,
                first_name='Sim',
                last_name='Fleet Manager',
                role=User.Role.FLEET_MANAGER,
                organization=org,
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Created fleet manager: {FM_SIM_EMAIL} (password in stdout below)'))

        type_map = {}
        for name, desc, days, km in VEHICLE_TYPES:
            vt, created = VehicleType.objects.get_or_create(
                organization=org,
                name=name,
                defaults={
                    'description': desc,
                    'maintenance_interval_days': days,
                    'maintenance_interval_km': km,
                },
            )
            type_map[name] = vt
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created VehicleType: {name}'))

        if options['clear']:
            deleted, _ = Vehicle.objects.filter(license_plate__startswith='SIM-', organization=org).delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} simulated vehicle(s) for org {org.slug}.'))

        driver_emails = [f'sim-driver{i}@fleetpredict.local' for i in range(1, 11)]
        driver_names = [f'Sim Driver {i}' for i in range(1, 11)]
        drivers = []
        for email, first in zip(driver_emails, driver_names):
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first,
                    'last_name': 'Simulated',
                    'role': User.Role.DRIVER,
                    'is_active': True,
                    'organization': org,
                },
            )
            if created:
                user.set_password(DRIVER_PASSWORD)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created driver: {email}'))
            elif user.organization_id != org.pk:
                user.organization = org
                user.save(update_fields=['organization'])
            drivers.append(user)

        created_count = 0
        for idx, (plate, vin, make, model, year, color, type_name, fuel_type, fuel_cap) in enumerate(SIMULATED_VEHICLES):
            if len(vin) == 17:
                vin_final = vin
            else:
                vin_final = vin[:16] + vin_check_digit(vin[:16])
            vehicle_type = type_map.get(type_name) or type_map['Sedan']
            start_mileage = random.randint(5000, 85000)
            driver = drivers[idx] if idx < len(drivers) else None
            vehicle, created = Vehicle.objects.update_or_create(
                organization=org,
                license_plate=plate,
                defaults={
                    'vin': vin_final,
                    'make': make,
                    'model': model,
                    'year': year,
                    'color': color,
                    'vehicle_type': vehicle_type,
                    'status': Vehicle.Status.ACTIVE,
                    'current_mileage': start_mileage,
                    'fuel_type': fuel_type,
                    'fuel_capacity': fuel_cap,
                    'is_deleted': False,
                    'deleted_at': None,
                    'assigned_driver': driver,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created vehicle: {plate} ({make} {model})'))
            else:
                self.stdout.write(f'Updated vehicle: {plate}')

        self.stdout.write(self.style.SUCCESS(f'Done. Simulated fleet: {created_count} created.'))
        self.stdout.write(
            f'Organization: slug={org.slug!r}, id={org.pk}. '
            'Send organization_id in telemetry JSON with license_plate when using multi-tenant DB.'
        )
        self.stdout.write('Simulators can connect using vehicle_id or (organization_id + license_plate).')
        self.stdout.write(self.style.SUCCESS(f'FM: {FM_SIM_EMAIL} — password: {FM_SIM_PASSWORD}'))
        self.stdout.write(
            self.style.SUCCESS(
                f'Drivers: {", ".join(driver_emails)} — password: {DRIVER_PASSWORD}'
            )
        )
