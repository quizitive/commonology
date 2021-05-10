from django.shortcuts import render
from django.views.generic.base import View
from django.http import Http404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.contrib.auth.mixins import UserPassesTestMixin

from game.models import Game, Series, Question
from leaderboard.leaderboard import build_answer_tally


class SeriesPermissionView(UserPassesTestMixin, View):

    slug = 'commonology'
    game_id = None

    # these preserve the original request and are used for url routing
    requested_slug = None
    requested_game_id = None

    def dispatch(self, request, *args, **kwargs):
        self.requested_slug = kwargs.get('series_slug')
        self.slug = self.requested_slug or self.slug
        if self.slug:
            try:
                Series.objects.get(slug=self.slug)
            except Series.DoesNotExist:
                raise Http404()

        # todo: maybe change this to is_authenticated to allow access to historical leaderboards
        self.game_id = self.requested_game_id = kwargs.get('game_id')
        if self.game_id is not None and not request.user.is_staff:
            raise Http404()

        # if no id is specified get the most recent published game for this series
        if not self.game_id:
            self.game_id = Game.objects.filter(
                publish=True, series__slug=self.slug).aggregate(Max('game_id'))['game_id__max']

        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        if self.request.user.is_staff:
            return True
        series = Series.objects.get(slug=self.slug)
        if series.public:
            return True
        return series.players.filter(id=self.request.user.id).exists()

    def get_context(self, game):
        date_range = game.date_range_pretty
        context = {
            'game_id': game.game_id,
            'game_name': game.name,
            'date_range': date_range,
            'series_slug': self.requested_slug,
            'requested_game_id': self.requested_game_id,
        }
        return context


class LeaderboardView(SeriesPermissionView):

    def get(self, request, *args, **kwargs):
        try:
            game = Game.objects.get(game_id=self.game_id)
        except Game.DoesNotExist:
            raise Http404("Game does not exist")

        context = self.get_context(game)

        messages.info(request, "Login to follow your friends and much more coming soon!")
        return render(request, 'leaderboard/leaderboard_view.html', context)


class ResultsView(SeriesPermissionView):

    def get(self, request, *args, **kwargs):
        try:
            game = Game.objects.get(game_id=self.game_id)
        except Game.DoesNotExist:
            raise Http404("Game does not exist")

        answer_tally = build_answer_tally(game)
        context = self.get_context(game)

        context.update({
            'answer_tally': answer_tally,
            'game_top_commentary': game.top_commentary,
            'game_bottom_commentary': game.bottom_commentary,
            'questions': game.questions.exclude(type=Question.op).order_by('number'),
            'host': game.hosts.first()
        })
        return render(request, 'leaderboard/results.html', context)
