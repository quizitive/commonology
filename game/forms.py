from django import forms
from game.models import Question


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


class QuestionAnswerForm(forms.Form):
    question_id = forms.IntegerField(widget=forms.HiddenInput())
    raw_string = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={'class': 'w3-input', 'placeholder': 'Your answer'})
    )

    def __init__(self, question_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['question_id'].initial = question_id

        q = Question.objects.get(id=question_id)
        if q.choices:
            self.fields['raw_string'].widget = forms.HiddenInput()
            self.fields['raw_string'].initial = None

        if q.type in (Question.op, Question.ov):
            self.fields['raw_string'].required = False

    def clean_raw_string(self):
        value = self.cleaned_data['raw_string']
        if not value:
            raise forms.ValidationError("Please enter a response!")
        return value
