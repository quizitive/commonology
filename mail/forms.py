from django import forms
from .models import MassMailMessage


class MassEmailForm(forms.ModelForm):

    class Meta:
        model = MassMailMessage
        fields = ['message']
