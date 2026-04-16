"""Shared vehicle visibility helpers across apps."""

from apps.vehicles.models import Vehicle


def visible_vehicle_queryset(user):
    """Vehicles visible to a user according to role."""
    qs = Vehicle.objects.filter(is_deleted=False)
    if getattr(user, "is_driver", False):
        qs = qs.filter(assigned_driver=user)
    return qs


def visible_vehicle_ids(user):
    """Set of visible vehicle IDs for cheap membership checks."""
    return set(visible_vehicle_queryset(user).values_list("id", flat=True))


def can_access_vehicle(user, vehicle_id):
    """True if the user can access the given vehicle ID."""
    return vehicle_id in visible_vehicle_ids(user)
