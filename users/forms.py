from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
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
        fields = ('email', 'first_name', 'last_name', 'location', 'birth_date', 'referrer')


class PendingEmailForm(forms.ModelForm):

    class Meta:
        model = PendingEmail
        fields = ('email',)


class JoinForm(PlayerCreationForm):
    required_css_class = 'required'
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    location = forms.CharField(label='Where do you live?',
                               widget=forms.Select(choices=LOCATIONS),
                               required=False)

    class Meta(UserCreationForm):
        model = Player
        fields = ('email', 'first_name', 'last_name', 'location')
