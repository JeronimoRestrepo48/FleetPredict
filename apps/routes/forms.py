from django import forms
from apps.vehicles.models import Vehicle
from apps.vehicles.visibility import visible_vehicle_queryset
from .models import Route


class RoutePlannerForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ('vehicle', 'origin', 'destination', 'optimization_priority')
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'optimization_priority': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = visible_vehicle_queryset(user) if user else Vehicle.objects.filter(is_deleted=False)
        self.fields['vehicle'].queryset = qs
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
