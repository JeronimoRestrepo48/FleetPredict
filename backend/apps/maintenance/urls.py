"""
URL patterns for Maintenance app.
"""

from django.urls import path

from .views import (
    MaintenanceTaskListCreateView,
    MaintenanceTaskDetailView,
    MaintenanceTaskCompleteView,
    MaintenanceTaskStatusView,
    MaintenanceDocumentUploadView,
    MaintenanceDocumentDeleteView,
    MaintenanceCommentListCreateView,
)

urlpatterns = [
    # Maintenance Tasks (FR4)
    path('', MaintenanceTaskListCreateView.as_view(), name='maintenance-list'),
    path('<int:pk>/', MaintenanceTaskDetailView.as_view(), name='maintenance-detail'),
    path('<int:pk>/complete/', MaintenanceTaskCompleteView.as_view(), name='maintenance-complete'),
    path('<int:pk>/status/', MaintenanceTaskStatusView.as_view(), name='maintenance-status'),
    
    # Documents (FR5)
    path('<int:task_id>/documents/', MaintenanceDocumentUploadView.as_view(), name='maintenance-document-upload'),
    path('documents/<int:pk>/', MaintenanceDocumentDeleteView.as_view(), name='maintenance-document-delete'),
    
    # Comments
    path('<int:task_id>/comments/', MaintenanceCommentListCreateView.as_view(), name='maintenance-comments'),
]
