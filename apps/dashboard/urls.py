"""
URL patterns for Dashboard app.
"""

from django.urls import path

from .views import (
    DashboardView,
    ExecuteRunbookView,
    PredictionsView,
    SuggestedMaintenanceView,
    AcceptSuggestionView,
    DismissSuggestionView,
    AlertsView,
    AlertRuleListView,
    AlertRuleCreateView,
    AlertRuleUpdateView,
    AlertThresholdListView,
    AlertThresholdCreateView,
    AlertThresholdUpdateView,
    AlertThresholdDeleteView,
    AuditLogListView,
)

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('soc/runbook/', ExecuteRunbookView.as_view(), name='execute_runbook'),
    path('predictions/', PredictionsView.as_view(), name='predictions'),
    path('suggested-maintenance/', SuggestedMaintenanceView.as_view(), name='suggested_maintenance'),
    path('suggested-maintenance/accept/', AcceptSuggestionView.as_view(), name='accept_suggestion'),
    path('suggested-maintenance/dismiss/', DismissSuggestionView.as_view(), name='dismiss_suggestion'),
    path('alerts/', AlertsView.as_view(), name='alerts'),
    path('alert-rules/', AlertRuleListView.as_view(), name='alertrule_list'),
    path('alert-rules/create/', AlertRuleCreateView.as_view(), name='alertrule_create'),
    path('alert-rules/<int:pk>/edit/', AlertRuleUpdateView.as_view(), name='alertrule_edit'),
    path('alert-thresholds/', AlertThresholdListView.as_view(), name='alertthreshold_list'),
    path('alert-thresholds/create/', AlertThresholdCreateView.as_view(), name='alertthreshold_create'),
    path('alert-thresholds/<int:pk>/edit/', AlertThresholdUpdateView.as_view(), name='alertthreshold_edit'),
    path('alert-thresholds/<int:pk>/delete/', AlertThresholdDeleteView.as_view(), name='alertthreshold_delete'),
    path('audit-log/', AuditLogListView.as_view(), name='auditlog_list'),
]
