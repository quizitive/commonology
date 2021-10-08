from django.shortcuts import render
from django.views.generic.base import View
from django.http import Http404
from django.contrib import messages
from django.db.models import Max
from django.contrib.auth.mixins import LoginRequiredMixin

from game.models import Game, Question
from game.views import BaseGameView
from users.models import Player
from leaderboard.leaderboard import build_answer_tally, player_rank_and_percentile_in_game


class LeaderboardView(BaseGameView):

    def get_game(self):
        """Only allows staff to view historical games, sets self.game_id to published game with highest game_id"""

        # if no id is specified get the most recent published game for this series
        if not self.requested_game_id:
            game = Game.objects.filter(
                publish=True, series__slug=self.slug).order_by('-game_id').first()
        else:
            game = Game.objects.get(series__slug=self.slug, game_id=self.requested_game_id)

        # todo: maybe change this to is_authenticated to allow access to historical leaderboards
        if self.requested_game_id is not None and not (
                self.request.user.is_staff
                or self.request.user in game.hosts.all()
        ):
            raise Http404()

        return game

    def get(self, request, *args, **kwargs):
        context = self.get_context()
        messages.info(request, "Login to follow your friends and join the conversation!")
        return render(request, 'leaderboard/leaderboard_view.html', context)


class ResultsView(LeaderboardView):

    def get(self, request, *args, **kwargs):
        game = self.get_game()
        answer_tally = build_answer_tally(game)
        context = self.get_context()
        questions = game.questions.exclude(type=Question.op).order_by('number')
        player_answers = []
        if request.user.is_authenticated:
            player_answers = game.coded_player_answers.filter(player=request.user)

        context.update({
            'answer_tally': answer_tally,
            'player_answers': player_answers,
            'game_top_commentary': game.top_commentary,
            'game_bottom_commentary': game.bottom_commentary,
            'questions': questions,
            'host': game.hosts.filter(email="alex@commonologygame.com").first() or game.hosts.first(),
            'visible_comments': 5
        })
        messages.info(request, "Login to follow your friends and join the conversation!")
        return render(request, 'leaderboard/results.html', context)


class PlayerHomeView(LoginRequiredMixin, View):
    template = 'leaderboard/player_home.html'

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
        player, _ = Player.objects.get_or_create(id=user.id)
        # todo: hardcoding commonology as series for now for now
        games = Game.objects.filter(publish=True, series__slug='commonology').order_by('-game_id')
        latest_game_id = games.aggregate(Max('game_id'))['game_id__max']

        context = {
            'display_name': user.first_name or user.email,
            'message': self._dashboard_message(player, 'commonology', latest_game_id),
            'latest_game_id': latest_game_id,
            'games': player.game_ids,
            'teams': player.teams.all(),
            'invite_message': "Enter your friends' emails to invite them to Commonology!"
        }
        return context

    @staticmethod
    def _dashboard_message(player, series_slug, latest_game_id):

        if latest_game_id not in player.game_ids.values_list('game_id', flat=True):
            return "Looks like you missed last weeks game... You'll get 'em this week!"

        latest_rank, percentile = player_rank_and_percentile_in_game(player.id, latest_game_id)
        player_count = Game.objects.get(game_id=latest_game_id, series__slug=series_slug).players_dict.count()

        follow_up = "This is gonna be your week!"
        if percentile <= 0.1:
            follow_up = "That puts you in the top 10%!"
        elif percentile <= 0.25:
            follow_up = "That puts you in the top 25%!"
        elif percentile <= 0.5:
            follow_up = "That puts you in the top half!"

        return f"Last week you ranked {latest_rank} out of {player_count} players. {follow_up}"
