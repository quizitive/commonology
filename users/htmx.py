from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.views.generic.base import View

from users.models import Player


class PlayersHTMXView(View):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # todo: this can return a nice modal to prompt sign in, make a base class
            raise PermissionDenied("You need to sign in to access this feature")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        user = Player.objects.get(id=request.user.id)
        data = request.POST.dict()

        if data.get('to_follow'):
            to_follow = data.get('to_follow')
            return self._follow_unfollow(user, to_follow)

        return HttpResponse('<i class="fas fa-check-circle" style="color:#4CAF50; margin:auto;"></i>')

    @staticmethod
    def _follow_unfollow(user, to_follow):
        if user.following.filter(id=to_follow).exists():
            user.following.remove(to_follow)
            resp = '<i class="far fa-circle" style="color:dimgrey; margin:auto;"></i>'
        else:
            user.following.add(to_follow)
            resp = '<i class="fas fa-check-circle" style="color:#4CAF50; margin:auto;"></i>'
        user.save()
        return HttpResponse(resp)
