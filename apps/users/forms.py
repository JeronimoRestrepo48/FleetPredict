"""
Forms for Users app.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password

from .models import User, UserProfile


class UserRegistrationForm(UserCreationForm):
    """Form for user registration."""

    role = forms.ChoiceField(
        choices=User.Role.choices,
        initial=User.Role.DRIVER,
        required=True
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['role'].widget.attrs.update({'class': 'form-select'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class ProfileForm(forms.ModelForm):
    """Form for editing user profile."""

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email_enabled = forms.BooleanField(required=False, initial=True)
    maintenance_due = forms.BooleanField(required=False, initial=True)
    maintenance_overdue = forms.BooleanField(required=False, initial=True)
    critical_alerts = forms.BooleanField(required=False, initial=True)

    class Meta:
        model = UserProfile
        fields = ('phone',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
        ns = getattr(self.instance, 'notification_settings', None) or {}
        self.fields['email_enabled'].initial = ns.get('email_enabled', True)
        self.fields['maintenance_due'].initial = ns.get('maintenance_due', True)
        self.fields['maintenance_overdue'].initial = ns.get('maintenance_overdue', True)
        self.fields['critical_alerts'].initial = ns.get('critical_alerts', True)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})
        for name in ('email_enabled', 'maintenance_due', 'maintenance_overdue', 'critical_alerts'):
            self.fields[name].widget.attrs.update({'class': 'form-check-input'})

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.save()
        profile.notification_settings = {
            'email_enabled': self.cleaned_data.get('email_enabled', True),
            'maintenance_due': self.cleaned_data.get('maintenance_due', True),
            'maintenance_overdue': self.cleaned_data.get('maintenance_overdue', True),
            'critical_alerts': self.cleaned_data.get('critical_alerts', True),
        }
        if commit:
            profile.save()
        return profile
