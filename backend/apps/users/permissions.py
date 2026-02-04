"""
Custom permissions for Users app.
Implements FR1: Role-based access control.
"""

from rest_framework import permissions


class IsAdministrator(permissions.BasePermission):
    """
    Permission check for Administrator role.
    """
    message = 'Only administrators can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_administrator
        )


class IsFleetManagerOrAdmin(permissions.BasePermission):
    """
    Permission check for Fleet Manager or Administrator roles.
    """
    message = 'Only fleet managers and administrators can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_administrator or request.user.is_fleet_manager)
        )


class IsMechanicOrAbove(permissions.BasePermission):
    """
    Permission check for Mechanic, Fleet Manager, or Administrator roles.
    """
    message = 'Insufficient permissions for this action.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['administrator', 'fleet_manager', 'mechanic']
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission check for object owners or administrators.
    """
    message = 'You can only modify your own data.'

    def has_object_permission(self, request, view, obj):
        # Admins can access anything
        if request.user.is_administrator:
            return True
        # Users can only access their own objects
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user


class CanManageVehicles(permissions.BasePermission):
    """
    Permission check for vehicle management.
    """
    message = 'You do not have permission to manage vehicles.'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return (
            request.user and
            request.user.is_authenticated and
            request.user.can_manage_vehicles()
        )


class CanManageMaintenance(permissions.BasePermission):
    """
    Permission check for maintenance management.
    """
    message = 'You do not have permission to manage maintenance tasks.'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return (
            request.user and
            request.user.is_authenticated and
            request.user.can_manage_maintenance()
        )
