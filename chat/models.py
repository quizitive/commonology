from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from users.models import Player


class Thread(models.Model):
    """An abstraction to relate a collection of comments to the object which they belong"""

    def __str__(self):
        return f"Comment thread for {self.object.first()}"


class Comment(models.Model):
    player = models.ForeignKey(Player, related_name="comments", null=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(default=timezone.now)
    removed = models.BooleanField(default=False, help_text="This comment should be removed from the thread")
    comment = models.CharField(max_length=255)
    thread = models.ForeignKey(Thread, related_name="comments", on_delete=models.CASCADE)

    class Meta:
        ordering = ("created",)

    def __str__(self):
        return f"Comment from {self.player} on {self.thread}"

    def commenter(self):
        if self.player:
            return f"{self.player.display_name}"
        else:
            return "anonymous"

    @property
    def clean_comment(self):
        if self.removed:
            return mark_safe("<span style='color:#aaa;font-size:12px;'>&ltThis comment has been removed&gt</span>")
        else:
            return self.comment
