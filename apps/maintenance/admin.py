"""
Admin configuration for Maintenance app.
"""

from django.contrib import admin

from .models import MaintenanceTask, MaintenanceDocument, MaintenanceComment


class MaintenanceDocumentInline(admin.TabularInline):
    model = MaintenanceDocument
    extra = 0
    readonly_fields = ['uploaded_at', 'file_size', 'file_type']


class MaintenanceCommentInline(admin.TabularInline):
    model = MaintenanceComment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'vehicle', 'maintenance_type', 'status',
        'priority', 'scheduled_date', 'assignee', 'created_at'
    ]
    list_filter = ['status', 'maintenance_type', 'priority', 'scheduled_date']
    search_fields = ['title', 'description', 'vehicle__license_plate']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MaintenanceDocumentInline, MaintenanceCommentInline]
    
    fieldsets = (
        ('Task Info', {'fields': ('title', 'description', 'vehicle', 'maintenance_type')}),
        ('Schedule', {'fields': ('scheduled_date', 'estimated_duration', 'status', 'priority')}),
        ('Completion', {'fields': ('completion_date', 'completion_notes', 'mileage_at_maintenance')}),
        ('Cost', {'fields': ('estimated_cost', 'actual_cost')}),
        ('Assignment', {'fields': ('assignee', 'created_by')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(MaintenanceDocument)
class MaintenanceDocumentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'task', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at']
    search_fields = ['filename', 'description']
    readonly_fields = ['uploaded_at', 'file_size', 'file_type']


@admin.register(MaintenanceComment)
class MaintenanceCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'content', 'created_at']
    search_fields = ['content']
    readonly_fields = ['created_at', 'updated_at']
