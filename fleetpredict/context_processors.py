"""
Context processors for FleetPredict Pro.
Adds alerts_unread_count and recent_alerts_inbox for nav badge and dropdown.
"""

from apps.vehicles.models import Vehicle, VehicleAlert
from apps.vehicles.visibility import visible_vehicle_queryset


def alerts_unread_count(request):
    """Add alerts_unread_count and recent_alerts_inbox for the navbar bell dropdown."""
    out = {'alerts_unread_count': 0, 'recent_alerts_inbox': []}
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return out
    user = request.user
    vehicle_ids = visible_vehicle_queryset(user)
    vehicle_ids = list(vehicle_ids.values_list('id', flat=True))
    if not vehicle_ids:
        return out
    unread_qs = VehicleAlert.objects.filter(
        vehicle_id__in=vehicle_ids,
        read_at__isnull=True,
    )
    out['alerts_unread_count'] = unread_qs.count()
    out['recent_alerts_inbox'] = list(
        VehicleAlert.objects.filter(vehicle_id__in=vehicle_ids)
        .select_related('vehicle')
        .order_by('-created_at')[:8]
    )
    return out
