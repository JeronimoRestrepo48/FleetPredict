"""
Views for Vehicles app.
Implements FR2: Vehicle registry.
"""

from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Vehicle, VehicleType
from .serializers import (
    VehicleTypeSerializer,
    VehicleListSerializer,
    VehicleDetailSerializer,
    VehicleCreateSerializer,
    VehicleUpdateSerializer,
)
from apps.users.permissions import CanManageVehicles, IsFleetManagerOrAdmin


# ============== Vehicle Type Views ==============

class VehicleTypeListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating vehicle types.
    """
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAuthenticated, IsFleetManagerOrAdmin]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsFleetManagerOrAdmin()]


class VehicleTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting vehicle types.
    """
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAuthenticated, IsFleetManagerOrAdmin]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsFleetManagerOrAdmin()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if there are vehicles using this type
        if instance.vehicles.filter(is_deleted=False).exists():
            return Response(
                {'error': 'Cannot delete vehicle type with associated vehicles.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============== Vehicle Views (FR2) ==============

class VehicleListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating vehicles.
    FR2: Register and manage fleet vehicles with CRUD operations and list view.
    """
    permission_classes = [IsAuthenticated, CanManageVehicles]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['license_plate', 'vin', 'make', 'model']
    ordering_fields = ['created_at', 'make', 'model', 'year', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Get vehicles based on user role.
        Admins and Fleet Managers see all vehicles.
        Mechanics see all vehicles.
        Drivers see only their assigned vehicles.
        """
        user = self.request.user
        queryset = Vehicle.objects.filter(is_deleted=False)

        # Drivers can only see their assigned vehicles
        if user.is_driver:
            queryset = queryset.filter(assigned_driver=user)

        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        vehicle_type = self.request.query_params.get('vehicle_type')
        if vehicle_type:
            queryset = queryset.filter(vehicle_type_id=vehicle_type)

        make = self.request.query_params.get('make')
        if make:
            queryset = queryset.filter(make__icontains=make)

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VehicleCreateSerializer
        return VehicleListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = serializer.save()

        return Response({
            'message': 'Vehicle created successfully.',
            'vehicle': VehicleDetailSerializer(vehicle).data
        }, status=status.HTTP_201_CREATED)


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting vehicles.
    FR2: Vehicle CRUD operations.
    """
    permission_classes = [IsAuthenticated, CanManageVehicles]

    def get_queryset(self):
        """
        Get vehicles based on user role.
        """
        user = self.request.user
        queryset = Vehicle.objects.filter(is_deleted=False)

        # Drivers can only see their assigned vehicles
        if user.is_driver:
            queryset = queryset.filter(assigned_driver=user)

        return queryset

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return VehicleUpdateSerializer
        return VehicleDetailSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            'message': 'Vehicle updated successfully.',
            'vehicle': VehicleDetailSerializer(instance).data
        })

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete vehicle.
        FR2: Delete vehicle (soft delete: mark as inactive, preserve history).
        """
        instance = self.get_object()
        instance.soft_delete()

        return Response({
            'message': 'Vehicle deleted successfully.'
        }, status=status.HTTP_200_OK)


class VehicleHistoryView(generics.ListAPIView):
    """
    API endpoint for getting vehicle maintenance history.
    FR5: View complete maintenance history for each vehicle.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get maintenance history for a vehicle."""
        try:
            vehicle = Vehicle.objects.get(pk=pk, is_deleted=False)
        except Vehicle.DoesNotExist:
            return Response(
                {'error': 'Vehicle not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions for drivers
        if request.user.is_driver and vehicle.assigned_driver != request.user:
            return Response(
                {'error': 'You do not have permission to view this vehicle.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Import here to avoid circular imports
        from apps.maintenance.serializers import MaintenanceTaskListSerializer
        
        history = vehicle.maintenance_tasks.filter(
            status='completed'
        ).order_by('-completion_date')

        serializer = MaintenanceTaskListSerializer(history, many=True)

        return Response({
            'vehicle': VehicleListSerializer(vehicle).data,
            'history': serializer.data,
            'total_count': history.count()
        })
