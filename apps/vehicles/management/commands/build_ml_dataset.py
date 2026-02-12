"""
Build ML dataset from historical telemetry and alerts.
Slides over time per vehicle, forms windows of W readings, labels from VehicleAlert
within a short delay after window end, else "normal". Writes CSV: features_1,...,features_K,label.
"""

import csv
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
    help = 'Build ML dataset CSV from telemetry windows and alert labels.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='dataset.csv',
            help='Output CSV path (default: dataset.csv)',
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
        output_path = options['output']
        days = options['days']
        window_size = options['window_size'] or getattr(settings, 'ML_WINDOW_SIZE', 20)
        step = max(1, options['step_readings'])
        since = timezone.now() - timedelta(days=days)
        label_delta = timedelta(minutes=LABEL_DELTA_MINUTES)

        vehicles = Vehicle.objects.filter(is_deleted=False).values_list('id', flat=True)
        n_features = extract_features([]).size
        total_rows = 0

        os.makedirs(os.path.dirname(os.path.abspath(output_path)) or '.', exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            header = [f'f{i}' for i in range(n_features)] + ['label']
            writer.writerow(header)

            for vehicle_id in vehicles:
                # All telemetry for this vehicle in range, ordered desc (newest first)
                readings_qs = (
                    VehicleTelemetry.objects.filter(vehicle_id=vehicle_id, timestamp__gte=since)
                    .order_by('-timestamp')
                )
                all_readings = list(readings_qs)
                if len(all_readings) < window_size:
                    continue
                # Alerts for this vehicle in the same time range (for labeling)
                alerts_in_range = list(
                    VehicleAlert.objects.filter(
                        vehicle_id=vehicle_id,
                        created_at__gte=since,
                    ).order_by('created_at')
                )

                # Slide: start at index 0, then step, then 2*step, ... while we have a full window
                idx = 0
                while idx + window_size <= len(all_readings):
                    window = all_readings[idx : idx + window_size]
                    last_ts = window[-1].timestamp
                    # Label: any alert created within label_delta after last_ts?
                    label = 'normal'
                    for alert in alerts_in_range:
                        if alert.created_at >= last_ts and (alert.created_at - last_ts) <= label_delta:
                            label = alert.alert_type
                            break
                    feats = extract_features(window)
                    row = feats.tolist() + [label]
                    writer.writerow(row)
                    total_rows += 1
                    idx += step

        self.stdout.write(self.style.SUCCESS(f'Wrote {total_rows} rows to {output_path}'))
