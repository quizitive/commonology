from django.db import models
from django.utils import timezone
from users.models import Player


class Thread(models.Model):
    """ An abstraction for a list of comments and the object to which those comments belong"""

    def __str__(self):
        return f"Comment thread for {self.object.first()}"


class Comment(models.Model):
    player = models.ForeignKey(Player, related_name='comments', null=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(default=timezone.now)
    removed = models.BooleanField(default=False,
                                  help_text='This comment should be removed from the thread')
    comment = models.CharField(max_length=255)
    thread = models.ForeignKey(Thread, related_name='comments', on_delete=models.CASCADE)

    def __str__(self):
        return f"Comment from {self.player} on {self.thread}"

    def commenter(self):
        if self.player:
            return f"{self.player.display_name}"
        else:
            return "anonymous"
