"""
Serializers for Maintenance app.
Implements FR4 (Maintenance management system) and FR5 (Maintenance history per vehicle).
"""

from rest_framework import serializers
from django.utils import timezone

from .models import MaintenanceTask, MaintenanceDocument, MaintenanceComment
from apps.users.serializers import UserListSerializer
from apps.vehicles.serializers import VehicleListSerializer


class MaintenanceDocumentSerializer(serializers.ModelSerializer):
    """Serializer for MaintenanceDocument model."""

    uploaded_by = UserListSerializer(read_only=True)

    class Meta:
        model = MaintenanceDocument
        fields = [
            'id', 'file', 'filename', 'description',
            'file_type', 'file_size', 'uploaded_by', 'uploaded_at'
        ]
        read_only_fields = ['id', 'filename', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at']


class MaintenanceCommentSerializer(serializers.ModelSerializer):
    """Serializer for MaintenanceComment model."""

    user = UserListSerializer(read_only=True)

    class Meta:
        model = MaintenanceComment
        fields = ['id', 'user', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class MaintenanceTaskListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing maintenance tasks."""

    vehicle_display = serializers.CharField(
        source='vehicle.display_name',
        read_only=True
    )
    vehicle_license_plate = serializers.CharField(
        source='vehicle.license_plate',
        read_only=True
    )
    assignee_name = serializers.CharField(
        source='assignee.get_full_name',
        read_only=True,
        allow_null=True
    )
    is_overdue = serializers.BooleanField(read_only=True)
    documents_count = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceTask
        fields = [
            'id', 'title', 'vehicle', 'vehicle_display', 'vehicle_license_plate',
            'maintenance_type', 'status', 'priority', 'scheduled_date',
            'completion_date', 'assignee', 'assignee_name', 'is_overdue',
            'estimated_cost', 'actual_cost', 'documents_count', 'created_at'
        ]

    def get_documents_count(self, obj):
        return obj.documents.count()


class MaintenanceTaskDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single maintenance task."""

    vehicle = VehicleListSerializer(read_only=True)
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset='apps.vehicles.Vehicle.objects.filter(is_deleted=False)',
        source='vehicle',
        write_only=True
    )
    assignee = UserListSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset='apps.users.User.objects.all()',
        source='assignee',
        write_only=True,
        required=False,
        allow_null=True
    )
    created_by = UserListSerializer(read_only=True)
    documents = MaintenanceDocumentSerializer(many=True, read_only=True)
    comments = MaintenanceCommentSerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = MaintenanceTask
        fields = [
            'id', 'title', 'description', 'vehicle', 'vehicle_id',
            'maintenance_type', 'status', 'priority',
            'scheduled_date', 'estimated_duration',
            'completion_date', 'completion_notes',
            'estimated_cost', 'actual_cost', 'mileage_at_maintenance',
            'assignee', 'assignee_id', 'created_by',
            'is_overdue', 'documents', 'comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fix the querysets
        from apps.vehicles.models import Vehicle
        from apps.users.models import User
        self.fields['vehicle_id'] = serializers.PrimaryKeyRelatedField(
            queryset=Vehicle.objects.filter(is_deleted=False),
            source='vehicle',
            write_only=True
        )
        self.fields['assignee_id'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            source='assignee',
            write_only=True,
            required=False,
            allow_null=True
        )


class MaintenanceTaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating maintenance tasks."""

    class Meta:
        model = MaintenanceTask
        fields = [
            'title', 'description', 'vehicle', 'maintenance_type',
            'priority', 'scheduled_date', 'estimated_duration',
            'estimated_cost', 'assignee'
        ]

    def validate_scheduled_date(self, value):
        """Validate scheduled date is not in the past (warning only)."""
        if value < timezone.now().date():
            # Allow but issue warning via context
            pass
        return value

    def validate_vehicle(self, value):
        """Validate vehicle is not deleted."""
        if value.is_deleted:
            raise serializers.ValidationError('Cannot create task for deleted vehicle.')
        return value

    def create(self, validated_data):
        """Create task with current user as creator."""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class MaintenanceTaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating maintenance tasks."""

    class Meta:
        model = MaintenanceTask
        fields = [
            'title', 'description', 'maintenance_type', 'priority',
            'scheduled_date', 'estimated_duration', 'estimated_cost',
            'assignee', 'status'
        ]


class MaintenanceTaskCompleteSerializer(serializers.Serializer):
    """Serializer for completing a maintenance task."""

    completion_notes = serializers.CharField(required=False, allow_blank=True)
    actual_cost = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    mileage_at_maintenance = serializers.IntegerField(required=False, allow_null=True)


class MaintenanceTaskStatusSerializer(serializers.Serializer):
    """Serializer for changing task status."""

    status = serializers.ChoiceField(choices=MaintenanceTask.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True)
