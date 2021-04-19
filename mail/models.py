from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils import timezone


class MassMailMessage(models.Model):
    test_recipient = models.EmailField('test recipient email address')
    subject = models.CharField(max_length=150, blank=False)
    message = RichTextUploadingField(blank=True)
    created = models.DateTimeField(default=timezone.now)
    sent = models.BooleanField(default=False)
