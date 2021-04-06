from django import forms
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, \
    AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.utils.translation import gettext, gettext_lazy as _
from django.contrib.auth.password_validation import password_validators_help_text_html
from .models import Player, PendingEmail, LOCATIONS, MAX_LOCATION_LEN


class PlayerCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = Player
        fields = ('email',)


class PlayerChangeForm(UserChangeForm):
    class Meta:
        model = Player
        fields = ('email',)


class PlayerProfileForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ('email', 'first_name', 'last_name', 'location', 'birth_date')


class PendingEmailForm(forms.ModelForm):
    email = forms.CharField(widget=forms.TextInput(attrs={'class': 'w3-input'}))

    class Meta:
        model = PendingEmail
        fields = ('email',)


class JoinForm(PlayerCreationForm):
    required_css_class = 'required'
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    display_name = forms.CharField(max_length=30, help_text="This displays on the public leaderboard")
    location = forms.CharField(label='Where do you live?',
                               widget=forms.Select(choices=LOCATIONS),
                               required=False)
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=password_validators_help_text_html(),
    )

    class Meta(UserCreationForm):
        model = Player
        fields = ('email', 'first_name', 'last_name', 'display_name',
                  'password1', 'password2', 'location')


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'w3-input',
                'autofocus': True
            },
        )
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w3-input'}))


class PwdResetForm(PasswordResetForm):
    email = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'w3-input',
                'autofocus': True
            },
        )
    )


class NewPwdForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'new-password', 'class': 'w3-input'}),
    )
    new_password2 = forms.CharField(
        label="New password confirmation",
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'new-password', 'class': 'w3-input'}),
        strip=False,
        help_text=password_validators_help_text_html(),
    )
