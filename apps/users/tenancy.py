"""Multi-tenant helpers: scope querysets by organization."""

from django.db.models import Q


def user_organization_id(user):
    return getattr(user, 'organization_id', None) or None


def vehicles_queryset_for_user(user, base=None):
    """
    Vehicles visible to user: superuser sees all; others only their organization.
    Drivers only see assigned vehicles within the org.
    """
    from apps.vehicles.models import Vehicle

    qs = base if base is not None else Vehicle.objects.filter(is_deleted=False)
    if getattr(user, 'is_superuser', False):
        return qs
    oid = user_organization_id(user)
    if not oid:
        return qs.none()
    qs = qs.filter(organization_id=oid)
    if getattr(user, 'is_driver', False):
        qs = qs.filter(assigned_driver=user)
    return qs


def users_in_same_organization_queryset(user, base=None):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    qs = base if base is not None else User.objects.all()
    if getattr(user, 'is_superuser', False):
        return qs
    oid = user_organization_id(user)
    if not oid:
        return qs.none()
    return qs.filter(organization_id=oid)


def organization_filter_q(user):
    if getattr(user, 'is_superuser', False):
        return Q()
    oid = user_organization_id(user)
    if not oid:
        return Q(pk__in=[])
    return Q(organization_id=oid)
