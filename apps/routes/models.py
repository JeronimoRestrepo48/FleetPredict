"""
FR17: Intelligent Route Optimizer models.
"""
from django.db import models
from django.conf import settings


class Route(models.Model):
    """A route request from a user for a specific vehicle."""

    class Status(models.TextChoices):
        PLANNING = 'planning', 'Planning'
        SELECTED = 'selected', 'Selected'
        COMPLETED = 'completed', 'Completed'

    class OptPriority(models.TextChoices):
        DISTANCE = 'distance', 'Shortest distance'
        TIME = 'time', 'Fastest time'
        FUEL = 'fuel', 'Lowest fuel cost'

    vehicle = models.ForeignKey(
        'vehicles.Vehicle', on_delete=models.CASCADE, related_name='routes',
    )
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    optimization_priority = models.CharField(
        max_length=10, choices=OptPriority.choices, default=OptPriority.DISTANCE,
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PLANNING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.origin} -> {self.destination} ({self.vehicle})'


class RouteSuggestion(models.Model):
    """An alternative suggestion for a route."""

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='suggestions')
    alternative_number = models.PositiveSmallIntegerField(default=1)
    distance_km = models.DecimalField(max_digits=8, decimal_places=2)
    estimated_time_min = models.PositiveIntegerField()
    fuel_cost = models.DecimalField(max_digits=8, decimal_places=2)
    vehicle_condition_impact = models.TextField(blank=True)
    recommended = models.BooleanField(default=False)
    selected = models.BooleanField(default=False)

    class Meta:
        ordering = ['alternative_number']

    def __str__(self):
        return f'Alt {self.alternative_number}: {self.distance_km} km, {self.estimated_time_min} min'
