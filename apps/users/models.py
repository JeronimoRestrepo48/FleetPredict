"""
User models for FleetPredict Pro.
Implements FR1 (Role-based access control) and FR21 (User profile management).
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.Role.ADMINISTRATOR)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email authentication and role-based access control.
    Implements FR1: Role-based access control.
    """

    class Role(models.TextChoices):
        ADMINISTRATOR = 'administrator', 'Administrator'
        FLEET_MANAGER = 'fleet_manager', 'Fleet Manager'
        MECHANIC = 'mechanic', 'Mechanic'
        DRIVER = 'driver', 'Driver'

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DRIVER
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMINISTRATOR

    @property
    def is_fleet_manager(self):
        return self.role == self.Role.FLEET_MANAGER

    @property
    def is_mechanic(self):
        return self.role == self.Role.MECHANIC

    @property
    def is_driver(self):
        return self.role == self.Role.DRIVER

    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role == self.Role.ADMINISTRATOR

    def can_manage_vehicles(self):
        """Check if user can create/edit/delete vehicles."""
        return self.role in [self.Role.ADMINISTRATOR, self.Role.FLEET_MANAGER]

    def can_manage_maintenance(self):
        """Check if user can create/edit maintenance tasks."""
        return self.role in [
            self.Role.ADMINISTRATOR,
            self.Role.FLEET_MANAGER,
            self.Role.MECHANIC
        ]

    def can_view_reports(self):
        """Check if user can view reports."""
        return self.role in [self.Role.ADMINISTRATOR, self.Role.FLEET_MANAGER]

    def can_manage_platform(self):
        """Check if user can manage platform settings (users, vehicle types, audit)."""
        return self.role == self.Role.ADMINISTRATOR


class UserProfile(models.Model):
    """
    Extended user profile with additional information.
    Implements FR21: User profile management.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )
    preferences = models.JSONField(default=dict, blank=True)
    notification_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text='Notification preferences (email, in-app, etc.)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f'Profile of {self.user.email}'

    def get_default_notification_settings(self):
        """Return default notification settings."""
        return {
            'email_enabled': True,
            'maintenance_due': True,
            'maintenance_overdue': True,
            'critical_alerts': True,
            'predictions': True,
        }

    def save(self, *args, **kwargs):
        """Set default notification settings if empty."""
        if not self.notification_settings:
            self.notification_settings = self.get_default_notification_settings()
        super().save(*args, **kwargs)
