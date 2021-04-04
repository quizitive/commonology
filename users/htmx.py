from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.views.generic.base import View

from users.models import PendingEmail

from .utils import remove_pending_email_invitations, send_invite

User = get_user_model()


class PlayersHTMXView(View):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You need to sign in to access this feature")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        user = User.objects.get(id=request.user.id)
        data = request.POST.dict()

        if data.get('to_follow'):
            to_follow = data.get('to_follow')
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


class InviteFriendsHTMXView(View):

    def post(self, request, *args, **kwargs):
        data = request.POST.dict()
        emails = data.get('email')
        responses = []
        for email in emails:
            try:
                User.objects.get(email=email)
                # can't join if user exists
                responses.append(HttpResponse(f"User {email} already exists", status_code=409))
            except (User.DoesNotExist):
                remove_pending_email_invitations()
                pe = PendingEmail(email=email, referrer=request.user.email)
                pe.save()
                send_invite(request, pe)
                responses.append(HttpResponse(f"Invite successfully sent to {email}."))

        return JsonResponse({'responses': responses})
