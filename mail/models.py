from django.db import models
from django_quill.fields import QuillField
from django.utils import timezone

class MassMailMessage(models.Model):
    message = QuillField()
    created = models.DateTimeField(default=timezone.now)
