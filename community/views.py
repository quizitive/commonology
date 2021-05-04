from django.shortcuts import render
from django.views.generic.base import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Max
from django.http import Http404, HttpResponse

from django.contrib.auth import get_user_model
from game.models import Game, Series

from leaderboard.leaderboard import player_rank_and_percentile_in_game
from leaderboard.views import LeaderboardView


class PlayerHomeView(LoginRequiredMixin, View):

    template = 'community/player_home.html'

    def get(self, request):
        context = self._get_context(request)
        return render(request, self.template, context)

    def post(self, request):
        emails = [e.strip() for e in request.POST.get("invite").split(",")]
        context = self._get_context(request)
        context['invite_message'] = "Your invites have been sent! Feel free to enter more below."
        return render(request, self.template, context)

    def _get_context(self, request):
        user = request.user
        User = get_user_model()
        player, _ = User.objects.get_or_create(id=user.id)
        games = Game.objects.filter(publish=True).order_by('-game_id')
        latest_game_id = games.aggregate(Max('game_id'))['game_id__max']

        context = {
            'display_name': user.first_name or user.email,
            'message': self._dashboard_message(player, latest_game_id),
            'latest_game_id': latest_game_id,
            'games': player.games,
            'teams': player.teams.all(),
            'invite_message': "Enter your friends' emails to invite them to Commonology!"
        }
        return context

    @staticmethod
    def _dashboard_message(player, latest_game_id):

        if latest_game_id not in player.games.values_list('game_id', flat=True):
            return "Looks like you missed last weeks game... You'll get 'em this week!"

        latest_rank, percentile = player_rank_and_percentile_in_game(player.id, latest_game_id)
        player_count = Game.objects.get(game_id=latest_game_id).players.count()

        follow_up = "This is gonna be your week!"
        if percentile <= 0.1:
            follow_up = "That puts you in the top 10%!"
        elif percentile <= 0.25:
            follow_up = "That puts you in the top 25%!"
        elif percentile <= 0.5:
            follow_up = "That puts you in the top half!"

        return f"Last week you ranked {latest_rank} out of {player_count} players. {follow_up}"
