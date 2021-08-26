from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from sortedm2m.fields import SortedManyToManyField
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from game.models import Series


class Component(models.Model):
    name = models.CharField(max_length=150, unique=True)
    message = RichTextUploadingField(null=True, blank=True)
    template = models.CharField(max_length=150, default='mail/simple_component.html')
    context = models.JSONField(default=dict, blank=True)

    top = 'top'
    btm = 'btm'
    LOCATION_CHOICES = [
        (top, 'Top'),
        (btm, 'Bottom'),
    ]
    location = models.CharField(max_length=3, choices=LOCATION_CHOICES, default='btm')

    def __str__(self):
        return f"{self.name} ({next(l for l in self.LOCATION_CHOICES if l[0] == self.location)[1]})"

    @property
    def render(self):
        self.context['component'] = self
        return render_to_string(self.template, self.context)

    @property
    def css_name(self):
        return self.name.lower().replace(' ', '-')


FROM_ADDRS = [(i, i) for i in [
    "alex@commonologygame.com",
    "ms@commonologygame.com",
    "ted@commonologygame.com",
    "concierge@commonologygame.com"]]


class MailMessage(models.Model):
    series = models.ForeignKey(Series, blank=False, on_delete=models.SET_NULL, null=True, default=1,
                               help_text="Only subscribed players will receive the email.")
    from_name = models.CharField(max_length=150, blank=False, default=settings.ALEX_FROM_NAME)
    from_email = models.EmailField('from email address', choices=FROM_ADDRS, default=settings.ALEX_FROM_EMAIL)
    test_recipient = models.EmailField('test recipient email address')
    categories = models.CharField(max_length=50, blank=True,
                                  help_text="A comma separated list of categories. i.e GameOn|Reminder|Resuts + Week#")
    subject = models.CharField(max_length=150, blank=False)
    message = RichTextUploadingField(blank=True,
                                     help_text='Play link example: https://commonologygame.com/play?-game_url_args-')
    components = SortedManyToManyField(Component, blank=True, related_name='messages')
    created = models.DateTimeField(default=timezone.now)
    tested = models.BooleanField(default=False,
                                 help_text="Must be checked to send blast.  It is set when a test message is sent.")
    enable_blast = models.BooleanField(default=False,
                                       help_text="Must be check to send blast.")
    sent = models.BooleanField(default=False,
                               help_text="You can uncheck this to send blast again.")
