from django.shortcuts import render
from django.views.generic.base import View

from users.models import Player
from game.models import Game
from leaderboard.leaderboard import build_answer_tally, build_filtered_leaderboard


class LeaderboardHTMXView(View):

    def get(self, request, game_id):
        """
        Accepts a query params following
        """
        user_following = {}
        if request.user.is_authenticated:
            user = Player.objects.get(id=request.user.id)
            user_following = {
                p: True
                for p in user.following.values_list('id', flat=True)
            }

        current_game = Game.objects.get(game_id=game_id)
        date_range = current_game.date_range_pretty

        # todo: answer_tally is still a bit expensive to calculate every time
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

        leaderboard = leaderboard.to_dict(orient='records')
        context = {
            'game_id': game_id,
            'date_range': date_range,
            'leaderboard': leaderboard,
            'search_term': search_term,
            'user_following': user_following,
            'follow_filter': follow_filter,
        }

        return render(request, 'leaderboard/components/leaderboard.html', context)
