"""
Admin configuration for Vehicles app.
"""

from django.contrib import admin

from .models import Vehicle, VehicleType


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'maintenance_interval_days', 'maintenance_interval_km', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        'license_plate', 'make', 'model', 'year',
        'vehicle_type', 'status', 'current_mileage', 'is_deleted'
    ]
    list_filter = ['status', 'vehicle_type', 'make', 'is_deleted']
    search_fields = ['license_plate', 'vin', 'make', 'model']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        ('Identification', {'fields': ('license_plate', 'vin')}),
        ('Details', {'fields': ('make', 'model', 'year', 'color', 'vehicle_type')}),
        ('Status', {'fields': ('status', 'current_mileage', 'fuel_type', 'fuel_capacity')}),
        ('Assignment', {'fields': ('assigned_driver', 'notes')}),
        ('Metadata', {'fields': ('created_by', 'created_at', 'updated_at', 'is_deleted', 'deleted_at')}),
    )
