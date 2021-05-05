from django.shortcuts import render
from django.views.generic.base import View
from django.http import Http404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Max

from users.models import Team
from django.contrib.auth import get_user_model
from game.models import Game
from leaderboard.leaderboard import build_filtered_leaderboard, build_answer_tally


def _render_leaderboard(request, game_id=None, published=True):
    user_following = {}
    if request.user.is_authenticated:
        User = get_user_model()
        user = User.objects.get(id=request.user.id)
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

    def dispatch(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')
        # todo: maybe change this to is_authenticated to allow access to historical leaderboards
        if game_id is not None and not request.user.is_staff:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, game_id=None):
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


class ResultsView(View):

    def dispatch(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')
        # todo: maybe change this to is_authenticated to allow access to historical leaderboards
        if game_id is not None and not request.user.is_staff:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, game_id=None):
        if not game_id:
            # default to most recent game
            game_id = Game.objects.aggregate(Max('game_id'))['game_id__max']
            game = Game.objects.get(game_id=game_id)

        if not game.publish and not request.user.is_staff:
            raise PermissionDenied("Results for this game have not yet been published!")

        answer_tally = build_answer_tally(game)

        context = {
            'game_id': game.game_id,
            'game_top_commentary': game.top_commentary,
            'game_bottom_commentary': game.bottom_commentary,
            'date_range': game.date_range_pretty,
            'questions': game.visible_questions,
            'answer_tally': answer_tally
        }
        return render(request, 'leaderboard/results.html', context)
