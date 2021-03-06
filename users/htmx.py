from django.http import HttpResponse
from django.views.generic.base import View
from django.contrib.auth.mixins import LoginRequiredMixin

from users.models import Player


class PlayersAPIViews(LoginRequiredMixin, View):

    def get(self, request):
        user = Player.objects.get(id=request.user.id)
        data = request.GET.dict()

        if data.get('follow'):
            to_follow = data.get('follow')
            user.following.add(id=to_follow)

        return

    def post(self, request):
        user = Player.objects.get(id=request.user.id)
        data = request.POST.dict()

        if data.get('to_follow'):
            to_follow = data.get('to_follow')
            return self._follow_unfollow(user, to_follow)

        return HttpResponse('<i class="fas fa-check-circle" style="color:#4CAF50; margin:auto;"></i>')

    def _follow_unfollow(self, user, to_follow):
        if user.following.filter(id=to_follow).exists():
            user.following.remove(to_follow)
            resp = '<i class="far fa-circle" style="color:dimgrey; margin:auto;"></i>'
        else:
            user.following.add(to_follow)
            resp = '<i class="fas fa-check-circle" style="color:#4CAF50; margin:auto;"></i>'
        user.save()
        return HttpResponse(resp)