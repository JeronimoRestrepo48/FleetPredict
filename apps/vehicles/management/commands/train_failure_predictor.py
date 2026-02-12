"""
Train the ML failure predictor from CSV or JSON produced by build_ml_dataset.
Saves a joblib pipeline (scaler + classifier) to ML_FAILURE_PREDICTOR_PATH.
"""

import json
import os
import csv
import numpy as np
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Train failure predictor from build_ml_dataset CSV or JSON and save joblib pipeline.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            type=str,
            default=None,
            help='Input CSV path (default: dataset.csv if --input-json not set)',
        )
        parser.add_argument(
            '--input-json',
            type=str,
            default=None,
            help='Input JSON path for continuous learning (e.g. media/models/ml_training_data.json). Overrides --input.',
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Output joblib path (default: settings.ML_FAILURE_PREDICTOR_PATH)',
        )

    def handle(self, *args, **options):
        input_path = options['input']
        input_json_path = options['input_json']
        output_path = options['output'] or getattr(settings, 'ML_FAILURE_PREDICTOR_PATH', None)
        if not output_path:
            self.stderr.write(self.style.ERROR('ML_FAILURE_PREDICTOR_PATH not set and --output not given.'))
            return

        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline
            import joblib
        except ImportError as e:
            self.stderr.write(self.style.ERROR(f'Missing dependency: {e}'))
            return

        rows = []
        if input_json_path and os.path.isfile(input_json_path):
            with open(input_json_path) as f:
                data = json.load(f)
            samples = data.get('samples') or []
            for s in samples:
                feats = s.get('features')
                label = s.get('label')
                if feats is not None and label is not None:
                    try:
                        rows.append(([float(x) for x in feats], str(label).strip()))
                    except (ValueError, TypeError):
                        continue
        else:
            input_path = input_path or 'dataset.csv'
            if not os.path.isfile(input_path):
                self.stderr.write(self.style.ERROR(f'Input file not found: {input_path}'))
                return
            with open(input_path, newline='') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header or header[-1] != 'label':
                    self.stderr.write(self.style.ERROR('CSV must have last column "label".'))
                    return
                n_features = len(header) - 1
                for row in reader:
                    if len(row) != n_features + 1:
                        continue
                    try:
                        feats = [float(x) for x in row[:n_features]]
                        label = row[n_features].strip()
                        rows.append((feats, label))
                    except ValueError:
                        continue

        if not rows:
            self.stderr.write(self.style.ERROR('No valid rows in input.'))
            return

        X = np.array([r[0] for r in rows])
        y = np.array([r[1] for r in rows])
        classes = np.unique(y)

        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', RandomForestClassifier(n_estimators=100, random_state=42)),
        ])
        pipeline.fit(X, y)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)) or '.', exist_ok=True)
        joblib.dump(pipeline, output_path)
        self.stdout.write(self.style.SUCCESS(f'Saved pipeline to {output_path}'))

        # Basic metrics on training data (documented as same-data eval when data is scarce)
        from sklearn.metrics import accuracy_score, classification_report
        y_pred = pipeline.predict(X)
        acc = accuracy_score(y, y_pred)
        self.stdout.write(f'Training accuracy: {acc:.4f}')
        self.stdout.write(classification_report(y, y_pred, zero_division=0))
