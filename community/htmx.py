from django.views import View
from django.http import HttpResponse
from django.shortcuts import render

from leaderboard.views import SeriesPermissionMixin
from community.models import Thread, Comment


class ThreadHTMXView(SeriesPermissionMixin, View):

    thread = None
    player = None

    def post(self, request, *args, **kwargs):
        # we're not using @login_required for HTMX views so we can return a
        # 401 error in order to handle in the view based on this error code
        # see
        if not request.user.is_authenticated:
            return HttpResponse("You need to sign in to access this feature", status=401)

        self.thread = Thread.objects.get(id=int(request.GET.get('thread-id')))
        self.player = request.user

        req_method = request.POST.get('method')
        if not req_method:
            return HttpResponse("No method specified", status=400)

        htmx_method = getattr(self, req_method)
        return htmx_method(request)

    def add_comment(self, request):
        comment = request.POST.get('comment')
        Comment.objects.create(comment=comment, player=self.player, thread=self.thread)
        return render(request, 'community/components/thread.html', {'thread': self.thread})
