from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth import get_user_model
from django.views.generic.base import View


class PlayersHTMXView(View):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse("You need to sign in to access this feature", status=401)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        User = get_user_model()
        user = User.objects.get(id=request.user.id)
        data = request.POST.dict()

        if data.get("to_follow"):
            to_follow = data.get("to_follow")
            return self._follow_unfollow(user, to_follow)

        return HttpResponseBadRequest("Request provided no target follower")

    @staticmethod
    def _follow_unfollow(user, to_follow):
        if user.following.filter(id=to_follow).exists():
            user.following.remove(to_follow)
        else:
            user.following.add(to_follow)
        user.save()
        return HttpResponse()
