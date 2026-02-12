"""
Create or update a user for E2E tests (Playwright).
Run: python manage.py create_e2e_user
Uses email admin@e2e.local and password E2ePass123! (administrator role).
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()
E2E_EMAIL = 'admin@e2e.local'
E2E_PASSWORD = 'E2ePass123!'


class Command(BaseCommand):
    help = 'Create or update E2E test user (admin@e2e.local / E2ePass123!)'

    def handle(self, *args, **options):
        user, created = User.objects.update_or_create(
            email=E2E_EMAIL,
            defaults={
                'role': User.Role.ADMINISTRATOR,
                'is_active': True,
            },
        )
        user.set_password(E2E_PASSWORD)
        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created E2E user {E2E_EMAIL}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated E2E user {E2E_EMAIL}'))
