from django.urls import path
from .views import RoutePlannerView, RouteSuggestionsView, RouteSelectView, RouteHistoryView

app_name = 'routes'

urlpatterns = [
    path('', RoutePlannerView.as_view(), name='planner'),
    path('<int:pk>/suggestions/', RouteSuggestionsView.as_view(), name='suggestions'),
    path('select/<int:pk>/', RouteSelectView.as_view(), name='select'),
    path('history/', RouteHistoryView.as_view(), name='history'),
]
