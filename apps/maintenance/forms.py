"""
Forms for Maintenance app.
"""

from django import forms
from django.contrib.auth import get_user_model

from .models import MaintenanceTask, MaintenanceTemplate, WorkOrder

User = get_user_model()


class MaintenanceTaskForm(forms.ModelForm):
    """Form for MaintenanceTask create/edit."""

    class Meta:
        model = MaintenanceTask
        fields = (
            'vehicle', 'title', 'description', 'maintenance_type',
            'scheduled_date', 'estimated_duration', 'status', 'priority',
            'assignee', 'estimated_cost'
        )
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})
            if name in ('vehicle', 'assignee'):
                field.widget.attrs.update({'class': 'form-select'})


class MaintenanceTaskCompleteForm(forms.Form):
    """Form for completing a maintenance task."""

    completion_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    actual_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    mileage_at_maintenance = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class MaintenanceTemplateForm(forms.ModelForm):
    """Form for MaintenanceTemplate create/edit (FR23)."""

    class Meta:
        model = MaintenanceTemplate
        fields = ('name', 'description', 'maintenance_type', 'estimated_duration', 'steps')
        widgets = {
            'steps': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'One step per line, e.g.: Check oil level\nInspect brakes',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.setdefault('class', 'form-control')
        if 'steps' in self.fields and not isinstance(self.fields['steps'].widget, forms.Textarea):
            pass
        # steps: accept JSON list or newline-separated lines
        self.fields['steps'].help_text = 'Enter one step per line, or a JSON list. Stored as checklist.'
        # Show list as newline-separated in textarea when editing
        if self.instance and self.instance.pk and getattr(self.instance, 'steps', None):
            steps = self.instance.steps
            if isinstance(steps, list):
                self.fields['steps'].initial = '\n'.join(str(s) for s in steps)

    def clean_steps(self):
        data = self.cleaned_data.get('steps')
        if not data:
            return []
        if isinstance(data, list):
            return data
        s = (data or '').strip()
        if not s:
            return []
        # Try JSON first
        import json
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except (TypeError, ValueError):
            pass
        # Newline-separated
        return [line.strip() for line in s.splitlines() if line.strip()]


class WorkOrderForm(forms.ModelForm):
    """Form for creating/editing WorkOrder (FR24)."""

    class Meta:
        model = WorkOrder
        fields = ('task', 'assignee', 'priority', 'due_date', 'status', 'notes')
        widgets = {
            'task': forms.Select(attrs={'class': 'form-select'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.setdefault('class', 'form-control')
            if name in ('task', 'assignee'):
                field.widget.attrs.setdefault('class', 'form-select')
        # For create: only tasks that don't have a work order yet
        if not self.instance or not self.instance.pk:
            self.fields['task'].queryset = MaintenanceTask.objects.filter(
                work_order__isnull=True
            ).select_related('vehicle').order_by('-scheduled_date')
        else:
            self.fields['task'].disabled = True
