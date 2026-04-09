"""
FR20: Spare Parts and Inventory Management.
FR26: Supplier Management.
"""
from django.db import models
from django.conf import settings


class SparePart(models.Model):
    """A spare part in inventory."""

    class Category(models.TextChoices):
        ENGINE = 'engine', 'Engine'
        BRAKES = 'brakes', 'Brakes'
        TIRES = 'tires', 'Tires'
        ELECTRICAL = 'electrical', 'Electrical'
        TRANSMISSION = 'transmission', 'Transmission'
        SUSPENSION = 'suspension', 'Suspension'
        FLUIDS = 'fluids', 'Fluids & Filters'
        BODY = 'body', 'Body & Exterior'
        OTHER = 'other', 'Other'

    name = models.CharField(max_length=200)
    part_number = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    description = models.TextField(blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_point = models.PositiveIntegerField(default=5, help_text='Alert when stock falls below this')
    current_stock = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.part_number})'

    @property
    def is_low_stock(self):
        return self.current_stock < self.reorder_point


class StockMovement(models.Model):
    """Records changes to spare part stock levels."""

    class MovementType(models.TextChoices):
        IN = 'in', 'Stock In'
        OUT = 'out', 'Stock Out'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=12, choices=MovementType.choices)
    quantity = models.IntegerField()
    maintenance_task = models.ForeignKey(
        'maintenance.MaintenanceTask', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='stock_movements',
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_movement_type_display()} {self.quantity} x {self.spare_part.name}'


class PartUsage(models.Model):
    """Links parts used in a maintenance task."""

    maintenance_task = models.ForeignKey(
        'maintenance.MaintenanceTask', on_delete=models.CASCADE, related_name='part_usages',
    )
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='usages')
    quantity_used = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('maintenance_task', 'spare_part')

    def __str__(self):
        return f'{self.quantity_used} x {self.spare_part.name}'


class Supplier(models.Model):
    """FR26: Supplier information."""

    name = models.CharField(max_length=200, unique=True)
    contact_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    delivery_terms = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, help_text='1-5')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SupplierPart(models.Model):
    """FR26: Links a supplier to a spare part with pricing."""

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='supplied_parts')
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='supplier_links')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    lead_time_days = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('supplier', 'spare_part')

    def __str__(self):
        return f'{self.supplier.name} -> {self.spare_part.name} @ ${self.unit_price}'
