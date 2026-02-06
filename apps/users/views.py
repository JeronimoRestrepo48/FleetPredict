"""
Views for Users app.
Implements FR1 (Role-based access control) and FR21 (User profile management).
Uses Django MVT - session-based auth, template rendering.
"""

from django.contrib.auth import login
from django.contrib.auth.views import (
    LoginView as AuthLoginView,
    LogoutView as AuthLogoutView,
    PasswordChangeView as AuthPasswordChangeView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    FormView,
    UpdateView,
    ListView,
    DetailView,
)
from django.db.models import Q

from .models import User, UserProfile
from .forms import UserRegistrationForm, ProfileForm


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin that requires user to be administrator."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'administrator'


# ============== Authentication Views (FR1) ==============

class LoginView(AuthLoginView):
    """Login view - uses Django session auth."""

    template_name = 'registration/login.html'
    redirect_authenticated_user = True


class LogoutView(AuthLogoutView):
    """Logout view."""

    next_page = 'users:login'


class RegisterView(FormView):
    """User registration view."""

    template_name = 'registration/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, 'Registration successful. You can now log in.')
        return redirect(self.success_url)


class ProfileView(LoginRequiredMixin, UpdateView):
    """Profile view - edit user profile (FR21)."""

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


# ============== User Management Views (Admin only) ==============

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List users (admin only)."""

    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = User.Role.choices
        return context


class UserDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """User detail view (admin only)."""

    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'
