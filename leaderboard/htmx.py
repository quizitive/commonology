from functools import cached_property

from django.shortcuts import render
from django.views.generic.base import View
from django.http import Http404
from django.utils.safestring import mark_safe

from game.models import Game
from game.views import SeriesPermissionMixin
from game.utils import new_players_for_game
from leaderboard.leaderboard import build_answer_tally, build_filtered_leaderboard, \
    visible_leaderboards, winners_of_series
from users.utils import players_with_referral_badge


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
        if self.request.user.is_staff or self.request.user in self.game.hosts.all():
            return True
        if not self.game.has_leaderboard or not self.game.leaderboard.publish:
            return False

        if self.game.leaderboard not in visible_leaderboards(self.slug):
            return False

        # super() will test if the user has access to this series
        return super().test_func()

    def get(self, request, *args, **kwargs):
        """
        Accepts the following query params:
        q: a comma separated case-insensitive search term to search display names
        team: a team id (not currently being used)
        following: a boolean that filters on players the logged-in users follows
        page: pagination page, defaults to 1, page_size is 100
        """
        try:
            current_game = Game.objects.get(game_id=self.game_id, series=self.game.series)
        except Game.DoesNotExist:
            raise Http404("Game does not exist")

        answer_tally = build_answer_tally(current_game)

        # leaderboard filters
        search_term = request.GET.get('q')
        team_id = request.GET.get('team')
        id_filter = request.GET.get('id_filter')
        player_ids = self._player_ids_filter(self.game_id, id_filter)
        leaderboard = build_filtered_leaderboard(
            current_game, answer_tally, player_ids, search_term, team_id)

        try:
            total_players = current_game.players_dict.count()
        except AttributeError:
            # a game has no questions or answers yet
            total_players = 0

        try:
            page = int(request.GET.get('page'))
        except (TypeError, ValueError):
            page = 1

        lb_page_start, lb_page_end, prev_page, next_page, leaderboard, lb_message = \
            self._pagination(leaderboard, page, id_filter)

        leaderboard = leaderboard.to_dict(orient='records')

        context = {
            'game_id': self.game_id,
            'leaderboard': leaderboard,
            'search_term': search_term,
            'id_filter': id_filter,
            'winners_of_series': set(winners_of_series(self.slug)),
            'players_with_referral_badge': set(players_with_referral_badge().values_list("id", flat=True)),
            'lb_message': lb_message,
            'total_players': total_players,
            'page': page,
            'next': next_page,
            'prev': prev_page
        }

        return render(request, 'leaderboard/components/leaderboard.html', context)

    @cached_property
    def _user_and_following(self):
        if self.request.user.is_authenticated:
            user_following = {
                p: True
                for p in self.request.user.following.values_list('id', flat=True)
            }
        else:
            user_following = {}
        return self.request.user, user_following

    def _player_ids_filter(self, game_id, id_filter):
        player_id_filters = ('following', 'followers', 'new_players')
        user, user_following = self._user_and_following
        if id_filter not in player_id_filters:
            return
        if id_filter == 'following':
            return user_following
        if id_filter == 'followers':
            try:
                return user.followers.values_list('id', flat=True)
            except AttributeError:
                return []
        if id_filter == 'new_players':
            return new_players_for_game(self.slug, self.game_id)
        return []

    def _pagination(self, leaderboard, page, id_filter):
        # leaderboard pagination logic
        lb_page_start = (page - 1) * 100
        lb_page_end = min(len(leaderboard), page * 100)
        filtered_player_count = len(leaderboard)

        prev_page = page - 1 or None
        if lb_page_end >= len(leaderboard):
            next_page = None
        else:
            next_page = page + 1

        leaderboard = leaderboard[lb_page_start:lb_page_end]

        if filtered_player_count > 0:
            msg_map = {
                "following": "players that you follow.",
                "followers": "players that follow you.",
                "new_players": "first time players!"
            }
            filter_msg = msg_map.get(id_filter, "results.")
            msg = f"Showing {lb_page_start + 1}-{lb_page_end} out of {filtered_player_count} {filter_msg}"
        elif self.request.user.is_authenticated:
            msg_map = {
                "following": "Follow your friends by checking the bubble next to their name.",
                "followers": "Nobody is following you yet :( Tell you friends you're awesome!",
                "new_players": "No first time players :("
            }
            msg = msg_map.get(id_filter, f"Showing 0 out of {filtered_player_count} results.")
        else:
            msg = mark_safe(f"<a href='/login'>Login</a> or <a href='/join'>Join</a> to follow your friends!")

        return lb_page_start, lb_page_end, prev_page, next_page, leaderboard, msg
