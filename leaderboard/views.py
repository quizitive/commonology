from django.shortcuts import render
from django.views.generic.base import View
from django.http import Http404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.contrib.auth.mixins import UserPassesTestMixin

from game.models import Game, Series
from leaderboard.leaderboard import build_answer_tally


class SeriesPermissionView(UserPassesTestMixin, View):

    def test_func(self):
        ss = self.kwargs.get('series_slug') or "commonology"
        try:
            series = Series.objects.get(slug=ss)
        except Series.DoesNotExist:
            return False
        if series.public:
            return True
        return series.players.filter(id=self.request.user.id).exists()


class LeaderboardView(SeriesPermissionView):

    def dispatch(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')
        # todo: maybe change this to is_authenticated to allow access to historical leaderboards
        if game_id is not None and not request.user.is_staff:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, game_id=None, series_slug=None):
        if not game_id:
            # default to most recent game
            game_id = Game.objects.filter(publish=True).aggregate(Max('game_id'))['game_id__max']
        current_game = Game.objects.get(game_id=game_id)
        date_range = current_game.date_range_pretty
        context = {
            'game_id': game_id,
            'date_range': date_range
        }
        messages.info(request, "Login to follow your friends and much more coming soon!")
        return render(request, 'leaderboard/leaderboard_view.html', context)


class ResultsView(SeriesPermissionView):

    def get(self, request, game_id):
        try:
            game = Game.objects.get(game_id=game_id)
        except Game.DoesNotExist:
            raise Http404("Game does not exist")

        if not game.publish and not request.user.is_staff:
            raise PermissionDenied("Results for this game have not yet been published!")

        answer_tally = build_answer_tally(game)

        context = {
            # 'player': request.user.player.display_name,
            'game_id': game_id,
            'date_range': game.date_range_pretty,
            'answer_tally': answer_tally
        }
        return render(request, 'leaderboard/results.html', context)
