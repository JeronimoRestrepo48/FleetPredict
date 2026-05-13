"""
URL configuration for Users app.
Auth routes at root; user management under /users/.
"""

from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('invite/<uidb64>/<token>/', views.InviteSetPasswordView.as_view(), name='invite_set_password'),
    path('team/', views.OrgTeamListView.as_view(), name='org_team_list'),
    path('team/invite/', views.OrgTeamInviteView.as_view(), name='org_team_invite'),
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/password/', views.PasswordChangeView.as_view(), name='password_change'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
]
