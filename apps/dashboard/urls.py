"""
URL patterns for Dashboard app.
"""

from django.urls import path

from .views import DashboardView, ExecuteRunbookView, PredictionsView, AlertsView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('soc/runbook/', ExecuteRunbookView.as_view(), name='execute_runbook'),
    path('predictions/', PredictionsView.as_view(), name='predictions'),
    path('alerts/', AlertsView.as_view(), name='alerts'),
]
