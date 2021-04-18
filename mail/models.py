from django.db import models
from ckeditor.fields import RichTextField
from django.utils import timezone

class MassMailMessage(models.Model):
    message = RichTextField(blank=True)
    created = models.DateTimeField(default=timezone.now)
