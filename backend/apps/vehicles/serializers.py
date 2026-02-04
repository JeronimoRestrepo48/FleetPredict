"""
Serializers for Vehicles app.
Implements FR2: Vehicle registry.
"""

from rest_framework import serializers

from .models import Vehicle, VehicleType
from apps.users.serializers import UserListSerializer


class VehicleTypeSerializer(serializers.ModelSerializer):
    """Serializer for VehicleType model."""

    vehicles_count = serializers.SerializerMethodField()

    class Meta:
        model = VehicleType
        fields = [
            'id', 'name', 'description',
            'maintenance_interval_days', 'maintenance_interval_km',
            'vehicles_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'vehicles_count', 'created_at', 'updated_at']

    def get_vehicles_count(self, obj):
        return obj.vehicles.filter(is_deleted=False).count()


class VehicleListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing vehicles."""

    vehicle_type_name = serializers.CharField(
        source='vehicle_type.name',
        read_only=True,
        allow_null=True
    )
    display_name = serializers.CharField(read_only=True)
    maintenance_count = serializers.SerializerMethodField()
    last_maintenance = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'id', 'license_plate', 'vin', 'make', 'model', 'year',
            'display_name', 'vehicle_type', 'vehicle_type_name',
            'status', 'current_mileage', 'maintenance_count',
            'last_maintenance', 'created_at'
        ]

    def get_maintenance_count(self, obj):
        return obj.maintenance_tasks.count()

    def get_last_maintenance(self, obj):
        return obj.get_last_maintenance_date()


class VehicleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single vehicle."""

    vehicle_type = VehicleTypeSerializer(read_only=True)
    vehicle_type_id = serializers.PrimaryKeyRelatedField(
        queryset=VehicleType.objects.all(),
        source='vehicle_type',
        write_only=True,
        required=False,
        allow_null=True
    )
    assigned_driver = UserListSerializer(read_only=True)
    assigned_driver_id = serializers.PrimaryKeyRelatedField(
        queryset='apps.users.User.objects.filter(role="driver")',
        source='assigned_driver',
        write_only=True,
        required=False,
        allow_null=True
    )
    created_by = UserListSerializer(read_only=True)
    display_name = serializers.CharField(read_only=True)
    maintenance_count = serializers.SerializerMethodField()
    last_maintenance = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'id', 'license_plate', 'vin', 'make', 'model', 'year',
            'color', 'display_name', 'vehicle_type', 'vehicle_type_id',
            'status', 'current_mileage', 'fuel_type', 'fuel_capacity',
            'assigned_driver', 'assigned_driver_id', 'notes',
            'maintenance_count', 'last_maintenance',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_maintenance_count(self, obj):
        return obj.maintenance_tasks.count()

    def get_last_maintenance(self, obj):
        return obj.get_last_maintenance_date()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fix the queryset for assigned_driver_id
        from apps.users.models import User
        self.fields['assigned_driver_id'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.filter(role='driver'),
            source='assigned_driver',
            write_only=True,
            required=False,
            allow_null=True
        )


class VehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vehicles."""

    class Meta:
        model = Vehicle
        fields = [
            'license_plate', 'vin', 'make', 'model', 'year',
            'color', 'vehicle_type', 'status', 'current_mileage',
            'fuel_type', 'fuel_capacity', 'assigned_driver', 'notes'
        ]

    def validate_vin(self, value):
        """Validate VIN format."""
        if len(value) != 17:
            raise serializers.ValidationError(
                'VIN must be exactly 17 characters.'
            )
        return value.upper()

    def validate_year(self, value):
        """Validate year is reasonable."""
        import datetime
        current_year = datetime.datetime.now().year
        if value < 1900 or value > current_year + 1:
            raise serializers.ValidationError(
                f'Year must be between 1900 and {current_year + 1}.'
            )
        return value

    def create(self, validated_data):
        """Create vehicle with current user as creator."""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class VehicleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating vehicles."""

    class Meta:
        model = Vehicle
        fields = [
            'make', 'model', 'year', 'color', 'vehicle_type',
            'status', 'current_mileage', 'fuel_type', 'fuel_capacity',
            'assigned_driver', 'notes'
        ]

    def validate_year(self, value):
        """Validate year is reasonable."""
        import datetime
        current_year = datetime.datetime.now().year
        if value < 1900 or value > current_year + 1:
            raise serializers.ValidationError(
                f'Year must be between 1900 and {current_year + 1}.'
            )
        return value
