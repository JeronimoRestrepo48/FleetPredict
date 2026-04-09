"""FR20: Spare Parts & Inventory + FR26: Supplier Management views."""
import csv
import io

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.template.response import TemplateResponse

from .models import SparePart, StockMovement, PartUsage, Supplier, SupplierPart
from .forms import SparePartForm, StockMovementForm, SupplierForm, SupplierPartForm


class CanManageInventoryMixin(UserPassesTestMixin):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (u.can_manage_vehicles() or u.can_manage_maintenance())


class SparePartListView(LoginRequiredMixin, ListView):
    model = SparePart
    template_name = 'inventory/sparepart_list.html'
    context_object_name = 'parts'
    paginate_by = 25

    def get_queryset(self):
        qs = SparePart.objects.all()
        cat = self.request.GET.get('category')
        if cat:
            qs = qs.filter(category=cat)
        search = self.request.GET.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=search) | Q(part_number__icontains=search))
        low = self.request.GET.get('low_stock')
        if low == '1':
            ids = [p.pk for p in qs if p.is_low_stock]
            qs = qs.filter(pk__in=ids)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = SparePart.Category.choices
        ctx['can_manage'] = self.request.user.can_manage_vehicles()
        return ctx


class SparePartDetailView(LoginRequiredMixin, DetailView):
    model = SparePart
    template_name = 'inventory/sparepart_detail.html'
    context_object_name = 'part'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['movements'] = self.object.movements.select_related('created_by')[:20]
        ctx['supplier_links'] = self.object.supplier_links.select_related('supplier')
        return ctx


class SparePartCreateView(LoginRequiredMixin, CanManageInventoryMixin, CreateView):
    model = SparePart
    form_class = SparePartForm
    template_name = 'inventory/sparepart_form.html'
    success_url = reverse_lazy('inventory:sparepart_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Spare part created.')
        return super().form_valid(form)


class SparePartUpdateView(LoginRequiredMixin, CanManageInventoryMixin, UpdateView):
    model = SparePart
    form_class = SparePartForm
    template_name = 'inventory/sparepart_form.html'
    context_object_name = 'part'
    success_url = reverse_lazy('inventory:sparepart_list')

    def form_valid(self, form):
        messages.success(self.request, 'Spare part updated.')
        return super().form_valid(form)


class SparePartDeleteView(LoginRequiredMixin, CanManageInventoryMixin, DeleteView):
    model = SparePart
    template_name = 'inventory/sparepart_confirm_delete.html'
    context_object_name = 'part'
    success_url = reverse_lazy('inventory:sparepart_list')


class StockAdjustView(LoginRequiredMixin, CanManageInventoryMixin, CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/stock_adjust.html'

    def form_valid(self, form):
        mov = form.save(commit=False)
        mov.created_by = self.request.user
        mov.save()
        part = mov.spare_part
        if mov.movement_type == 'in':
            part.current_stock += mov.quantity
        elif mov.movement_type == 'out':
            part.current_stock = max(0, part.current_stock - mov.quantity)
        else:
            part.current_stock = max(0, part.current_stock + mov.quantity)
        part.save(update_fields=['current_stock'])
        messages.success(self.request, f'Stock updated: {part.name} -> {part.current_stock}')
        return redirect('inventory:sparepart_detail', pk=part.pk)


class LowStockListView(LoginRequiredMixin, ListView):
    model = SparePart
    template_name = 'inventory/low_stock.html'
    context_object_name = 'parts'

    def get_queryset(self):
        return [p for p in SparePart.objects.all() if p.is_low_stock]


class ReorderSuggestionsView(LoginRequiredMixin, ListView):
    model = SparePart
    template_name = 'inventory/reorder_suggestions.html'
    context_object_name = 'parts'

    def get_queryset(self):
        return [p for p in SparePart.objects.all() if p.is_low_stock]


class InventoryExportCsvView(LoginRequiredMixin, CanManageInventoryMixin, View):
    def get(self, request):
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(['Part Number', 'Name', 'Category', 'Unit Cost', 'Stock', 'Reorder Point', 'Low Stock'])
        for p in SparePart.objects.all():
            writer.writerow([p.part_number, p.name, p.category, p.unit_cost, p.current_stock, p.reorder_point, p.is_low_stock])
        resp = HttpResponse(buf.getvalue(), content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="inventory_export.csv"'
        return resp


class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'inventory/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 25


class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = 'inventory/supplier_detail.html'
    context_object_name = 'supplier'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['supplied_parts'] = self.object.supplied_parts.select_related('spare_part')
        return ctx


class SupplierCreateView(LoginRequiredMixin, CanManageInventoryMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    success_url = reverse_lazy('inventory:supplier_list')

    def form_valid(self, form):
        messages.success(self.request, 'Supplier created.')
        return super().form_valid(form)


class SupplierUpdateView(LoginRequiredMixin, CanManageInventoryMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    context_object_name = 'supplier'
    success_url = reverse_lazy('inventory:supplier_list')

    def form_valid(self, form):
        messages.success(self.request, 'Supplier updated.')
        return super().form_valid(form)


class SupplierDeleteView(LoginRequiredMixin, CanManageInventoryMixin, DeleteView):
    model = Supplier
    template_name = 'inventory/supplier_confirm_delete.html'
    context_object_name = 'supplier'
    success_url = reverse_lazy('inventory:supplier_list')


class SupplierComparisonView(LoginRequiredMixin, View):
    def get(self, request):
        part_id = request.GET.get('part')
        links = []
        parts = SparePart.objects.all()
        if part_id:
            links = SupplierPart.objects.filter(spare_part_id=part_id).select_related('supplier', 'spare_part').order_by('unit_price')
        return TemplateResponse(request, 'inventory/supplier_comparison.html', {
            'links': links, 'parts': parts, 'selected_part': part_id,
        })
