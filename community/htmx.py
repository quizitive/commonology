from django.views import View
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from community.models import Thread, Comment


class ThreadHTMXView(UserPassesTestMixin, View):

    thread = None
    player = None

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse("You need to sign in to access this feature", status=401)

        self.thread = Thread.objects.get(id=int(request.GET.get('thread_id')))
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
