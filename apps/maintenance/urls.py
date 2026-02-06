"""
URL patterns for Maintenance app.
"""

from django.urls import path

from .views import (
    MaintenanceTaskListView,
    MaintenanceTaskDetailView,
    MaintenanceTaskCreateView,
    MaintenanceTaskUpdateView,
    MaintenanceTaskDeleteView,
    MaintenanceTaskCompleteView,
    MaintenanceDocumentUploadView,
)

app_name = 'maintenance'

urlpatterns = [
    path('', MaintenanceTaskListView.as_view(), name='task_list'),
    path('create/', MaintenanceTaskCreateView.as_view(), name='task_create'),
    path('<int:pk>/', MaintenanceTaskDetailView.as_view(), name='task_detail'),
    path('<int:pk>/edit/', MaintenanceTaskUpdateView.as_view(), name='task_update'),
    path('<int:pk>/delete/', MaintenanceTaskDeleteView.as_view(), name='task_delete'),
    path('<int:pk>/complete/', MaintenanceTaskCompleteView.as_view(), name='task_complete'),
    path('<int:pk>/documents/', MaintenanceDocumentUploadView.as_view(), name='task_documents'),
]
