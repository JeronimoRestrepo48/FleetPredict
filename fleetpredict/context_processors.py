"""
Context processors for FleetPredict Pro.
Adds alerts_unread_count for nav badge.
"""

from apps.vehicles.models import Vehicle, VehicleAlert


def alerts_unread_count(request):
    """Add alerts_unread_count for authenticated users (alerts they can see, unread)."""
    out = {'alerts_unread_count': 0}
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return out
    user = request.user
    vehicle_ids = Vehicle.objects.filter(is_deleted=False)
    if user.is_driver:
        vehicle_ids = vehicle_ids.filter(assigned_driver=user)
    vehicle_ids = list(vehicle_ids.values_list('id', flat=True))
    if not vehicle_ids:
        return out
    out['alerts_unread_count'] = VehicleAlert.objects.filter(
        vehicle_id__in=vehicle_ids,
        read_at__isnull=True,
    ).count()
    return out
