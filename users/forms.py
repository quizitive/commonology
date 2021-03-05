from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser, PendingEmail, LOCATIONS, MAX_LOCATION_LEN


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = CustomUser
        fields = ('email',)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email',)


class CustomUserDashboardForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'location', 'birth_date', 'referrer')


class PendingEmailForm(forms.ModelForm):

    class Meta:
        model = PendingEmail
        fields = ('email',)


class JoinForm(CustomUserCreationForm):
    required_css_class = 'required'
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    location = forms.CharField(label='Where do you live?',
                               widget=forms.Select(choices=LOCATIONS),
                               required=False)

    class Meta(UserCreationForm):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'location')
