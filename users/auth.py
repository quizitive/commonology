
from django.contrib.auth.backends import ModelBackend
from users.models import Player


class PlayerBackend(ModelBackend):
    # A player can be authenticated if their referrer code matches the one in their session
    # and their PendingEmail record is less than 1 hour old.
    # If a user's session is already logged in then we don't have to do this validation.

    def authenticate(self, request, **kwargs):
        user_id = request.session.get('user_id')
        try:
            return Player.objects.get(id=user_id)
        except Player.DoesNotExist:
            pass
