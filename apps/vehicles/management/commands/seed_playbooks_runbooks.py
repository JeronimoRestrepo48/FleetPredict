"""
Seed default Playbooks and Runbooks for SOC (alert type -> suggested steps and executable actions).
Run: python manage.py seed_playbooks_runbooks
"""

from django.core.management.base import BaseCommand
from apps.vehicles.models import VehicleAlert, Playbook, Runbook


# alert_type -> (name, description, steps)
PLAYBOOKS = {
    VehicleAlert.AlertType.HIGH_ENGINE_TEMP: (
        'High engine temperature',
        'Recommended steps when engine temperature is above normal.',
        [
            'Stop the vehicle in a safe place and allow engine to cool.',
            'Check coolant level and condition.',
            'Inspect for leaks in cooling system.',
            'Schedule inspection at workshop.',
        ],
    ),
    VehicleAlert.AlertType.ANOMALOUS_FUEL: (
        'Anomalous fuel consumption',
        'Steps when rapid fuel drop or anomaly is detected.',
        [
            'Verify fuel gauge and sensor readings.',
            'Check for visible fuel leaks.',
            'Review recent driving conditions and load.',
            'Schedule diagnostic at workshop if needed.',
        ],
    ),
    VehicleAlert.AlertType.HARSH_DRIVING: (
        'Harsh driving event',
        'Follow-up after harsh acceleration or braking.',
        [
            'Review driving behavior with driver.',
            'Check brake and tire condition.',
            'Document if recurring for training.',
        ],
    ),
    VehicleAlert.AlertType.PROLONGED_IDLE: (
        'Prolonged idling',
        'Reduce unnecessary engine idling.',
        [
            'Remind driver to avoid prolonged idling.',
            'Review operational procedures.',
        ],
    ),
    VehicleAlert.AlertType.MAINTENANCE_MILEAGE: (
        'Maintenance due by mileage',
        'Preventive maintenance approaching.',
        [
            'Schedule preventive maintenance before interval.',
            'Prepare parts and labor estimate.',
            'Assign to workshop.',
        ],
    ),
    VehicleAlert.AlertType.MAINTENANCE_TIME: (
        'Maintenance due by time',
        'Preventive maintenance by calendar.',
        [
            'Schedule preventive maintenance.',
            'Confirm vehicle availability.',
            'Assign to workshop.',
        ],
    ),
    VehicleAlert.AlertType.STATISTICAL_ANOMALY: (
        'Statistical anomaly',
        'Unusual reading vs recent baseline.',
        [
            'Verify sensor and telemetry consistency.',
            'Check for environmental or load factors.',
            'Schedule inspection if anomaly persists.',
        ],
    ),
}

# List of (name, alert_type or None, action_type, params)
RUNBOOKS = [
    ('Mark as read', None, Runbook.ActionType.MARK_ALERT_READ, {}),
    ('Dismiss alert', None, Runbook.ActionType.DISMISS_ALERT, {}),
    ('Create preventive task', None, Runbook.ActionType.CREATE_MAINTENANCE_TASK, {
        'title': 'Preventive maintenance (SOC)',
        'maintenance_type': 'preventive',
        'days_ahead': 3,
        'priority': 'medium',
    }),
    ('Create corrective task', None, Runbook.ActionType.CREATE_MAINTENANCE_TASK, {
        'title': 'Corrective maintenance (SOC)',
        'maintenance_type': 'corrective',
        'days_ahead': 1,
        'priority': 'high',
    }),
]


class Command(BaseCommand):
    help = 'Create default Playbooks and Runbooks for SOC.'

    def handle(self, *args, **options):
        for alert_type, (name, desc, steps) in PLAYBOOKS.items():
            pb, created = Playbook.objects.update_or_create(
                alert_type=alert_type,
                defaults={'name': name, 'description': desc, 'steps': steps},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created playbook: {pb.name}'))
            else:
                self.stdout.write(f'Updated playbook: {pb.name}')

        for name, alert_type, action_type, params in RUNBOOKS:
            rb, created = Runbook.objects.update_or_create(
                name=name,
                defaults={
                    'alert_type': alert_type,
                    'action_type': action_type,
                    'params': params,
                    'is_active': True,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created runbook: {rb.name}'))
            else:
                self.stdout.write(f'Updated runbook: {rb.name}')

        self.stdout.write(self.style.SUCCESS('Done. Playbooks and runbooks ready for SOC.'))
