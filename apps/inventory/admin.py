from django.contrib import admin
from .models import SparePart, StockMovement, Supplier, SupplierPart

admin.site.register(SparePart)
admin.site.register(StockMovement)
admin.site.register(Supplier)
admin.site.register(SupplierPart)
