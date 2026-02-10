"""
Admin configuration for Vehicles app.
"""

from django.contrib import admin

from .models import Vehicle, VehicleType, VehicleTelemetry, VehicleAlert, Playbook, Runbook


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
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'last_telemetry_at']

    fieldsets = (
        ('Identification', {'fields': ('license_plate', 'vin')}),
        ('Details', {'fields': ('make', 'model', 'year', 'color', 'vehicle_type')}),
        ('Status', {'fields': ('status', 'current_mileage', 'fuel_type', 'fuel_capacity')}),
        ('Assignment', {'fields': ('assigned_driver', 'notes')}),
        ('Metadata', {'fields': ('created_by', 'created_at', 'updated_at', 'last_telemetry_at', 'is_deleted', 'deleted_at')}),
    )


@admin.register(VehicleTelemetry)
class VehicleTelemetryAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'timestamp', 'speed_kmh', 'fuel_level_pct', 'engine_temperature_c', 'mileage']
    list_filter = ['vehicle']
    search_fields = ['vehicle__license_plate', 'vehicle__vin']
    readonly_fields = ['vehicle', 'timestamp', 'speed_kmh', 'fuel_level_pct', 'engine_temperature_c',
                       'latitude', 'longitude', 'rpm', 'mileage', 'voltage', 'throttle_pct', 'brake_status']
    date_hierarchy = 'timestamp'


@admin.register(VehicleAlert)
class VehicleAlertAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'alert_type', 'severity', 'message', 'confidence', 'created_at', 'read_at']
    list_filter = ['alert_type', 'severity']
    search_fields = ['vehicle__license_plate', 'message']
    readonly_fields = ['vehicle', 'alert_type', 'severity', 'message', 'confidence', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(Playbook)
class PlaybookAdmin(admin.ModelAdmin):
    list_display = ['name', 'alert_type', 'created_at']
    list_filter = ['alert_type']


@admin.register(Runbook)
class RunbookAdmin(admin.ModelAdmin):
    list_display = ['name', 'alert_type', 'action_type', 'is_active', 'created_at']
    list_filter = ['action_type', 'alert_type', 'is_active']
