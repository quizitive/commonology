from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils import timezone
from django.conf import settings


class MailMessage(models.Model):
    from_name = models.CharField(max_length=150, blank=False, default=settings.ALEX_FROM_NAME)
    from_email = models.EmailField('from email address', default=settings.ALEX_FROM_EMAIL)
    test_recipient = models.EmailField('test recipient email address')
    categories = models.CharField(max_length=50, blank=True,
                                  help_text="A comma separated list of categories.")
    subject = models.CharField(max_length=150, blank=False)
    message = RichTextUploadingField(blank=True)
    created = models.DateTimeField(default=timezone.now)
    tested = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
