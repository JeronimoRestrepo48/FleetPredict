from django.urls import path
from .views import (
    SparePartListView, SparePartDetailView, SparePartCreateView,
    SparePartUpdateView, SparePartDeleteView,
    StockAdjustView, LowStockListView, ReorderSuggestionsView,
    InventoryExportCsvView,
    SupplierListView, SupplierDetailView, SupplierCreateView,
    SupplierUpdateView, SupplierDeleteView, SupplierComparisonView, SupplierReviewCreateView,
)

app_name = 'inventory'

urlpatterns = [
    path('', SparePartListView.as_view(), name='sparepart_list'),
    path('create/', SparePartCreateView.as_view(), name='sparepart_create'),
    path('<int:pk>/', SparePartDetailView.as_view(), name='sparepart_detail'),
    path('<int:pk>/edit/', SparePartUpdateView.as_view(), name='sparepart_update'),
    path('<int:pk>/delete/', SparePartDeleteView.as_view(), name='sparepart_delete'),
    path('stock-adjust/', StockAdjustView.as_view(), name='stock_adjust'),
    path('low-stock/', LowStockListView.as_view(), name='low_stock'),
    path('reorder/', ReorderSuggestionsView.as_view(), name='reorder_suggestions'),
    path('export/csv/', InventoryExportCsvView.as_view(), name='inventory_export_csv'),
    path('suppliers/', SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/', SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', SupplierUpdateView.as_view(), name='supplier_update'),
    path('suppliers/<int:pk>/delete/', SupplierDeleteView.as_view(), name='supplier_delete'),
    path('suppliers/<int:pk>/review/', SupplierReviewCreateView.as_view(), name='supplier_review_create'),
    path('suppliers/compare/', SupplierComparisonView.as_view(), name='supplier_comparison'),
]
