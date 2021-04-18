from django import forms
from .models import MassMailMessage
from ckeditor.fields import RichTextField, CKEditorWidget


class MassEmailForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = MassMailMessage
        fields = ['message']
