# Generated manually for multi-tenant backfill

from django.db import migrations


def backfill_organizations(apps, schema_editor):
    Organization = apps.get_model('users', 'Organization')
    User = apps.get_model('users', 'User')
    Vehicle = apps.get_model('vehicles', 'Vehicle')
    VehicleType = apps.get_model('vehicles', 'VehicleType')
    AlertThreshold = apps.get_model('dashboard', 'AlertThreshold')
    SparePart = apps.get_model('inventory', 'SparePart')
    Supplier = apps.get_model('inventory', 'Supplier')

    org, _ = Organization.objects.get_or_create(
        slug='default-company',
        defaults={'name': 'Default company'},
    )
    User.objects.filter(is_superuser=False).update(organization=org)
    User.objects.filter(is_superuser=True).update(organization=None)
    Vehicle.objects.filter(organization__isnull=True).update(organization=org)
    VehicleType.objects.filter(organization__isnull=True).update(organization=org)
    AlertThreshold.objects.filter(organization__isnull=True).update(organization=org)
    SparePart.objects.filter(organization__isnull=True).update(organization=org)
    Supplier.objects.filter(organization__isnull=True).update(organization=org)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('vehicles', '0012_vehicle_organization_vehicletype_organization_and_more'),
        ('dashboard', '0007_alertthreshold_organization_auditlog_organization'),
        ('inventory', '0003_sparepart_organization_supplier_organization_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_organizations, noop_reverse),
    ]
