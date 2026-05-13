"""
Forms for Users app.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.text import slugify

from .models import Organization, User, UserProfile


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


class FleetCompanyRegistrationForm(forms.Form):
    """Public signup: create organization + single fleet manager account."""

    organization_name = forms.CharField(max_length=200, label='Company / organization name')
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.fields:
            w = self.fields[name].widget
            if hasattr(w, 'attrs'):
                w.attrs.setdefault('class', 'form-control')

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data['email'])
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        data = super().clean()
        p1, p2 = data.get('password1'), data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('The two password fields do not match.')
        if p1:
            validate_password(p1)
        return data

    @transaction.atomic
    def save(self):
        org_name = self.cleaned_data['organization_name'].strip()
        base = (slugify(org_name) or 'company')[:72]
        slug = base
        n = 0
        while Organization.objects.filter(slug=slug).exists():
            n += 1
            slug = f'{base}-{n}'
        org = Organization.objects.create(name=org_name, slug=slug)
        return User.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['first_name'].strip(),
            last_name=self.cleaned_data['last_name'].strip(),
            role=User.Role.FLEET_MANAGER,
            organization=org,
        )


class TeamMemberInviteForm(forms.Form):
    """Fleet manager invites a mechanic or driver (password set via email link)."""

    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    role = forms.ChoiceField(
        choices=[
            (User.Role.MECHANIC, 'Mechanic'),
            (User.Role.DRIVER, 'Driver'),
        ]
    )

    def __init__(self, *args, organization=None, **kwargs):
        self.organization = organization
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.setdefault('class', 'form-control')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data['email'])
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('This email is already registered.')
        return email

    @transaction.atomic
    def save(self):
        user = User(
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'].strip(),
            last_name=self.cleaned_data['last_name'].strip(),
            role=self.cleaned_data['role'],
            organization=self.organization,
        )
        user.set_unusable_password()
        user.save()
        return user
