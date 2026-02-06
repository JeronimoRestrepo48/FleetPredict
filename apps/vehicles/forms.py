"""
Forms for Vehicles app.
"""

from django import forms
from django.contrib.auth import get_user_model

from .models import Vehicle, VehicleType

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
