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
    birth_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)

    class Meta:
        model = Player
        fields = ('email', 'first_name', 'last_name', 'display_name', 'location',
                  'birth_date', 'subscribed')
        help_texts = {
            'subscribed': 'Unchecking this will remove you from the game emails.',
            'display_name': 'This is what displays on the public leaderboard. If left '
                            'blank we will use your first and last name.'
        }


class PendingEmailForm(forms.ModelForm):
    email = forms.CharField(widget=forms.TextInput(attrs={'class': 'w3-input'}))

    class Meta:
        model = PendingEmail
        fields = ('email',)


class InviteFriendsForm(forms.Form):
    emails = forms.CharField(
        max_length=256,
        help_text="Enter multiple emails as a comma separated list, e.g. john@thebeatles.com, paul@thebeatles.com"
    )


class JoinForm(PlayerCreationForm):
    required_css_class = 'required'
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    display_name = forms.CharField(
        max_length=100,
        help_text="This is what displays on the public leaderboard. If left "
                  "blank we will use your first and last name."
    )
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
        help_texts = {
            'display_name': 'This is what displays on the public leaderboard. If left '
                            'blank we will use your first and last name.'
        }


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
