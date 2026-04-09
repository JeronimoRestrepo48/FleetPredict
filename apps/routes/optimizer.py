"""
FR17: Route suggestion generator.
Produces 3 route alternatives considering vehicle health and maintenance.
"""
import random
from decimal import Decimal


def generate_suggestions(route):
    """
    Generate 3 route alternatives for the given Route object.
    Uses mock data since there's no real mapping API.
    Returns a list of RouteSuggestion instances (unsaved).
    """
    from .models import RouteSuggestion

    vehicle = route.vehicle
    health = vehicle.get_health_status()

    base_distance = random.uniform(20, 200)
    base_time = base_distance / random.uniform(40, 80) * 60
    base_fuel = base_distance * random.uniform(0.08, 0.15) * random.uniform(3, 6)

    health_warnings = {
        'red': 'Vehicle in critical condition — short routes recommended.',
        'yellow': 'Vehicle needs attention — monitor closely on long trips.',
        'green': 'Vehicle in good condition.',
    }

    suggestions = []
    for i in range(1, 4):
        factor = 1 + (i - 1) * random.uniform(0.05, 0.2)
        dist = round(base_distance * factor, 2)
        time_min = int(base_time * factor * random.uniform(0.9, 1.1))
        fuel = round(base_fuel * factor, 2)

        impact = health_warnings.get(health, '')
        if health == 'red' and dist > 100:
            impact += ' Long distance NOT recommended for this vehicle.'

        suggestions.append(RouteSuggestion(
            route=route,
            alternative_number=i,
            distance_km=Decimal(str(dist)),
            estimated_time_min=time_min,
            fuel_cost=Decimal(str(fuel)),
            vehicle_condition_impact=impact,
            recommended=(i == 1),
        ))

    if route.optimization_priority == 'distance':
        suggestions.sort(key=lambda s: s.distance_km)
    elif route.optimization_priority == 'time':
        suggestions.sort(key=lambda s: s.estimated_time_min)
    elif route.optimization_priority == 'fuel':
        suggestions.sort(key=lambda s: s.fuel_cost)

    suggestions[0].recommended = True
    for idx, s in enumerate(suggestions, 1):
        s.alternative_number = idx

    return suggestions
