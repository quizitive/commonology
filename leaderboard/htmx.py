from django.shortcuts import render
from django.views.generic.base import View
from django.db.models import Max
from django.http import Http404

from django.contrib.auth import get_user_model
from game.models import Game
from leaderboard.leaderboard import build_answer_tally, build_filtered_leaderboard


class LeaderboardHTMXView(View):

    def dispatch(self, request, *args, **kwargs):
        game_id = request.GET.get('game_id', False)
        # return most recent game for any non-staff requests, or requests with not game_id
        if not request.user.is_staff or not game_id:
            kwargs['game_id'] = Game.objects.filter(publish=True).aggregate(Max('game_id'))['game_id__max']
        else:
            kwargs['game_id'] = game_id
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, game_id):
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
            current_game = Game.objects.get(game_id=game_id)
        except Game.DoesNotExist:
            raise Http404("Game does not exist")

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

        try:
            total_players = current_game.players.count()
        except AttributeError:
            # a game has no questions or answers yet
            total_players = 0

        visible_players = min(len(leaderboard), total_players)
        # todo: paginate results and restrict functionality to logged in users
        leaderboard = leaderboard.to_dict(orient='records')

        context = {
            'game_id': game_id,
            'leaderboard': leaderboard,
            'search_term': search_term,
            'user_following': user_following,
            'follow_filter': follow_filter,
            'visible_players': visible_players,
            'total_players': total_players
        }

        return render(request, 'leaderboard/components/leaderboard.html', context)
