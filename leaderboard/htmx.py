from django.shortcuts import render
from django.views.generic.base import View
from django.http import Http404
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import get_user_model

from game.models import Game
from leaderboard.views import SeriesPermissionMixin
from leaderboard.leaderboard import build_answer_tally, build_filtered_leaderboard


class LeaderboardHTMXView(SeriesPermissionMixin, View):

    game_id = None
    game = None

    def dispatch(self, request, *args, **kwargs):
        try:
            self.game_id = int(request.GET.get('game_id', None))
            self.slug = request.GET.get('series', None) or self.slug
        except TypeError:
            raise Http404

        try:
            self.game = Game.objects.get(game_id=self.game_id, series__slug=self.slug)
        except Game.DoesNotExist:
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        if self.request.user.is_staff:
            return True
        if not self.game.publish:
            return False

        # used while we're only showing most recent game
        if self.game_id != max(self.game.series.games.filter(publish=True).values_list('game_id', flat=True)):
            return False

        # super() will test if the user has access to this series
        return super().test_func()

    def get(self, request, *args, **kwargs):
        """
        Accepts a query params following
        """
        user_following = {}
        if request.user.is_authenticated:
            User = get_user_model()
            user = User.objects.get(id=request.user.id)
            user_following = {
                p: True
                for p in user.following.values_list('id', flat=True)
            }

        try:
            current_game = Game.objects.get(game_id=self.game_id, series=self.game.series)
        except Game.DoesNotExist:
            raise Http404("Game does not exist")

        answer_tally = build_answer_tally(current_game)

        # leaderboard filters
        search_term = request.GET.get('q')
        team_id = request.GET.get('team')
        player_ids = None
        follow_filter = request.GET.get('following', False)
        if follow_filter:
            player_ids = user_following

        leaderboard = build_filtered_leaderboard(
            current_game, answer_tally, player_ids, search_term, team_id)

        try:
            total_players = current_game.players.count()
        except AttributeError:
            # a game has no questions or answers yet
            total_players = 0

        visible_players = min(len(leaderboard), total_players)
        # todo: paginate results and restrict functionality to logged in users
        leaderboard = leaderboard.to_dict(orient='records')

        context = {
            'game_id': self.game_id,
            'leaderboard': leaderboard,
            'search_term': search_term,
            'user_following': user_following,
            'follow_filter': follow_filter,
            'visible_players': visible_players,
            'total_players': total_players
        }

        return render(request, 'leaderboard/components/leaderboard.html', context)
