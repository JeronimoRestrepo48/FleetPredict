"""
Signals for Users app.
Automatically create UserProfile when a User is created.
"""

from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import User, UserProfile
from apps.dashboard.audit import log_audit


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile instance when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    log_audit(request, 'login', 'User', user.pk, 'User logged in')


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    if user:
        log_audit(request, 'logout', 'User', user.pk, 'User logged out')
