"""
Dashboard app models.
FR8: Configurable alert thresholds (alert rules).
FR27: Audit log for user actions.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AlertRule(models.Model):
    """
    Global alert rule: when to trigger alerts (e.g. maintenance due in X days).
    FR8: Configurable alert thresholds.
    """
    RULE_TYPES = [
        ('maintenance_due_days', _('Maintenance due within (days)')),
        ('maintenance_overdue', _('Maintenance overdue alert')),
        ('compliance_expiring_days', _('Compliance expiring within (days)')),
        ('workorder_due_days', _('Work orders due within (days)')),
    ]
    name = models.CharField(max_length=64, unique=True, choices=RULE_TYPES)
    value_int = models.IntegerField(
        default=7,
        help_text='Numeric value (e.g. days)',
        null=True,
        blank=True,
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Alert Rule'
        verbose_name_plural = 'Alert Rules'
        ordering = ['name']

    def __str__(self):
        return f'{self.get_name_display()}: {self.value_int}'

    @classmethod
    def get_maintenance_due_days(cls):
        """Return configured days for "maintenance due" window (default 7)."""
        r = cls.objects.filter(name='maintenance_due_days', enabled=True).first()
        return r.value_int if r and r.value_int is not None else 7

    @classmethod
    def get_compliance_expiring_days(cls):
        """
        Return configured days for \"compliance expiring\" window.
        Default: 30 days if rule is missing or disabled.
        """
        r = cls.objects.filter(name='compliance_expiring_days', enabled=True).first()
        return r.value_int if r and r.value_int is not None else 30

    @classmethod
    def get_workorder_due_days(cls):
        """
        Return configured days for \"work orders due soon\" window.
        Default: 7 days if rule is missing or disabled.
        """
        r = cls.objects.filter(name='workorder_due_days', enabled=True).first()
        return r.value_int if r and r.value_int is not None else 7


class AlertThreshold(models.Model):
    """
    Configurable trigger/threshold for telemetry attributes.
    Users can create rules like "alert when engine_temperature_c >= 105".
    """
    ATTRIBUTES = [
        ('engine_temperature_c', _('Engine temperature (°C)')),
        ('fuel_level_pct', _('Fuel level (%)')),
        ('speed_kmh', _('Speed (km/h)')),
        ('rpm', _('Engine RPM')),
        ('mileage', _('Mileage (km)')),
        ('voltage', _('Battery voltage (V)')),
        ('throttle_pct', _('Throttle position (%)')),
    ]
    OPERATORS = [
        ('gte', _('≥ (greater or equal)')),
        ('lte', _('≤ (less or equal)')),
        ('gt', _('> (greater)')),
        ('lt', _('< (less)')),
    ]

    attribute = models.CharField(max_length=64, choices=ATTRIBUTES)
    operator = models.CharField(max_length=8, choices=OPERATORS)
    value_float = models.FloatField(help_text='Threshold value')
    severity = models.CharField(
        max_length=16,
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
            ('critical', _('Critical')),
        ],
        default='medium',
    )
    description = models.CharField(
        max_length=128,
        blank=True,
        help_text='Optional label for this rule (e.g. "Engine overheating warning")',
    )
    enabled = models.BooleanField(default=True)
    organization = models.ForeignKey(
        'users.Organization',
        on_delete=models.CASCADE,
        related_name='alert_thresholds',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Alert Threshold'
        verbose_name_plural = 'Alert Thresholds'
        ordering = ['attribute', 'value_float']

    def __str__(self):
        op_symbol = {'gte': '≥', 'lte': '≤', 'gt': '>', 'lt': '<'}.get(self.operator, self.operator)
        return f'{self.get_attribute_display()} {op_symbol} {self.value_float}'


class AuditLog(models.Model):
    """
    FR27: Audit log - record user actions for compliance and traceability.
    """
    ACTION_CHOICES = [
        ('create', _('Create')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('export', _('Export')),
        ('override', _('Override')),
        ('system', _('System event')),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    organization = models.ForeignKey(
        'users.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=64, blank=True, db_index=True)
    object_id = models.CharField(max_length=64, blank=True)
    message = models.CharField(max_length=500, blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_name', 'object_id'], name='audit_model_obj_idx'),
            models.Index(fields=['created_at'], name='audit_created_idx'),
        ]

    def __str__(self):
        return f'{self.action} {self.model_name} {self.object_id} @ {self.created_at}'


class DashboardLayout(models.Model):
    """
    FR28: Per-user customizable dashboard layout.
    Stores a JSON list of widget configs: [{widget_type, position, size}]
    """

    WIDGET_CHOICES = [
        ('vehicle_count', _('Vehicle Count')),
        ('status_summary', _('Status Summary')),
        ('recent_alerts', _('Recent Alerts')),
        ('upcoming_maintenance', _('Upcoming Maintenance')),
        ('health_overview', _('Health Overview')),
        ('cost_summary', _('Cost Summary')),
        ('chart_maintenance_trend', _('Maintenance Trend Chart')),
        ('chart_alerts_by_type', _('Alerts by Type Chart')),
        ('compliance_status', _('Compliance Status')),
        ('task_priority', _('Task Priority')),
    ]

    SIZE_CHOICES = [
        ('sm', _('Small (4 cols)')),
        ('md', _('Medium (6 cols)')),
        ('lg', _('Large (12 cols)')),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='dashboard_layout',
    )
    layout = models.JSONField(
        default=list,
        help_text='List of widget configs: [{widget_type, position, size}]',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dashboard Layout'

    def __str__(self):
        return f'Layout for {self.user}'

    @classmethod
    def get_default_layout(cls):
        return [
            {'widget_type': 'vehicle_count', 'position': 0, 'size': 'sm'},
            {'widget_type': 'health_overview', 'position': 1, 'size': 'sm'},
            {'widget_type': 'upcoming_maintenance', 'position': 2, 'size': 'sm'},
            {'widget_type': 'recent_alerts', 'position': 3, 'size': 'md'},
            {'widget_type': 'status_summary', 'position': 4, 'size': 'md'},
            {'widget_type': 'cost_summary', 'position': 5, 'size': 'sm'},
        ]
