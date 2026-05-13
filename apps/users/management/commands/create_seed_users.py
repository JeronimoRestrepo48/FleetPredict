"""
Create or update default Fleet Manager and Mechanic users for development/testing.
Run: python manage.py create_seed_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.users.models import Organization

User = get_user_model()

SEED_USERS = [
    {
        'email': 'manager@fleetpredict.local',
        'password': 'ManagerPass123!',
        'first_name': 'Fleet',
        'last_name': 'Manager',
        'role': User.Role.FLEET_MANAGER,
    },
    {
        'email': 'mechanic@fleetpredict.local',
        'password': 'MechanicPass123!',
        'first_name': 'Chief',
        'last_name': 'Mechanic',
        'role': User.Role.MECHANIC,
    },
]


class Command(BaseCommand):
    help = 'Create or update Fleet Manager and Mechanic seed users for testing'

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(
            slug='fleetpredict-seed',
            defaults={'name': 'FleetPredict Seed Company'},
        )
        for entry in SEED_USERS:
            data = dict(entry)
            password = data.pop('password')
            user, created = User.objects.update_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': data['role'],
                    'is_active': True,
                    'organization': org,
                },
            )
            user.set_password(password)
            user.save()
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(
                    f'{action} {data["role"]}: {data["email"]}'
                )
            )
        self.stdout.write(
            self.style.SUCCESS(
                'Fleet Manager: manager@fleetpredict.local / ManagerPass123!'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                'Mechanic: mechanic@fleetpredict.local / MechanicPass123!'
            )
        )
