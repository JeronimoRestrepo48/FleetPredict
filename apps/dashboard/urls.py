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
    AlertRuleUpdateView,
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
    path('alert-rules/<int:pk>/edit/', AlertRuleUpdateView.as_view(), name='alertrule_edit'),
    path('audit-log/', AuditLogListView.as_view(), name='auditlog_list'),
]
