from django.urls import path

from users import views
from django.contrib.auth import views as auth_views
from users.htmx import PlayersHTMXView
from users.forms import LoginForm, PwdResetForm, NewPwdForm


urlpatterns = [
    path('logout/', views.user_logout, name='logout'),
    path('password_change/', views.PwdChangeView.as_view(
        template_name='users/base.html'
    ), name='password_change'),
    path('password_change_done/', views.PwdChangeView.as_view(), name='password_change_done'),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("join/", views.JoinView.as_view(), name='join'),
    path("join/<uidb64>", views.EmailConfirmedView.as_view(), name='join'),
    path("email_change_confirm/<uidb64>", views.EmailChangeConfirmedView.as_view(), name='email_change_confirm'),
    path("invite/", views.InviteFriendsView.as_view(), name='invite'),
    path("login/", views.CustomLoginView.as_view(form_class=LoginForm, extra_context={"header": "Login"}), name="login"),
    path("validate_email/<uidb64>", views.ValidateEmailView.as_view(), name='validate_email'),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="users/templates/registration/login.html")),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='users/pwd_reset.html',
        html_email_template_name='emails/password_reset_email.html',
        form_class=PwdResetForm
    ), name='password_reset'),
    path('password_reset_done/', views.PwdResetRequestSentView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.PwdResetConfirmView.as_view(
        form_class=NewPwdForm
    ), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordChangeDoneView.as_view(), name='password_reset_complete'),
    path('htmx/', PlayersHTMXView.as_view(), name='users-htmx'),
    path('unsubscribe/<token>', views.UnsubscribeView.as_view(), name='unsubscribe'),
    path('subscribe/<token>', views.SubscribeView.as_view(), name='subscribe')
]
