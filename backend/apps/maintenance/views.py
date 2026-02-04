"""
Views for Maintenance app.
Implements FR4 (Maintenance management system) and FR5 (Maintenance history per vehicle).
"""

from rest_framework import generics, status, filters, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from django.utils import timezone

from .models import MaintenanceTask, MaintenanceDocument, MaintenanceComment
from .serializers import (
    MaintenanceTaskListSerializer,
    MaintenanceTaskDetailSerializer,
    MaintenanceTaskCreateSerializer,
    MaintenanceTaskUpdateSerializer,
    MaintenanceTaskCompleteSerializer,
    MaintenanceTaskStatusSerializer,
    MaintenanceDocumentSerializer,
    MaintenanceCommentSerializer,
)
from apps.users.permissions import CanManageMaintenance


# ============== Maintenance Task Views (FR4) ==============

class MaintenanceTaskListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating maintenance tasks.
    FR4: Plan, record, and track maintenance tasks.
    """
    permission_classes = [IsAuthenticated, CanManageMaintenance]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'vehicle__license_plate', 'vehicle__make']
    ordering_fields = ['scheduled_date', 'created_at', 'priority', 'status']
    ordering = ['-scheduled_date']

    def get_queryset(self):
        """Get tasks based on user role and filters."""
        user = self.request.user
        queryset = MaintenanceTask.objects.all()

        # Drivers can only see tasks for their assigned vehicles
        if user.is_driver:
            queryset = queryset.filter(vehicle__assigned_driver=user)
        # Mechanics see tasks assigned to them or unassigned
        elif user.is_mechanic:
            queryset = queryset.filter(
                Q(assignee=user) | Q(assignee__isnull=True)
            )

        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        vehicle_id = self.request.query_params.get('vehicle')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)

        maintenance_type = self.request.query_params.get('type')
        if maintenance_type:
            queryset = queryset.filter(maintenance_type=maintenance_type)

        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        assignee = self.request.query_params.get('assignee')
        if assignee:
            queryset = queryset.filter(assignee_id=assignee)

        # Date range filters
        from_date = self.request.query_params.get('from_date')
        if from_date:
            queryset = queryset.filter(scheduled_date__gte=from_date)

        to_date = self.request.query_params.get('to_date')
        if to_date:
            queryset = queryset.filter(scheduled_date__lte=to_date)

        # Check for overdue tasks
        for task in queryset.filter(status=MaintenanceTask.Status.SCHEDULED):
            task.check_overdue()

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MaintenanceTaskCreateSerializer
        return MaintenanceTaskListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        return Response({
            'message': 'Maintenance task created successfully.',
            'task': MaintenanceTaskDetailSerializer(task).data
        }, status=status.HTTP_201_CREATED)


class MaintenanceTaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting maintenance tasks.
    FR4: Maintenance task CRUD operations.
    """
    permission_classes = [IsAuthenticated, CanManageMaintenance]

    def get_queryset(self):
        """Get tasks based on user role."""
        user = self.request.user
        queryset = MaintenanceTask.objects.all()

        if user.is_driver:
            queryset = queryset.filter(vehicle__assigned_driver=user)
        elif user.is_mechanic:
            queryset = queryset.filter(
                Q(assignee=user) | Q(assignee__isnull=True)
            )

        return queryset

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MaintenanceTaskUpdateSerializer
        return MaintenanceTaskDetailSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Don't allow updates to completed or cancelled tasks
        if instance.status in [MaintenanceTask.Status.COMPLETED, MaintenanceTask.Status.CANCELLED]:
            return Response(
                {'error': 'Cannot modify completed or cancelled tasks.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            'message': 'Maintenance task updated successfully.',
            'task': MaintenanceTaskDetailSerializer(instance).data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Don't allow deletion of completed tasks
        if instance.status == MaintenanceTask.Status.COMPLETED:
            return Response(
                {'error': 'Cannot delete completed tasks.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_destroy(instance)
        return Response({
            'message': 'Maintenance task deleted successfully.'
        }, status=status.HTTP_200_OK)


class MaintenanceTaskCompleteView(views.APIView):
    """
    API endpoint for completing a maintenance task.
    FR4: Mark maintenance as completed.
    """
    permission_classes = [IsAuthenticated, CanManageMaintenance]

    def post(self, request, pk):
        try:
            task = MaintenanceTask.objects.get(pk=pk)
        except MaintenanceTask.DoesNotExist:
            return Response(
                {'error': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if task is already completed
        if task.status == MaintenanceTask.Status.COMPLETED:
            return Response(
                {'error': 'Task is already completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MaintenanceTaskCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task.mark_completed(
            completion_notes=serializer.validated_data.get('completion_notes', ''),
            actual_cost=serializer.validated_data.get('actual_cost'),
            mileage=serializer.validated_data.get('mileage_at_maintenance')
        )

        return Response({
            'message': 'Maintenance task completed successfully.',
            'task': MaintenanceTaskDetailSerializer(task).data
        })


class MaintenanceTaskStatusView(views.APIView):
    """
    API endpoint for changing task status.
    FR4: Track maintenance status.
    """
    permission_classes = [IsAuthenticated, CanManageMaintenance]

    def post(self, request, pk):
        try:
            task = MaintenanceTask.objects.get(pk=pk)
        except MaintenanceTask.DoesNotExist:
            return Response(
                {'error': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MaintenanceTaskStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')

        if new_status == MaintenanceTask.Status.COMPLETED:
            task.mark_completed(completion_notes=notes)
        elif new_status == MaintenanceTask.Status.CANCELLED:
            task.mark_cancelled(reason=notes)
        elif new_status == MaintenanceTask.Status.IN_PROGRESS:
            task.mark_in_progress()
        else:
            task.status = new_status
            task.save()

        return Response({
            'message': f'Task status changed to {new_status}.',
            'task': MaintenanceTaskDetailSerializer(task).data
        })


# ============== Document Views (FR5) ==============

class MaintenanceDocumentUploadView(views.APIView):
    """
    API endpoint for uploading documents to a maintenance task.
    FR5: Upload and attach documents/files to maintenance records.
    """
    permission_classes = [IsAuthenticated, CanManageMaintenance]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, task_id):
        try:
            task = MaintenanceTask.objects.get(pk=task_id)
        except MaintenanceTask.DoesNotExist:
            return Response(
                {'error': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No file provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'File size exceeds 10MB limit.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        document = MaintenanceDocument.objects.create(
            task=task,
            file=file,
            description=request.data.get('description', ''),
            uploaded_by=request.user
        )

        return Response({
            'message': 'Document uploaded successfully.',
            'document': MaintenanceDocumentSerializer(document).data
        }, status=status.HTTP_201_CREATED)


class MaintenanceDocumentDeleteView(views.APIView):
    """
    API endpoint for deleting a document.
    """
    permission_classes = [IsAuthenticated, CanManageMaintenance]

    def delete(self, request, pk):
        try:
            document = MaintenanceDocument.objects.get(pk=pk)
        except MaintenanceDocument.DoesNotExist:
            return Response(
                {'error': 'Document not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        document.file.delete()
        document.delete()

        return Response({
            'message': 'Document deleted successfully.'
        }, status=status.HTTP_200_OK)


# ============== Comment Views ==============

class MaintenanceCommentListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating comments on a task.
    """
    serializer_class = MaintenanceCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        task_id = self.kwargs.get('task_id')
        return MaintenanceComment.objects.filter(task_id=task_id)

    def create(self, request, *args, **kwargs):
        task_id = self.kwargs.get('task_id')
        try:
            task = MaintenanceTask.objects.get(pk=task_id)
        except MaintenanceTask.DoesNotExist:
            return Response(
                {'error': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        comment = MaintenanceComment.objects.create(
            task=task,
            user=request.user,
            content=request.data.get('content', '')
        )

        return Response({
            'message': 'Comment added successfully.',
            'comment': MaintenanceCommentSerializer(comment).data
        }, status=status.HTTP_201_CREATED)
