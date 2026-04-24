from django import forms
from .models import SparePart, StockMovement, Supplier, SupplierPart, SupplierReview


class SparePartForm(forms.ModelForm):
    class Meta:
        model = SparePart
        fields = ('name', 'part_number', 'category', 'description', 'unit_cost', 'reorder_point', 'current_stock')
        widgets = {'category': forms.Select(attrs={'class': 'form-select'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ('spare_part', 'movement_type', 'quantity', 'maintenance_task', 'notes')
        widgets = {
            'spare_part': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'maintenance_task': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ('name', 'contact_name', 'email', 'phone', 'address', 'delivery_terms')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class SupplierPartForm(forms.ModelForm):
    class Meta:
        model = SupplierPart
        fields = ('supplier', 'spare_part', 'unit_price', 'lead_time_days')
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'spare_part': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class SupplierReviewForm(forms.ModelForm):
    class Meta:
        model = SupplierReview
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.Select(
                choices=[(1, '1 star'), (2, '2 stars'), (3, '3 stars'), (4, '4 stars'), (5, '5 stars')],
                attrs={'class': 'form-select'},
            ),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Optional feedback'}),
        }
