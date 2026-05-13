"""
Views for Users app.
Implements FR1 (Role-based access control) and FR21 (User profile management).
Uses Django MVT - session-based auth, template rendering.
"""

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    LoginView as AuthLoginView,
    LogoutView as AuthLogoutView,
    PasswordChangeView as AuthPasswordChangeView,
    PasswordResetView as AuthPasswordResetView,
    PasswordResetDoneView as AuthPasswordResetDoneView,
    PasswordResetConfirmView as AuthPasswordResetConfirmView,
    PasswordResetCompleteView as AuthPasswordResetCompleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    FormView,
    UpdateView,
    ListView,
    DetailView,
)
from django.db.models import Q

from .models import User, UserProfile
from .forms import FleetCompanyRegistrationForm, ProfileForm, TeamMemberInviteForm


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin that requires global platform access."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_platform()


class FleetManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_organization_team()


# ============== Authentication Views ==============


class LoginView(AuthLoginView):
    """Login view - uses Django session auth."""

    template_name = 'registration/login.html'
    redirect_authenticated_user = True


class LogoutView(AuthLogoutView):
    """Logout view."""

    next_page = 'users:login'


class RegisterView(FormView):
    """Register as fleet manager and create a new organization."""

    template_name = 'registration/register.html'
    form_class = FleetCompanyRegistrationForm
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        user = form.save()
        messages.success(
            self.request,
            _('Registration successful. You can now log in as fleet manager for %(org)s.')
            % {'org': user.organization.name},
        )
        return redirect(self.success_url)


class InviteSetPasswordView(AuthPasswordResetConfirmView):
    """Mechanic/driver sets password from invitation link (same token flow as password reset)."""

    template_name = 'registration/invite_set_password.html'
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Your password has been set. You can log in now.'))
        return response


class OrgTeamListView(LoginRequiredMixin, FleetManagerRequiredMixin, ListView):
    """Fleet manager: list users in the same organization."""

    model = User
    template_name = 'users/org_team_list.html'
    context_object_name = 'members'
    paginate_by = 30

    def get_queryset(self):
        return (
            User.objects.filter(organization_id=self.request.user.organization_id)
            .order_by('role', 'email')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['organization'] = self.request.user.organization
        return ctx


class OrgTeamInviteView(LoginRequiredMixin, FleetManagerRequiredMixin, FormView):
    """Invite mechanic or driver: create account and email set-password link."""

    template_name = 'users/org_team_invite.html'
    form_class = TeamMemberInviteForm
    success_url = reverse_lazy('users:org_team_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def form_valid(self, form):
        user = form.save()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        link = self.request.build_absolute_uri(
            reverse('users:invite_set_password', kwargs={'uidb64': uid, 'token': token})
        )
        subject = _('Your FleetPredict Pro account')
        body = _('You were invited to join %(org)s on FleetPredict Pro.\n\n'
                  'Open this link to set your password and sign in:\n%(link)s\n\n'
                  'If you did not expect this message, you can ignore it.') % {
            'org': self.request.user.organization.name,
            'link': link,
        }
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
            messages.success(
                self.request,
                _('Invitation sent to %(email)s. They must use the link in the email to set a password.')
                % {'email': user.email},
            )
        except Exception:
            messages.warning(
                self.request,
                _('User %(email)s was created but the invitation email could not be sent. '
                  'Share this link manually: %(link)s')
                % {'email': user.email, 'link': link},
            )
        return redirect(self.success_url)


class ProfileView(LoginRequiredMixin, UpdateView):
    """Profile view - edit user profile."""

    model = UserProfile
    form_class = ProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['first_name'].initial = self.request.user.first_name
        form.fields['last_name'].initial = self.request.user.last_name
        return form

    def form_valid(self, form):
        return super().form_valid(form)


class PasswordChangeView(LoginRequiredMixin, AuthPasswordChangeView):
    """Change password view."""

    template_name = 'registration/password_change.html'
    success_url = reverse_lazy('users:profile')


# ============== Password reset (FR1 acceptance criteria) ==============


class PasswordResetView(AuthPasswordResetView):
    """Request password reset - send email with link."""

    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')


class PasswordResetDoneView(AuthPasswordResetDoneView):
    """Shown after user submits email for reset."""

    template_name = 'registration/password_reset_done.html'


class PasswordResetConfirmView(AuthPasswordResetConfirmView):
    """Set new password from token in email link."""

    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')


class PasswordResetCompleteView(AuthPasswordResetCompleteView):
    """Shown after password has been reset."""

    template_name = 'registration/password_reset_complete.html'


# ============== User Management Views (platform admin) ==============


class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List users (global superuser)."""

    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_paginate_by(self, queryset):
        per = self.request.GET.get('per_page', '20')
        if per in ('10', '20', '50'):
            return int(per)
        return 20

    def get_queryset(self):
        queryset = User.objects.all().select_related('organization')
        org = self.request.GET.get('organization')
        if org:
            queryset = queryset.filter(organization_id=org)
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = User.Role.choices
        from .models import Organization

        context['organizations'] = Organization.objects.order_by('name')
        return context


class UserDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """User detail view (admin only)."""

    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'
