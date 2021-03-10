from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.generic.base import View

from users.models import Player, Team
from game.models import Game
from leaderboard.leaderboard import build_answer_tally, build_filtered_leaderboard


class LeaderboardHTMXView(View):

    def get(self, request, game_id):
        """
        Accepts a query params following
        """
        user_following = {}
        if request.GET.get('following', False) and request.user.is_authenticated:
            user = Player.objects.get(id=request.user.id)
            user_following = {
                p: True
                for p in user.following.values_list('id', flat=True)
            }

        current_game = Game.objects.get(game_id=game_id)
        date_range = current_game.date_range_pretty

        # todo: answer_tally is still a bit expensive to calculate every time
        answer_tally = build_answer_tally(current_game)

        search_term = request.GET.get('q')
        team_id = request.GET.get('team')
        leaderboard = build_filtered_leaderboard(
            current_game, answer_tally, user_following, search_term, team_id)

        leaderboard = leaderboard.to_dict(orient='records')
        context = {
            'game_id': game_id,
            'date_range': date_range,
            'leaderboard': leaderboard,
            'search_term': search_term,
            'user_following': user_following
        }

        return render(request, 'leaderboard/components/leaderboard.html', context)
