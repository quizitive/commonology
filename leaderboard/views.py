from django.shortcuts import render
from django.views.generic.base import View
from django.http import Http404
from django.contrib import messages
from django.db.models import Max
from django.contrib.auth.mixins import LoginRequiredMixin

from game.models import Game, Question
from game.views import BaseGameView
from users.models import Player
from leaderboard.leaderboard import build_answer_tally, player_latest_game_message, \
    player_score_rank_percentile, rank_string, score_string, visible_leaderboards


class LeaderboardView(BaseGameView):

    def get_game(self):
        """Only allows staff to view historical games, sets self.game_id to published game with highest game_id"""

        # if no id is specified get the most recent published game for this series
        if not self.requested_game_id:
            game = Game.objects.filter(
                publish=True, series__slug=self.slug).order_by('-game_id').first()
        else:
            game = Game.objects.get(series__slug=self.slug, game_id=self.requested_game_id)

        # staff and hosts can view unpublished games
        if self.request.user.is_staff or self.request.user in game.hosts.all():
            return game

        # no one else can
        if not game.publish:
            return Http404()

        # anonymous users cannot view other games at all
        if self.requested_game_id is not None and not self.request.user.is_authenticated:
            raise Http404()

        # for now, limit leaderboards and results to last 10 games
        if game not in visible_leaderboards(slug=self.slug):
            raise Http404("Only the results for most recent 10 games can be viewed.")

        return game

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        if self.request.user.is_authenticated:
            # get the logged in player's stats for the game
            player_score, player_rank, player_percentile = \
                player_score_rank_percentile(self.request.user, self.game)
            context.update({
                'player_score': score_string(player_score),
                'player_rank': rank_string(player_rank),
                'player_message': player_latest_game_message(self.game, player_rank, player_percentile),
                'historical_leaderboards': visible_leaderboards(self.slug)
            })
        return context

    def get(self, request, *args, **kwargs):
        messages.info(request, "Login to follow your friends and join the conversation!")
        return render(request, 'leaderboard/leaderboard_view.html', self.get_context(*args, **kwargs))


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
            'message': player_latest_game_message(player, 'commonology', latest_game_id),
            'latest_game_id': latest_game_id,
            'games': player.game_ids,
            'teams': player.teams.all(),
            'invite_message': "Enter your friends' emails to invite them to Commonology!"
        }
        return context
