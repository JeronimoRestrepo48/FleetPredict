"""
Maintenance models for FleetPredict Pro.
Implements FR4 (Maintenance management system) and FR5 (Maintenance history per vehicle).
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class MaintenanceTask(models.Model):
    """
    Maintenance task model.
    Implements FR4: Plan, record, and track maintenance tasks.
    """

    class Type(models.TextChoices):
        PREVENTIVE = 'preventive', 'Preventive'
        CORRECTIVE = 'corrective', 'Corrective'
        INSPECTION = 'inspection', 'Inspection'
        EMERGENCY = 'emergency', 'Emergency'

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        OVERDUE = 'overdue', 'Overdue'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    # Relationships
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='maintenance_tasks'
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )

    # Task details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    maintenance_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.PREVENTIVE
    )

    # Scheduling
    scheduled_date = models.DateField()
    estimated_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Estimated duration in minutes'
    )

    # Status and priority
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )

    # Completion
    completion_date = models.DateField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)

    # Cost tracking
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Mileage at maintenance
    mileage_at_maintenance = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Vehicle mileage when maintenance was performed'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Maintenance Task'
        verbose_name_plural = 'Maintenance Tasks'
        ordering = ['-scheduled_date', '-created_at']

    def __str__(self):
        return f'{self.title} - {self.vehicle}'

    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if self.status in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return False
        return self.scheduled_date < timezone.now().date()

    def mark_in_progress(self):
        """Mark task as in progress."""
        self.status = self.Status.IN_PROGRESS
        self.save()

    def mark_completed(self, completion_notes='', actual_cost=None, mileage=None):
        """Mark task as completed."""
        self.status = self.Status.COMPLETED
        self.completion_date = timezone.now().date()
        self.completion_notes = completion_notes
        if actual_cost is not None:
            self.actual_cost = actual_cost
        if mileage is not None:
            self.mileage_at_maintenance = mileage
        self.save()

    def mark_cancelled(self, reason=''):
        """Mark task as cancelled."""
        self.status = self.Status.CANCELLED
        self.completion_notes = reason
        self.save()

    def check_overdue(self):
        """Update status to overdue if applicable."""
        if self.is_overdue and self.status == self.Status.SCHEDULED:
            self.status = self.Status.OVERDUE
            self.save()
            return True
        return False


class MaintenanceTemplate(models.Model):
    """
    Reusable maintenance template (FR23).
    Apply when creating a task to pre-fill title, type, duration, description.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    maintenance_type = models.CharField(
        max_length=20,
        choices=MaintenanceTask.Type.choices,
        default=MaintenanceTask.Type.PREVENTIVE,
    )
    estimated_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Estimated duration in minutes',
    )
    steps = models.JSONField(
        default=list,
        blank=True,
        help_text='List of step strings (checklist)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Maintenance Template'
        verbose_name_plural = 'Maintenance Templates'
        ordering = ['name']

    def __str__(self):
        return self.name


class MaintenanceDocument(models.Model):
    """
    Document/attachment for maintenance tasks.
    Implements FR5: Upload and attach documents/files to maintenance records.
    """

    task = models.ForeignKey(
        MaintenanceTask,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    file = models.FileField(upload_to='maintenance_documents/')
    filename = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True)
    file_type = models.CharField(max_length=50, blank=True)
    file_size = models.PositiveIntegerField(
        default=0,
        help_text='File size in bytes'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Maintenance Document'
        verbose_name_plural = 'Maintenance Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.filename} - {self.task}'

    def save(self, *args, **kwargs):
        """Set filename and file type from the uploaded file."""
        if self.file:
            self.filename = self.file.name
            self.file_size = self.file.size
            # Extract file extension
            if '.' in self.file.name:
                self.file_type = self.file.name.split('.')[-1].lower()
        super().save(*args, **kwargs)


class MaintenanceComment(models.Model):
    """
    Comments/notes on maintenance tasks.
    """

    task = models.ForeignKey(
        MaintenanceTask,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Maintenance Comment'
        verbose_name_plural = 'Maintenance Comments'
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.user} on {self.task}'


class WorkOrder(models.Model):
    """
    Work order linked to a maintenance task (FR24).
    Tracks status, assignee, due date, completion, and notes.
    """

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    task = models.OneToOneField(
        MaintenanceTask,
        on_delete=models.CASCADE,
        related_name='work_order',
        unique=True,
    )
    work_order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders',
    )
    priority = models.CharField(
        max_length=20,
        choices=MaintenanceTask.Priority.choices,
        default=MaintenanceTask.Priority.MEDIUM,
    )
    due_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Work Order'
        verbose_name_plural = 'Work Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.work_order_number} - {self.task.title}'

    @property
    def is_overdue(self):
        if self.status in (self.Status.COMPLETED, self.Status.CANCELLED):
            return False
        if self.due_date:
            return self.due_date < timezone.now().date()
        return False

    def save(self, *args, **kwargs):
        if not self.work_order_number:
            from django.db.models import Max
            year = timezone.now().year
            prefix = f'WO-{year}-'
            last = WorkOrder.objects.filter(
                work_order_number__startswith=prefix
            ).aggregate(Max('work_order_number'))['work_order_number__max']
            if last:
                try:
                    num = int(last.split('-')[-1]) + 1
                except (IndexError, ValueError):
                    num = 1
            else:
                num = 1
            self.work_order_number = f'{prefix}{num:04d}'
        super().save(*args, **kwargs)
