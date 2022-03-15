
from django.contrib.auth.backends import ModelBackend
from users.models import Player


class PlayerBackend(ModelBackend):

    def authenticate(self, request, **kwargs):
        if request is not None:
            user_id = request.session.get('user_id')
            try:
                return Player.objects.get(id=user_id)
            except Player.DoesNotExist:
                pass
