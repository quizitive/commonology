from django import forms
from rewards.models import MailingAddress


class ClaimForm(forms.ModelForm):

    class Meta:
        model = MailingAddress
        fields = ('Full Name', 'Address line 1', 'Address line 2', 'City', 'State', 'ZIP / Postal code')
