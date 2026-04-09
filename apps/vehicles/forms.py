"""
Forms for Vehicles app.
"""

from django import forms
from django.contrib.auth import get_user_model

from .models import Vehicle, VehicleType, ComplianceRequirement, SensorReading

User = get_user_model()


class VehicleTypeForm(forms.ModelForm):
    """Form for VehicleType create/edit."""

    class Meta:
        model = VehicleType
        fields = ('name', 'description', 'maintenance_interval_days', 'maintenance_interval_km')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class VehicleForm(forms.ModelForm):
    """Form for Vehicle create/edit."""

    class Meta:
        model = Vehicle
        fields = (
            'license_plate', 'vin', 'make', 'model', 'year', 'color',
            'vehicle_type', 'status', 'current_mileage', 'fuel_type',
            'fuel_capacity', 'assigned_driver', 'notes'
        )
        widgets = {
            'assigned_driver': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_driver'].queryset = User.objects.filter(role='driver')
        for name, field in self.fields.items():
            if name != 'assigned_driver' and hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})
            elif name == 'assigned_driver':
                field.widget.attrs.update({'class': 'form-select'})


class ComplianceRequirementForm(forms.ModelForm):
    """Form for ComplianceRequirement create/edit."""

    class Meta:
        model = ComplianceRequirement
        fields = (
            'vehicle', 'requirement_type', 'name', 'expiration_date',
            'issuing_authority', 'document_reference', 'notes',
        )
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.setdefault('class', 'form-control')
            if name == 'vehicle':
                field.widget.attrs.setdefault('class', 'form-select')


class SensorReadingForm(forms.ModelForm):
    """FR18: Manual sensor reading entry."""

    class Meta:
        model = SensorReading
        fields = ('vehicle', 'sensor_type', 'value', 'timestamp')
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'sensor_type': forms.Select(attrs={'class': 'form-select'}),
            'timestamp': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class SensorCSVUploadForm(forms.Form):
    """FR18: Upload sensor readings via CSV file."""
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(is_deleted=False),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'}),
        help_text='CSV columns: sensor_type, value, timestamp (ISO format)',
    )
