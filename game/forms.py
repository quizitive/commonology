from django import forms
from django.utils.safestring import mark_safe
from game.models import Question, Answer


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


class QuestionAnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ('question', 'raw_string', 'player')

    question = forms.ModelChoiceField(queryset=Question.objects.all(), widget=forms.HiddenInput())
    raw_string = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={'class': 'w3-input', 'placeholder': 'Your answer'}),
        max_length=1000,
        error_messages={'required': 'This is a required question'}
    )

    def __init__(self, question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['question'].initial = question
        self.fields['player'].required = False

        self.q = question
        if self.q.choices:
            self.fields['raw_string'].widget = forms.HiddenInput(attrs={'required': True})
            self.fields['raw_string'].initial = None

        if self.q.type in (Question.op, Question.ov):
            self.fields['raw_string'].required = False

    def clean_raw_string(self):
        value = self.cleaned_data['raw_string']
        if self.q.choices:
            if value not in self.q.choices:
                raise forms.ValidationError(f"{value} isn't a valid choice for this question")
        return value

    def as_p(self):
        as_p = super().as_p()
        # a hack to remove standard error formatting, easier than rewriting as_p from scratch
        return mark_safe(as_p.replace("(Hidden field raw_string)", ""))
