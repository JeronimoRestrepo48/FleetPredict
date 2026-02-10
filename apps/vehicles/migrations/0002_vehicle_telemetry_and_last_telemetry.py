# Generated manually for existing DB: add last_telemetry_at and VehicleTelemetry
# 0001 was faked; this applies only DB changes.

from django.db import migrations


def apply_sqlite(apps, schema_editor):
    """Add last_telemetry_at column and create VehicleTelemetry table for existing DB."""
    if schema_editor.connection.vendor != 'sqlite':
        return
    with schema_editor.connection.cursor() as c:
        # Add last_telemetry_at to vehicles_vehicle if missing
        c.execute("PRAGMA table_info(vehicles_vehicle)")
        cols = [row[1] for row in c.fetchall()]
        if 'last_telemetry_at' not in cols:
            c.execute(
                "ALTER TABLE vehicles_vehicle ADD COLUMN last_telemetry_at TEXT NULL"
            )
        # Create VehicleTelemetry table if missing
        c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles_vehicletelemetry'"
        )
        if not c.fetchone():
            c.execute("""
                CREATE TABLE vehicles_vehicletelemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    timestamp TEXT NOT NULL,
                    speed_kmh REAL NULL,
                    fuel_level_pct REAL NULL,
                    engine_temperature_c REAL NULL,
                    latitude REAL NULL,
                    longitude REAL NULL,
                    rpm INTEGER NULL,
                    mileage INTEGER NULL,
                    voltage REAL NULL,
                    throttle_pct REAL NULL,
                    brake_status INTEGER NULL,
                    vehicle_id INTEGER NOT NULL REFERENCES vehicles_vehicle(id) ON DELETE CASCADE
                )
            """)
            c.execute(
                "CREATE INDEX veh_telem_vehicle_ts_idx ON vehicles_vehicletelemetry (vehicle_id, timestamp)"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0001_telemetry_and_last_telemetry'),
    ]

    operations = [
        migrations.RunPython(apply_sqlite, migrations.RunPython.noop),
    ]
