"""
User management URL patterns.
"""

from django.urls import path

from ..views import (
    ProfileView,
    ChangePasswordView,
    UserListView,
    UserDetailView,
)

urlpatterns = [
    # Profile endpoints (FR21)
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # User management endpoints (FR1 - Admin only)
    path('', UserListView.as_view(), name='user-list'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]
