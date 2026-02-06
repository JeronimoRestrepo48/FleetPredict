"""
Views for Maintenance app.
Implements FR4 (Maintenance management system) and FR5 (Maintenance history per vehicle).
Uses Django MVT - template rendering.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
)
from django.db.models import Q
from django.utils import timezone

from .models import MaintenanceTask, MaintenanceDocument
from .forms import MaintenanceTaskForm, MaintenanceTaskCompleteForm


class CanManageMaintenanceMixin(UserPassesTestMixin):
    """Mixin that requires user to be admin, fleet manager, or mechanic."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_maintenance()


# ============== Maintenance Task Views (FR4) ==============

class MaintenanceTaskListView(LoginRequiredMixin, ListView):
    """List maintenance tasks with filters."""

    model = MaintenanceTask
    template_name = 'maintenance/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        queryset = MaintenanceTask.objects.select_related('vehicle', 'assignee')

        if user.is_driver:
            queryset = queryset.filter(vehicle__assigned_driver=user)
        elif user.is_mechanic:
            queryset = queryset.filter(Q(assignee=user) | Q(assignee__isnull=True))

        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        vehicle_id = self.request.GET.get('vehicle')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)

        # Check overdue
        for task in queryset.filter(status=MaintenanceTask.Status.SCHEDULED):
            task.check_overdue()

        return queryset.order_by('-scheduled_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_manage'] = self.request.user.can_manage_maintenance()
        context['status_choices'] = MaintenanceTask.Status.choices
        return context


class MaintenanceTaskDetailView(LoginRequiredMixin, DetailView):
    """Maintenance task detail."""

    model = MaintenanceTask
    template_name = 'maintenance/task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        user = self.request.user
        queryset = MaintenanceTask.objects.select_related('vehicle', 'assignee')
        if user.is_driver:
            queryset = queryset.filter(vehicle__assigned_driver=user)
        elif user.is_mechanic:
            queryset = queryset.filter(Q(assignee=user) | Q(assignee__isnull=True))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_manage'] = self.request.user.can_manage_maintenance()
        context['documents'] = self.object.documents.all()
        return context


class MaintenanceTaskCreateView(LoginRequiredMixin, CanManageMaintenanceMixin, CreateView):
    """Create maintenance task."""

    model = MaintenanceTask
    form_class = MaintenanceTaskForm
    template_name = 'maintenance/task_form.html'
    success_url = reverse_lazy('maintenance:task_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Maintenance task created successfully.')
        return super().form_valid(form)


class MaintenanceTaskUpdateView(LoginRequiredMixin, CanManageMaintenanceMixin, UpdateView):
    """Update maintenance task."""

    model = MaintenanceTask
    form_class = MaintenanceTaskForm
    template_name = 'maintenance/task_form.html'
    context_object_name = 'task'

    def get_success_url(self):
        return reverse_lazy('maintenance:task_detail', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        return MaintenanceTask.objects.all()

    def form_valid(self, form):
        instance = form.instance
        if instance.status in [MaintenanceTask.Status.COMPLETED, MaintenanceTask.Status.CANCELLED]:
            messages.error(self.request, 'Cannot modify completed or cancelled tasks.')
            return redirect('maintenance:task_detail', pk=instance.pk)
        messages.success(self.request, 'Maintenance task updated successfully.')
        return super().form_valid(form)


class MaintenanceTaskDeleteView(LoginRequiredMixin, CanManageMaintenanceMixin, DeleteView):
    """Delete maintenance task."""

    model = MaintenanceTask
    template_name = 'maintenance/task_confirm_delete.html'
    context_object_name = 'task'
    success_url = reverse_lazy('maintenance:task_list')

    def get_queryset(self):
        return MaintenanceTask.objects.all()

    def form_valid(self, form):
        if self.object.status == MaintenanceTask.Status.COMPLETED:
            messages.error(self.request, 'Cannot delete completed tasks.')
            return redirect('maintenance:task_detail', pk=self.object.pk)
        messages.success(self.request, 'Maintenance task deleted successfully.')
        return super().form_valid(form)


class MaintenanceTaskCompleteView(LoginRequiredMixin, CanManageMaintenanceMixin, View):
    """Mark maintenance task as completed (FR4)."""

    def get(self, request, pk):
        task = get_object_or_404(MaintenanceTask, pk=pk)
        if task.status == MaintenanceTask.Status.COMPLETED:
            messages.warning(request, 'Task is already completed.')
            return redirect('maintenance:task_detail', pk=pk)
        form = MaintenanceTaskCompleteForm()
        return render(request, 'maintenance/task_complete.html', {'task': task, 'form': form})

    def post(self, request, pk):
        task = get_object_or_404(MaintenanceTask, pk=pk)
        if task.status == MaintenanceTask.Status.COMPLETED:
            messages.warning(request, 'Task is already completed.')
            return redirect('maintenance:task_detail', pk=pk)
        form = MaintenanceTaskCompleteForm(request.POST)
        if form.is_valid():
            task.mark_completed(
                completion_notes=form.cleaned_data.get('completion_notes', ''),
                actual_cost=form.cleaned_data.get('actual_cost'),
                mileage=form.cleaned_data.get('mileage_at_maintenance')
            )
            messages.success(request, 'Maintenance task completed successfully.')
            return redirect('maintenance:task_detail', pk=pk)
        return render(request, 'maintenance/task_complete.html', {'task': task, 'form': form})


class MaintenanceDocumentUploadView(LoginRequiredMixin, CanManageMaintenanceMixin, View):
    """Upload document to maintenance task (FR5)."""

    def post(self, request, pk):
        task = get_object_or_404(MaintenanceTask, pk=pk)
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'No file provided.')
            return redirect('maintenance:task_detail', pk=pk)
        if file.size > 10 * 1024 * 1024:
            messages.error(request, 'File size exceeds 10MB limit.')
            return redirect('maintenance:task_detail', pk=pk)
        MaintenanceDocument.objects.create(
            task=task,
            file=file,
            description=request.POST.get('description', ''),
            uploaded_by=request.user
        )
        messages.success(request, 'Document uploaded successfully.')
        return redirect('maintenance:task_detail', pk=pk)
