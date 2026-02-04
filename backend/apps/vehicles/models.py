"""
Vehicle models for FleetPredict Pro.
Implements FR2: Vehicle registry.
"""

from django.db import models
from django.conf import settings


class VehicleType(models.Model):
    """
    Vehicle type/category with specific maintenance intervals.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    maintenance_interval_days = models.PositiveIntegerField(
        default=90,
        help_text='Default maintenance interval in days'
    )
    maintenance_interval_km = models.PositiveIntegerField(
        default=10000,
        help_text='Default maintenance interval in kilometers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Vehicle Type'
        verbose_name_plural = 'Vehicle Types'
        ordering = ['name']

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    """
    Fleet vehicle model.
    Implements FR2: Register and manage fleet vehicles.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        UNDER_MAINTENANCE = 'under_maintenance', 'Under Maintenance'
        RETIRED = 'retired', 'Retired'

    # Identification
    license_plate = models.CharField(max_length=20, unique=True)
    vin = models.CharField(
        max_length=17,
        unique=True,
        help_text='Vehicle Identification Number'
    )

    # Basic information
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    color = models.CharField(max_length=50, blank=True)

    # Classification
    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.PROTECT,
        related_name='vehicles',
        null=True,
        blank=True
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    # Operational data
    current_mileage = models.PositiveIntegerField(
        default=0,
        help_text='Current mileage in kilometers'
    )
    fuel_type = models.CharField(max_length=50, blank=True)
    fuel_capacity = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Fuel capacity in liters'
    )

    # Assignment
    assigned_driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_vehicles',
        limit_choices_to={'role': 'driver'}
    )

    # Notes
    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_vehicles'
    )

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.make} {self.model} ({self.license_plate})'

    @property
    def display_name(self):
        """Return a display-friendly name for the vehicle."""
        return f'{self.year} {self.make} {self.model}'

    @property
    def is_active(self):
        """Check if vehicle is active."""
        return self.status == self.Status.ACTIVE

    @property
    def is_under_maintenance(self):
        """Check if vehicle is under maintenance."""
        return self.status == self.Status.UNDER_MAINTENANCE

    def soft_delete(self):
        """Perform soft delete instead of actual deletion."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.status = self.Status.RETIRED
        self.save()

    def get_maintenance_count(self):
        """Get the total number of maintenance records."""
        return self.maintenance_tasks.count()

    def get_last_maintenance_date(self):
        """Get the date of the last completed maintenance."""
        last_task = self.maintenance_tasks.filter(
            status='completed'
        ).order_by('-completion_date').first()
        return last_task.completion_date if last_task else None


class VehicleManager(models.Manager):
    """Custom manager for Vehicle model."""

    def active(self):
        """Return only non-deleted vehicles."""
        return self.filter(is_deleted=False)

    def by_status(self, status):
        """Return vehicles by status."""
        return self.active().filter(status=status)
