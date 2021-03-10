import os

from django.shortcuts import render
from django.views.generic.base import View
from django.http import Http404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Max

from users.models import Player, Team
from game.models import Game
from leaderboard.leaderboard import build_filtered_leaderboard, build_answer_tally


@login_required
def loggedin_leaderboard_view(request):
    return _render_leaderboard(request)


@login_required
def game_leaderboard_view(request, game_id):
    return _render_leaderboard(request, game_id, False)


def uuid_leaderboard_view(request, uuid):
    if uuid != os.environ.get('LEADERBOARD_UUID'):
        raise Http404("Page does not exist")
    return _render_leaderboard(request)


def _render_leaderboard(request, game_id=None, published=True):
    user_following = {}
    if request.user.is_authenticated:
        user = Player.objects.get(id=request.user.id)
        user_following = {
            p: True
            for p in user.following.values_list('id', flat=True)
        }

    if published:
        games = Game.objects.filter(publish=True).order_by('-game_id')
    else:
        games = Game.objects.order_by('-game_id')

    # default to most recent game
    if not game_id:
        game_id = games.aggregate(Max('game_id'))['game_id__max']

    current_game = games.get(game_id=game_id)
    date_range = current_game.date_range_pretty
    teams = current_game.teams
    answer_tally = build_answer_tally(current_game)
    search_term = request.GET.get('q')
    team_id = request.GET.get('team')
    leaderboard = build_filtered_leaderboard(current_game, answer_tally, search_term, team_id)
    team = Team.objects.filter(id=team_id).first() or None

    leaderboard = leaderboard.to_dict(orient='records')
    context = {
        'game_id': game_id,
        'games': games,
        'teams': teams,
        'date_range': date_range,
        'leaderboard': leaderboard,
        'search_term': search_term,
        'team': team,
        'user_following': user_following
    }

    return render(request, 'leaderboard/leaderboard_view.html', context)


class LeaderboardView(View):

    def get(self, request, uuid):
        if uuid != os.environ.get('LEADERBOARD_UUID'):
            raise Http404("Page does not exist")
        return render(request, 'leaderboard/leaderboard_view.html', {})

    def _render_leaderboard(self, request):
        return _render_leaderboard(request)


class ResultsView(View):

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
