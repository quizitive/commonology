from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils import timezone
from django.conf import settings
from game.models import Series


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
    created = models.DateTimeField(default=timezone.now)
    tested = models.BooleanField(default=False,
                                 help_text="Must be checked to send blast.  It is set when a test message is sent.")
    enable_blast = models.BooleanField(default=False,
                                       help_text="Must be check to send blast.")
    sent = models.BooleanField(default=False,
                               help_text="You can uncheck this to send blast again.")
