from django.shortcuts import render
from django.http import Http404
from django.contrib import messages


from game.models import Game, Question
from game.views import BaseGameView
from leaderboard.leaderboard import build_answer_tally


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
