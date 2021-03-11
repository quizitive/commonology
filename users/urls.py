from django.urls import include, path
from django.contrib.auth import views as auth_views

from users.views import user_logout, profile_view, join_view, \
    email_confirmed_view, send_invite_view
from users.htmx import PlayersHTMXView
from users.forms import LoginForm


app_name = 'users'

urlpatterns = [
    path('logout/', user_logout, name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change_done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path("profile/", profile_view, name="profile"),
    path("join/<uidb64>", email_confirmed_view, name='join'),
    path("join/", join_view, name='join'),
    path("invite/", send_invite_view, name='invite'),
    path("login/", auth_views.LoginView.as_view(template_name="users/login.html", form_class=LoginForm), name="login"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="users/login.html")),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('htmx/', PlayersHTMXView.as_view(), name='htmx')
]
