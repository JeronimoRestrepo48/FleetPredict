"""FR17: Route optimizer views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, View
from django.template.response import TemplateResponse

from .models import Route, RouteSuggestion
from .forms import RoutePlannerForm
from .optimizer import generate_suggestions
from apps.vehicles.visibility import visible_vehicle_queryset


def _visible_routes_queryset(user):
    qs = Route.objects.select_related('vehicle', 'created_by')
    if user.is_administrator or user.is_fleet_manager:
        return qs
    vehicle_qs = visible_vehicle_queryset(user)
    return qs.filter(vehicle__in=vehicle_qs)


class RoutePlannerView(LoginRequiredMixin, View):
    def get(self, request):
        form = RoutePlannerForm(user=request.user)
        return TemplateResponse(request, 'routes/planner.html', {'form': form})

    def post(self, request):
        form = RoutePlannerForm(request.POST, user=request.user)
        if form.is_valid():
            route = form.save(commit=False)
            route.created_by = request.user
            route.save()
            suggestions = generate_suggestions(route)
            RouteSuggestion.objects.bulk_create(suggestions)
            return redirect('routes:suggestions', pk=route.pk)
        return TemplateResponse(request, 'routes/planner.html', {'form': form})


class RouteSuggestionsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        route = get_object_or_404(_visible_routes_queryset(request.user), pk=pk)
        suggestions = route.suggestions.all()
        return TemplateResponse(request, 'routes/suggestions.html', {
            'route': route, 'suggestions': suggestions,
        })


class RouteSelectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        suggestion = get_object_or_404(
            RouteSuggestion.objects.select_related('route'),
            pk=pk,
            route__in=_visible_routes_queryset(request.user),
        )
        route = suggestion.route
        route.status = Route.Status.SELECTED
        route.save(update_fields=['status'])
        route.suggestions.update(selected=False)
        suggestion.selected = True
        suggestion.save(update_fields=['selected'])
        messages.success(request, f'Route alternative {suggestion.alternative_number} selected.')
        return redirect('routes:suggestions', pk=route.pk)


class RouteHistoryView(LoginRequiredMixin, ListView):
    model = Route
    template_name = 'routes/history.html'
    context_object_name = 'routes'
    paginate_by = 20

    def get_queryset(self):
        return _visible_routes_queryset(self.request.user)
