from django import forms
from rewards.models import MailingAddress


class ClaimForm(forms.ModelForm):

    class Meta:
        model = MailingAddress
        fields = ("name", "address1", "address2", "city", "state", "zip_code")
