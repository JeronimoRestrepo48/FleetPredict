"""
URL patterns for Dashboard app.
"""

from django.urls import path

from .views import DashboardSummaryView, DashboardStatsView

urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
