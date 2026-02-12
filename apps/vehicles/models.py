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

    # Last telemetry timestamp (updated when telemetry is received)
    last_telemetry_at = models.DateTimeField(null=True, blank=True)

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

    def is_engine_on(self, threshold_seconds=90):
        """True if last telemetry was within threshold_seconds (vehicle considered on)."""
        from django.utils import timezone
        if not self.last_telemetry_at:
            return False
        delta = (timezone.now() - self.last_telemetry_at).total_seconds()
        return delta < threshold_seconds

    def get_health_status(self, alert_days=7):
        """
        Return 'red' | 'yellow' | 'green' for FR6 health indicator.
        Red: critical unread alert in last alert_days, or overdue maintenance.
        Yellow: high unread alert, or maintenance due soon, or recent anomalous telemetry.
        Green: otherwise.
        """
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        since = now - timedelta(days=alert_days)

        # Red: critical unread alert or overdue maintenance
        if self.alerts.filter(
            severity=VehicleAlert.Severity.CRITICAL,
            read_at__isnull=True,
            created_at__gte=since,
        ).exists():
            return 'red'
        overdue = self.maintenance_tasks.filter(
            status__in=['scheduled', 'overdue'],
            scheduled_date__lt=now.date(),
        ).exists()
        if overdue:
            return 'red'

        # Yellow: high unread alert
        if self.alerts.filter(
            severity=VehicleAlert.Severity.HIGH,
            read_at__isnull=True,
            created_at__gte=since,
        ).exists():
            return 'yellow'
        # Maintenance due soon (within VehicleType buffer or next 14 days)
        next_due = now.date() + timedelta(days=14)
        if self.maintenance_tasks.filter(
            status__in=['scheduled', 'overdue'],
            scheduled_date__lte=next_due,
        ).exists():
            return 'yellow'
        # Recent anomalous telemetry (high temp in last 24h, threshold 105 C)
        from django.conf import settings
        day_ago = now - timedelta(hours=24)
        thresh = getattr(settings, 'TELEMETRY_PATTERNS_ENGINE_TEMP_HIGH_C', 105)
        if self.telemetry_readings.filter(
            timestamp__gte=day_ago,
            engine_temperature_c__gte=thresh,
        ).exists():
            return 'yellow'

        return 'green'

    def get_health_status_reasons(self, alert_days=7):
        """
        Return a list of human-readable reasons for the current health status.
        Used for tooltip/modal explanation (FR6).
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.conf import settings
        now = timezone.now()
        since = now - timedelta(days=alert_days)
        reasons = []

        if self.alerts.filter(
            severity=VehicleAlert.Severity.CRITICAL,
            read_at__isnull=True,
            created_at__gte=since,
        ).exists():
            reasons.append('Alerta crítica sin leer')
        overdue = self.maintenance_tasks.filter(
            status__in=['scheduled', 'overdue'],
            scheduled_date__lt=now.date(),
        )
        if overdue.exists():
            reasons.append('Mantenimiento vencido')
        if reasons:
            return ('red', reasons)

        if self.alerts.filter(
            severity=VehicleAlert.Severity.HIGH,
            read_at__isnull=True,
            created_at__gte=since,
        ).exists():
            reasons.append('Alerta alta sin leer')
        next_due = now.date() + timedelta(days=14)
        if self.maintenance_tasks.filter(
            status__in=['scheduled', 'overdue'],
            scheduled_date__lte=next_due,
        ).exists():
            reasons.append('Mantenimiento próximo (14 días)')
        day_ago = now - timedelta(hours=24)
        thresh = getattr(settings, 'TELEMETRY_PATTERNS_ENGINE_TEMP_HIGH_C', 105)
        if self.telemetry_readings.filter(
            timestamp__gte=day_ago,
            engine_temperature_c__gte=thresh,
        ).exists():
            reasons.append('Telemetría: temperatura alta reciente')
        if reasons:
            return ('yellow', reasons)
        return ('green', ['Sin problemas detectados.'])

    @property
    def health_status(self):
        """FR6: expose get_health_status() as property for templates."""
        return self.get_health_status()


class VehicleTelemetry(models.Model):
    """
    Time-series telemetry readings from vehicle sensors.
    Used for real-time monitoring and pattern/AI evaluation.
    """
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='telemetry_readings'
    )
    timestamp = models.DateTimeField(db_index=True)

    # Core telemetry
    speed_kmh = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Speed in km/h'
    )
    fuel_level_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Fuel level percentage 0-100'
    )
    engine_temperature_c = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Engine temperature in Celsius'
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    rpm = models.PositiveIntegerField(null=True, blank=True, help_text='Engine RPM')
    mileage = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Odometer reading in km'
    )

    # Optional for driving patterns
    voltage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Battery voltage'
    )
    throttle_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Throttle position percentage'
    )
    brake_status = models.BooleanField(null=True, blank=True, help_text='Brake pedal pressed')

    class Meta:
        verbose_name = 'Vehicle Telemetry'
        verbose_name_plural = 'Vehicle Telemetry'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['vehicle', 'timestamp'], name='veh_telem_vehicle_ts_idx'),
        ]

    def __str__(self):
        return f'{self.vehicle_id} @ {self.timestamp}'


class VehicleAlert(models.Model):
    """
    Alerts and prediction events from pattern/AI evaluation.
    Feeds FR6 (health), FR7 (notifications), FR9 (failure prediction).
    """
    class AlertType(models.TextChoices):
        HIGH_ENGINE_TEMP = 'high_engine_temp', 'High engine temperature'
        ANOMALOUS_FUEL = 'anomalous_fuel', 'Anomalous fuel consumption'
        HARSH_DRIVING = 'harsh_driving', 'Harsh driving'
        PROLONGED_IDLE = 'prolonged_idle', 'Prolonged idling'
        MAINTENANCE_MILEAGE = 'maintenance_mileage', 'Maintenance due by mileage'
        MAINTENANCE_TIME = 'maintenance_time', 'Maintenance due by time'
        STATISTICAL_ANOMALY = 'statistical_anomaly', 'Statistical anomaly'

    class Severity(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    alert_type = models.CharField(max_length=32, choices=AlertType.choices)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.MEDIUM)
    message = models.TextField()
    confidence = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='0-1 confidence score'
    )
    timeframe_text = models.CharField(
        max_length=128,
        blank=True,
        help_text='e.g. "Próximos 7 días", "En 500 km" (FR9)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    # FR11: Suggested maintenance - accept (create task) or dismiss
    suggestion_status = models.CharField(
        max_length=16,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('dismissed', 'Dismissed'),
        ],
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Vehicle Alert'
        verbose_name_plural = 'Vehicle Alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vehicle', 'created_at'], name='veh_alert_vehicle_ts_idx'),
        ]

    def __str__(self):
        return f'{self.vehicle_id} {self.alert_type} @ {self.created_at}'


class Playbook(models.Model):
    """Suggested steps for an alert type (SOC playbook)."""
    alert_type = models.CharField(
        max_length=32,
        choices=VehicleAlert.AlertType.choices,
        unique=True,
        help_text='Alert type this playbook applies to',
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    steps = models.JSONField(
        default=list,
        help_text='List of step strings (e.g. ["Check coolant", "Schedule inspection"])',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Playbook'
        verbose_name_plural = 'Playbooks'
        ordering = ['alert_type']

    def __str__(self):
        return f'{self.name} ({self.get_alert_type_display()})'


class Runbook(models.Model):
    """Executable action for alerts (SOC runbook)."""
    class ActionType(models.TextChoices):
        MARK_ALERT_READ = 'mark_alert_read', 'Mark alert as read'
        CREATE_MAINTENANCE_TASK = 'create_maintenance_task', 'Create maintenance task'
        DISMISS_ALERT = 'dismiss_alert', 'Dismiss alert'

    name = models.CharField(max_length=200)
    alert_type = models.CharField(
        max_length=32,
        choices=VehicleAlert.AlertType.choices,
        null=True,
        blank=True,
        help_text='Optional: only for this alert type',
    )
    action_type = models.CharField(max_length=32, choices=ActionType.choices)
    params = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Runbook'
        verbose_name_plural = 'Runbooks'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_action_type_display()})'

    def execute(self, alert, user):
        """Execute this runbook for the given alert. Returns (success: bool, message: str)."""
        from django.utils import timezone
        if self.action_type == self.ActionType.MARK_ALERT_READ:
            alert.read_at = timezone.now()
            alert.save(update_fields=['read_at'])
            return True, 'Alert marked as read.'
        if self.action_type == self.ActionType.DISMISS_ALERT:
            alert.read_at = timezone.now()
            alert.save(update_fields=['read_at'])
            return True, 'Alert dismissed.'
        if self.action_type == self.ActionType.CREATE_MAINTENANCE_TASK:
            from apps.maintenance.models import MaintenanceTask
            from datetime import timedelta
            task = MaintenanceTask(
                vehicle=alert.vehicle,
                title=self.params.get('title', f'Follow-up: {alert.get_alert_type_display()}'),
                description=self.params.get('description', alert.message),
                maintenance_type=self.params.get('maintenance_type', 'preventive'),
                scheduled_date=(timezone.now() + timedelta(days=self.params.get('days_ahead', 1))).date(),
                status=MaintenanceTask.Status.SCHEDULED,
                priority=self.params.get('priority', 'medium'),
                created_by=user,
            )
            task.save()
            return True, f'Maintenance task created: {task.title}'
        return False, 'Unknown action type.'


class ComplianceRequirement(models.Model):
    """
    Regulatory compliance requirement per vehicle (FR25).
    Inspections, certifications, licenses, registrations with expiration alerts.
    """

    class Type(models.TextChoices):
        INSPECTION = 'inspection', 'Inspection'
        CERTIFICATION = 'certification', 'Certification'
        LICENSE = 'license', 'License'
        REGISTRATION = 'registration', 'Registration'
        INSURANCE = 'insurance', 'Insurance'
        OTHER = 'other', 'Other'

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='compliance_requirements',
    )
    requirement_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.INSPECTION,
    )
    name = models.CharField(max_length=200, help_text='Short name (e.g. Annual inspection)')
    expiration_date = models.DateField()
    issuing_authority = models.CharField(max_length=200, blank=True)
    document_reference = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Compliance Requirement'
        verbose_name_plural = 'Compliance Requirements'
        ordering = ['expiration_date']

    def __str__(self):
        return f'{self.name} - {self.vehicle} (exp: {self.expiration_date})'

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expiration_date < timezone.now().date()

    @property
    def days_until_expiry(self):
        from django.utils import timezone
        delta = self.expiration_date - timezone.now().date()
        return delta.days


class VehicleManager(models.Manager):
    """Custom manager for Vehicle model."""

    def active(self):
        """Return only non-deleted vehicles."""
        return self.filter(is_deleted=False)

    def by_status(self, status):
        """Return vehicles by status."""
        return self.active().filter(status=status)
