"""
Forms for Maintenance app.
"""

from django import forms
from django.contrib.auth import get_user_model

from .models import MaintenanceTask

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
