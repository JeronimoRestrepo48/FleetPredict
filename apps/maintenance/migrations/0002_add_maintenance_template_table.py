# Add MaintenanceTemplate table (0001 was faked; Task/Document/Comment already existed)

from django.db import migrations


def create_template_table(apps, schema_editor):
    """Create maintenance_maintenancetemplate table; model already in state from 0001."""
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_maintenancetemplate (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                maintenance_type TEXT NOT NULL DEFAULT 'preventive',
                estimated_duration INTEGER NULL,
                steps TEXT NOT NULL DEFAULT '[]',
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0001_maintenance_template'),
    ]

    operations = [
        migrations.RunPython(create_template_table, migrations.RunPython.noop),
    ]
