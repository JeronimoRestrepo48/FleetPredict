from django import forms
from apps.vehicles.models import Vehicle
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
        qs = Vehicle.objects.filter(is_deleted=False)
        if user and getattr(user, 'is_driver', False):
            qs = qs.filter(assigned_driver=user)
        self.fields['vehicle'].queryset = qs
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
