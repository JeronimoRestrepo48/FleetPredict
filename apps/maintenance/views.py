"""
Views for Maintenance app.
Implements FR4 (Maintenance management system) and FR5 (Maintenance history per vehicle).
Uses Django MVT - template rendering.
"""

import csv
import io

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponse
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

from apps.dashboard.audit import log_audit
from .models import MaintenanceTask, MaintenanceDocument, MaintenanceTemplate, WorkOrder
from .forms import (
    MaintenanceTaskForm,
    MaintenanceTaskCompleteForm,
    MaintenanceTemplateForm,
    WorkOrderForm,
)


class CanManageMaintenanceMixin(UserPassesTestMixin):
    """Mixin that requires user to be admin, fleet manager, or mechanic."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_maintenance()


# ============== Maintenance Task Views (FR4) ==============

class MaintenanceBulkCsvView(LoginRequiredMixin, CanManageMaintenanceMixin, View):
    """FR16: Bulk export maintenance tasks as CSV."""

    def get(self, request):
        qs = MaintenanceTask.objects.select_related('vehicle', 'assignee').order_by('-scheduled_date')
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            'Vehicle', 'Title', 'Type', 'Status', 'Priority', 'Scheduled date',
            'Completion date', 'Estimated cost', 'Actual cost', 'Assignee',
        ])
        for t in qs:
            writer.writerow([
                str(t.vehicle),
                t.title,
                t.get_maintenance_type_display(),
                t.get_status_display(),
                t.get_priority_display(),
                t.scheduled_date.isoformat() if t.scheduled_date else '',
                t.completion_date.isoformat() if t.completion_date else '',
                str(t.estimated_cost) if t.estimated_cost is not None else '',
                str(t.actual_cost) if t.actual_cost is not None else '',
                t.assignee.get_full_name() if t.assignee else '',
            ])
        response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="maintenance_export.csv"'
        return response


class MaintenanceTaskListView(LoginRequiredMixin, ListView):
    """List maintenance tasks with filters."""

    model = MaintenanceTask
    template_name = 'maintenance/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_paginate_by(self, queryset):
        per = self.request.GET.get('per_page', '20')
        if per in ('10', '20', '50'):
            return int(per)
        return 20

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
        context['work_order'] = getattr(self.object, 'work_order', None)
        return context


class MaintenanceTaskCreateView(LoginRequiredMixin, CanManageMaintenanceMixin, CreateView):
    """Create maintenance task. Supports ?template=<pk> to prefill from MaintenanceTemplate (FR23)."""

    model = MaintenanceTask
    form_class = MaintenanceTaskForm
    template_name = 'maintenance/task_form.html'
    success_url = reverse_lazy('maintenance:task_list')

    def get_initial(self):
        initial = super().get_initial()
        template_id = self.request.GET.get('template')
        if template_id:
            tpl = MaintenanceTemplate.objects.filter(pk=template_id).first()
            if tpl:
                initial['title'] = tpl.name
                initial['description'] = tpl.description or ''
                initial['maintenance_type'] = tpl.maintenance_type
                initial['estimated_duration'] = tpl.estimated_duration
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['maintenance_templates'] = MaintenanceTemplate.objects.all().order_by('name')
        context['selected_template_id'] = self.request.GET.get('template')
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        log_audit(self.request, 'create', 'MaintenanceTask', self.object.pk, f'Task {self.object.title} created')
        messages.success(self.request, 'Maintenance task created successfully.')
        return response


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

    def get(self, request, pk):
        """Redirect GET to task detail (upload is via POST form)."""
        return redirect('maintenance:task_detail', pk=pk)

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


# ============== Maintenance Templates (FR23) ==============

class MaintenanceTemplateListView(LoginRequiredMixin, CanManageMaintenanceMixin, ListView):
    """List maintenance templates."""

    model = MaintenanceTemplate
    template_name = 'maintenance/maintenancetemplate_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        return MaintenanceTemplate.objects.all().order_by('name')


class MaintenanceTemplateCreateView(LoginRequiredMixin, CanManageMaintenanceMixin, CreateView):
    """Create maintenance template."""

    model = MaintenanceTemplate
    form_class = MaintenanceTemplateForm
    template_name = 'maintenance/maintenancetemplate_form.html'
    success_url = reverse_lazy('maintenance:template_list')

    def form_valid(self, form):
        messages.success(self.request, 'Maintenance template created successfully.')
        return super().form_valid(form)


class MaintenanceTemplateUpdateView(LoginRequiredMixin, CanManageMaintenanceMixin, UpdateView):
    """Update maintenance template."""

    model = MaintenanceTemplate
    form_class = MaintenanceTemplateForm
    template_name = 'maintenance/maintenancetemplate_form.html'
    context_object_name = 'template'
    success_url = reverse_lazy('maintenance:template_list')

    def form_valid(self, form):
        messages.success(self.request, 'Template updated successfully.')
        return super().form_valid(form)


class MaintenanceTemplateDeleteView(LoginRequiredMixin, CanManageMaintenanceMixin, DeleteView):
    """Delete maintenance template."""

    model = MaintenanceTemplate
    template_name = 'maintenance/maintenancetemplate_confirm_delete.html'
    context_object_name = 'template'
    success_url = reverse_lazy('maintenance:template_list')

    def form_valid(self, form):
        messages.success(self.request, 'Template deleted.')
        return super().form_valid(form)


# ============== Work Orders (FR24) ==============

class WorkOrderListView(LoginRequiredMixin, CanManageMaintenanceMixin, ListView):
    """List work orders with filters (status, assignee, date range)."""

    model = WorkOrder
    template_name = 'maintenance/workorder_list.html'
    context_object_name = 'work_orders'
    paginate_by = 20

    def get_queryset(self):
        qs = WorkOrder.objects.select_related('task', 'task__vehicle', 'assignee')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        assignee_id = self.request.GET.get('assignee')
        if assignee_id:
            qs = qs.filter(assignee_id=assignee_id)
        date_from = self.request.GET.get('date_from')
        if date_from:
            qs = qs.filter(due_date__gte=date_from)
        date_to = self.request.GET.get('date_to')
        if date_to:
            qs = qs.filter(due_date__lte=date_to)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = WorkOrder.Status.choices
        return context


class WorkOrderDetailView(LoginRequiredMixin, CanManageMaintenanceMixin, DetailView):
    """Work order detail."""

    model = WorkOrder
    template_name = 'maintenance/workorder_detail.html'
    context_object_name = 'work_order'


class WorkOrderCreateView(LoginRequiredMixin, CanManageMaintenanceMixin, CreateView):
    """Create work order manually (link to task). Supports ?task=<pk> to preselect task."""

    model = WorkOrder
    form_class = WorkOrderForm
    template_name = 'maintenance/workorder_form.html'
    success_url = reverse_lazy('maintenance:workorder_list')

    def get_initial(self):
        initial = super().get_initial()
        task_id = self.request.GET.get('task')
        if task_id:
            initial['task'] = task_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Work order created successfully.')
        return super().form_valid(form)


class WorkOrderUpdateView(LoginRequiredMixin, CanManageMaintenanceMixin, UpdateView):
    """Update work order (status, assignee, notes). Completed work orders are read-only."""

    model = WorkOrder
    form_class = WorkOrderForm
    template_name = 'maintenance/workorder_form.html'
    context_object_name = 'work_order'

    def get_success_url(self):
        return reverse_lazy('maintenance:workorder_detail', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        return WorkOrder.objects.select_related('task', 'assignee')

    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(WorkOrder, pk=kwargs.get('pk'))
        if obj.status == WorkOrder.Status.COMPLETED:
            messages.error(request, 'Completed work orders cannot be modified.')
            return redirect('maintenance:workorder_detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if form.cleaned_data.get('status') == WorkOrder.Status.COMPLETED:
            form.instance.completion_date = timezone.now().date()
        messages.success(self.request, 'Work order updated.')
        return super().form_valid(form)
