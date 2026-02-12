"""
Dashboard app models.
FR8: Configurable alert thresholds (alert rules).
FR27: Audit log for user actions.
"""

from django.conf import settings
from django.db import models


class AlertRule(models.Model):
    """
    Global alert rule: when to trigger alerts (e.g. maintenance due in X days).
    FR8: Configurable alert thresholds.
    """
    RULE_TYPES = [
        ('maintenance_due_days', 'Maintenance due within (days)'),
        ('maintenance_overdue', 'Maintenance overdue alert'),
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


class AuditLog(models.Model):
    """
    FR27: Audit log - record user actions for compliance and traceability.
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=64, blank=True, db_index=True)
    object_id = models.CharField(max_length=64, blank=True)
    message = models.CharField(max_length=500, blank=True)
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
