from django import forms


class TabulatorForm(forms.Form):
    sheet_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'w3-input'}))
    update_existing = forms.BooleanField(
        label="Update existing answer records (slower) ",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w3-check',
            'style': "margin-left: 8px"
        })
    )
