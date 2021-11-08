from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from mail.models import FROM_ADDRS


class OneMailForm(forms.Form):
    email = forms.CharField(max_length=75, required=True)
    from_email = forms.CharField(widget=forms.Select(choices=FROM_ADDRS))
    subject = forms.CharField(max_length=150)
    message = forms.CharField(widget=CKEditorUploadingWidget())
