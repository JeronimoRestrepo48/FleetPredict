"""Commercial reporting and export models."""

from django.conf import settings
from django.db import models


class ReportSchedule(models.Model):
    """Saved report schedule metadata for future automated delivery."""

    FREQUENCIES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    name = models.CharField(max_length=120)
    report_type = models.CharField(max_length=64)
    filters = models.JSONField(default=dict, blank=True)
    frequency = models.CharField(max_length=16, choices=FREQUENCIES, default='weekly')
    recipients = models.TextField(blank=True, help_text='Comma-separated email list')
    enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ExportJob(models.Model):
    """History of exports requested through the Sprint 4 Export Center."""

    DATASETS = [
        ('vehicles', 'Vehicles'),
        ('maintenance', 'Maintenance'),
        ('predictions', 'Predictions'),
        ('inventory', 'Inventory'),
        ('suppliers', 'Suppliers'),
        ('audit', 'Audit Log'),
        ('sensors', 'Sensor Readings'),
        ('gps', 'GPS Readings'),
    ]
    FORMATS = [
        ('csv', 'CSV'),
        ('xlsx', 'Excel-compatible CSV'),
    ]
    STATUSES = [
        ('completed', 'Completed'),
        ('queued', 'Queued'),
        ('failed', 'Failed'),
    ]

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    dataset = models.CharField(max_length=32, choices=DATASETS)
    export_format = models.CharField(max_length=8, choices=FORMATS, default='csv')
    filters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=STATUSES, default='completed')
    row_count = models.PositiveIntegerField(default=0)
    filename = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_dataset_display()} export by {self.requested_by}'

