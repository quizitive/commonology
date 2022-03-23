from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from sortedm2m.fields import SortedManyToManyField
from django.utils import timezone
from django.conf import settings
from django.forms import model_to_dict
from game.models import Series
from components.models import Component


FROM_ADDRS = [(i, i) for i in [
    "concierge@commonologygame.com",
    "alex@commonologygame.com",
    "ms@commonologygame.com",
    "ted@commonologygame.com"]]


class MailMessageBase(models.Model):
    series = models.ForeignKey(Series, blank=False, on_delete=models.SET_NULL, null=True, default=1,
                               help_text="Only subscribed players will receive the email.")
    from_name = models.CharField(max_length=150, blank=False, default=settings.ALEX_FROM_NAME)
    from_email = models.EmailField('from email address', choices=FROM_ADDRS, default=settings.ALEX_FROM_EMAIL)
    test_recipient = models.EmailField('test recipient email address')
    categories = models.CharField(max_length=50, blank=True,
                                  help_text="A comma separated list of categories. i.e GameOn|Reminder|Results + Week#")
    reminder = models.BooleanField(default=False,
                                   help_text="This is a game reminder messsage.  Only players opting for reminders will get it")
    subject = models.CharField(max_length=150, blank=False)
    message = RichTextUploadingField(blank=True,
                                     help_text='Play link example: https://commonologygame.com/play-game_url_args-')
    top_components = SortedManyToManyField(
        Component, blank=True,
        help_text=f"These appear just below the header image, above the main message")
    bottom_components = SortedManyToManyField(
        Component, blank=True,
        help_text=f"These appear below the the main message")
    created = models.DateTimeField(default=timezone.now)
    scheduled = models.DateTimeField(null=True, blank=True,
                                     help_text="If set then mail will go out at the scheduled time.")
    sent_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class MailMessage(MailMessageBase):
    tested = models.BooleanField(default=False,
                                 help_text="Must be checked to send blast.  It is set when a test message is sent.")
    enable_blast = models.BooleanField(default=False,
                                       help_text="Must be check to send blast.")
    sent = models.BooleanField(default=False,
                               help_text="You can uncheck this to send blast again.")
    top_components = SortedManyToManyField(
        Component, blank=True, related_name='messages_top',
        help_text=f"These appear just below the header image, above the main message")
    bottom_components = SortedManyToManyField(
        Component, blank=True, related_name='messages_bottom',
        help_text=f"These appear below the the main message")


class MailLog(MailMessageBase):
    batch_id = models.CharField(max_length=256)
    canceled = models.DateTimeField(null=True, blank=True, default=None)
    top_components = SortedManyToManyField(
        Component, blank=True, related_name='maillog_messages_top',
        help_text=f"These appear just below the header image, above the main message")
    bottom_components = SortedManyToManyField(
        Component, blank=True, related_name='maillog_messages_bottom',
        help_text=f"These appear below the the main message")


def add_mail_log(mail_message, batch_id, canceled=None):
    kwargs = model_to_dict(mail_message, exclude=['id', 'series', 'top_components', 'bottom_components', 'enable_blast', 'sent', 'tested'])
    kwargs['batch_id'] = batch_id
    kwargs['canceled'] = canceled
    ml = MailLog.objects.create(**kwargs)
    ml.series = mail_message.series
    ml.top_components.add(*mail_message.top_components.all())
    ml.bottom_components.add(*mail_message.bottom_components.all())
    ml.save()
    return ml
