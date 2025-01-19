from django.utils.translation import ugettext_lazy as _
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth.password_validation import password_validators_help_text_html
from .models import Player, PendingEmail, LOCATIONS, custom_validate_email


class PlayerCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = Player
        fields = ("email",)


class PlayerChangeForm(UserChangeForm):
    class Meta:
        model = Player
        fields = ("email",)


class PlayerProfileForm(forms.ModelForm):
    birth_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)

    class Meta:
        model = Player
        fields = (
            "email",
            "first_name",
            "last_name",
            "display_name",
            "location",
            "birth_date",
            "subscribed",
            "reminder",
        )
        help_texts = {
            "subscribed": "Unchecking this will remove you from the game emails.",
            "reminder": "You will be receive game play reminders even if you played the game this week.",
            "display_name": "This is what displays on the public leaderboard.",
        }


class PendingEmailForm(forms.ModelForm):
    class Meta:
        model = PendingEmail
        fields = ("email",)

    email = forms.EmailField(label="", max_length=256, widget=forms.TextInput(attrs={"placeholder": "Email"}))


class InviteFriendsForm(forms.Form):
    emails = forms.CharField(
        max_length=256,
        help_text="Enter multiple emails as a comma separated list, e.g. john@thebeatles.com, paul@thebeatles.com",
    )


class JoinForm(PlayerCreationForm):
    required_css_class = "required"
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    display_name = forms.CharField(max_length=100, help_text="This is what displays on the public leaderboard.")
    location = forms.CharField(label="Where do you live?", widget=forms.Select(choices=LOCATIONS), required=False)
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password"},
        ),
        required=False,
        help_text="Passwords are optional.  Leave it out if you want to use email magic links instead.",
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        required=False,
        help_text=password_validators_help_text_html(),
    )

    class Meta(UserCreationForm):
        model = Player
        fields = ("email", "first_name", "last_name", "display_name", "password1", "password2", "location")

    def is_valid(self):
        # email must be valid because the join link was sent to it
        # skipping so form doesn't throw duplicate email validation
        # that is handled in the view using JoinForm(request.POST, instance=user)
        self.errors.pop("email", None)
        valid = super().is_valid()
        return valid


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        validators=[custom_validate_email], widget=forms.TextInput(attrs={"class": "w3-input", "autofocus": True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "w3-input"}),
        required=False,
        help_text="Leave blank to login without password, we'll send you a link.",
    )

    def clean_username(self):
        email = self.cleaned_data["username"]
        p = Player.objects.filter(email=email).first()
        if p is None or (not p.is_active):
            raise forms.ValidationError(_("The email address entered is not associated with an active account."))
        return email


class PwdResetForm(PasswordResetForm):
    email = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "w3-input", "autofocus": True},
        )
    )


class NewPwdForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "w3-input"}),
    )
    new_password2 = forms.CharField(
        label="New password confirmation",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "w3-input"}),
        strip=False,
        help_text=password_validators_help_text_html(),
    )
