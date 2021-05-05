from django import forms


class TabulatorForm(forms.Form):

    def __init__(self, series_choices):
        super().__init__()
        self.fields['series'].widget.choices = [("", "")] + series_choices
        self.fields['series'].initial = "Please Select"

    series = forms.CharField(widget=forms.Select(attrs={'class': 'w3-input'}), required=True)
    sheet_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'w3-input'}))
    update_existing = forms.BooleanField(
        label="Update existing answer records (slower) ",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w3-check',
            'style': "margin-left: 8px"
        })
    )
