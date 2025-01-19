from django import forms
from game.models import Question, Answer


class TabulatorForm(forms.Form):

    def __init__(self, series_choices):
        super().__init__()
        self.fields["series"].widget.choices = [("", "")] + series_choices
        self.fields["series"].initial = "Please Select"

    series = forms.CharField(widget=forms.Select(attrs={"class": "w3-input"}), required=True)
    sheet_name = forms.CharField(widget=forms.TextInput(attrs={"class": "w3-input"}))
    update_existing = forms.BooleanField(
        label="Update existing answer records (slower) ",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "w3-check", "style": "margin-left: 8px"}),
    )


class QuestionAnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ("question", "raw_string", "player")

    question = forms.ModelChoiceField(queryset=Question.objects.all(), widget=forms.HiddenInput())
    raw_string = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={"class": "w3-input", "placeholder": "Your answer"}),
        max_length=1000,
        error_messages={"required": "This is a required question"},
    )

    def __init__(self, question, editable=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not editable:
            self.fields["raw_string"].disabled = True
            self.fields["raw_string"].widget.attrs["placeholder"] = ""

        self.fields["question"].initial = question
        self.fields["player"].required = False

        self.q = question
        if self.q.choices:
            # hide default CharField and render custom "radio button" style input (in template)
            self.fields["raw_string"].widget = forms.HiddenInput(attrs={"required": not self.q.is_optional})
            self.fields["raw_string"].initial = None

        if self.q.is_optional:
            self.fields["raw_string"].required = False

    def clean_raw_string(self):
        value = self.cleaned_data["raw_string"]
        if value and self.q.choices:
            if value not in self.q.choices:
                raise forms.ValidationError(f"{value} isn't a valid choice for this question")
        return value

    def save(self, commit=True):
        if self.q.is_optional and not self.cleaned_data["raw_string"]:
            return
        return super().save(commit)


class GameDisplayNameForm(forms.Form):
    display_name = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={"class": "w3-input", "placeholder": "Your name"}),
        max_length=100,
        error_messages={"required": "This is a required question"},
    )

    def __init__(self, editable=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not editable:
            self.fields["display_name"].disabled = True


class QuestionSuggestionForm(forms.Form):
    suggestion = forms.CharField(
        label="",
        widget=forms.Textarea(
            attrs={
                "placeholder": "Is a hamburger a sandwich?",
                "rows": 4,
                "style": "border: 1px solid lightgrey;border-radius: 4px;",
            }
        ),
        max_length=1000,
        error_messages={"required": "This is a required question"},
    )


class AwardCertificateForm(forms.Form):
    name = forms.CharField(max_length=75)
    game_number = forms.IntegerField(required=True)
