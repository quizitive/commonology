from asgiref.sync import sync_to_async
from celery import shared_task

from django.views import View
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from project.utils import REDIS
from game.models import Game
from leaderboard.views import SeriesPermissionMixin
from community.models import Thread, Comment

from time import sleep


class ThreadHTMXView(SeriesPermissionMixin, View):

    thread = None
    player = None

    def get(self, request, *args, **kwargs):
        self.thread = Thread.objects.get(id=int(request.GET.get('thread_id')))
        # return render(request, 'community/components/thread.html', {'thread': self.thread})
        return HttpResponse("foo")

    def post(self, request, *args, **kwargs):
        # we're not using @login_required for HTMX views so we can return a
        # 401 error in order to handle in the view based on this error code
        # see
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
        # set the html for the thread in redis,
        comment_seq_num = f'{self.thread.comments.count()}'.zfill(7)
        REDIS.set(
            f'thread_{self.thread.id}_{comment_seq_num}',
            render_to_string('community/components/comment_thread.html', {'thread': self.thread}, request)
        )
        resp = f'<textarea id="text_{self.thread.id}" name="comment" class="comment-text" ' \
               f'placeholder="Add comment..."></textarea>'
        return HttpResponse(resp)


# @sync_to_async
def comment_stream(request):

    def _get_comments():
        game = Game.objects.get(game_id=request.GET.get('game_id'))
        thread_ids = game.questions.values_list('thread_id', flat=True)
        threads_last_comment = {t: None for t in thread_ids}  # seed dict with no last comment seq num
        while True:
            for tid, lc in threads_last_comment.items():
                keys = sorted(REDIS.keys(f'thread_{tid}_*'))
                if not keys:
                    continue
                if lc == keys[-1]:
                    continue
                threads_last_comment[tid] = keys[-1]  # update the dictionary
                event_data = f"event: thread_{tid}\n"
                comment_html = "data: " + REDIS.get(threads_last_comment[tid]).replace('\n', '') + "\n\n"
                yield event_data + comment_html
            sleep(0.1)

    return StreamingHttpResponse(_get_comments(), content_type='text/event-stream')
