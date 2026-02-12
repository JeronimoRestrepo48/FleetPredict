"""
Build ML dataset from historical telemetry and alerts.
Slides over time per vehicle, forms windows of W readings, labels from VehicleAlert
within a short delay after window end, else "normal". Writes CSV and/or JSON for training and continuous learning.
"""

import csv
import json
import os
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from apps.vehicles.models import Vehicle, VehicleTelemetry, VehicleAlert
from apps.vehicles.ml.features import extract_features


# Label: if an alert was created for this vehicle within LABEL_DELTA after the window's last timestamp
LABEL_DELTA_MINUTES = 5


class Command(BaseCommand):
    help = 'Build ML dataset from telemetry windows and alert labels. Writes CSV and/or JSON for training and continuous learning.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Output CSV path (default: dataset.csv if --output-json not given; omit to write only JSON).',
        )
        parser.add_argument(
            '--output-json',
            type=str,
            default=None,
            help='Also write JSON for continuous learning (e.g. media/models/ml_training_data.json). Same samples as CSV.',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of history (default: 90)',
        )
        parser.add_argument(
            '--window-size',
            type=int,
            default=None,
            help=f'Window size (default: settings.ML_WINDOW_SIZE or {getattr(settings, "ML_WINDOW_SIZE", 20)})',
        )
        parser.add_argument(
            '--step-readings',
            type=int,
            default=5,
            help='Slide step: form next window every N readings (default: 5)',
        )

    def handle(self, *args, **options):
        output_path = (options['output'] or '').strip() or None
        output_json_path = (options['output_json'] or '').strip() or None
        days = options['days']
        window_size = options['window_size'] or getattr(settings, 'ML_WINDOW_SIZE', 20)
        step = max(1, options['step_readings'])
        since = timezone.now() - timedelta(days=days)
        label_delta = timedelta(minutes=LABEL_DELTA_MINUTES)

        if output_path is None and not output_json_path:
            output_path = 'dataset.csv'
        elif output_path is None and output_json_path:
            output_path = None  # JSON only

        vehicles = Vehicle.objects.filter(is_deleted=False).values_list('id', flat=True)
        n_features = extract_features([]).size
        rows = []  # list of (features_list, label)

        for vehicle_id in vehicles:
            readings_qs = (
                VehicleTelemetry.objects.filter(vehicle_id=vehicle_id, timestamp__gte=since)
                .order_by('-timestamp')
            )
            all_readings = list(readings_qs)
            if len(all_readings) < window_size:
                continue
            alerts_in_range = list(
                VehicleAlert.objects.filter(
                    vehicle_id=vehicle_id,
                    created_at__gte=since,
                ).order_by('created_at')
            )

            idx = 0
            while idx + window_size <= len(all_readings):
                window = all_readings[idx : idx + window_size]
                last_ts = window[-1].timestamp
                label = 'normal'
                for alert in alerts_in_range:
                    if alert.created_at >= last_ts and (alert.created_at - last_ts) <= label_delta:
                        label = alert.alert_type
                        break
                feats = extract_features(window)
                rows.append((feats.tolist(), label))
                idx += step

        total_rows = len(rows)

        if output_path and total_rows > 0:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)) or '.', exist_ok=True)
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([f'f{i}' for i in range(n_features)] + ['label'])
                for feats, label in rows:
                    writer.writerow(feats + [label])
            self.stdout.write(self.style.SUCCESS(f'Wrote {total_rows} rows to {output_path}'))

        if output_json_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_json_path)) or '.', exist_ok=True)
            data = {
                'samples': [{'features': feats, 'label': label} for feats, label in rows],
                'updated': timezone.now().isoformat(),
                'n_features': n_features,
            }
            with open(output_json_path, 'w') as f:
                json.dump(data, f, indent=2)
            self.stdout.write(self.style.SUCCESS(f'Wrote {total_rows} samples to {output_json_path}'))

        if total_rows == 0:
            self.stdout.write(self.style.WARNING('No rows generated. Need more telemetry and/or alerts.'))
        elif not output_path and output_json_path:
            self.stdout.write(self.style.SUCCESS(f'Built {total_rows} samples (JSON only).'))
