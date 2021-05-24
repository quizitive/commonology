from django.shortcuts import render
from django.views.generic.base import View
from django.http import Http404
from django.contrib import messages
from django.db.models import Max
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

from game.models import Game, Series, Question, Answer, AnswerCode
from users.models import Player
from leaderboard.leaderboard import build_answer_tally, player_rank_and_percentile_in_game


class SeriesPermissionMixin(UserPassesTestMixin):
    """
    A mixin to validate that a user can access series assets.
    Will return true for players of that series or for any public series.
    """

    slug = 'commonology'

    def dispatch(self, request, *args, **kwargs):
        self.slug = self.kwargs.get('slug') or self.slug
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        if self.request.user.is_staff:
            return True
        series = Series.objects.get(slug=self.slug)
        if series.public:
            return True
        return series.players.filter(id=self.request.user.id).exists()


class SeriesPermissionView(SeriesPermissionMixin, View):
    game_id = None

    # these preserve the original request and are used for top level url handling
    # in order to preserve commonologygame.com/leaderboard/ for the main game
    requested_slug = None
    requested_game_id = None

    def dispatch(self, request, *args, **kwargs):
        self.requested_slug = kwargs.get('series_slug')
        self.slug = self.requested_slug or self.slug
        if self.slug:
            try:
                Series.objects.get(slug=self.slug)
            except Series.DoesNotExist:
                raise Http404()

        # todo: maybe change this to is_authenticated to allow access to historical leaderboards
        self.game_id = self.requested_game_id = kwargs.get('game_id')
        if self.game_id is not None and not request.user.is_staff:
            raise Http404()

        # if no id is specified get the most recent published game for this series
        if not self.game_id:
            self.game_id = Game.objects.filter(
                publish=True, series__slug=self.slug).aggregate(Max('game_id'))['game_id__max']

        return super().dispatch(request, *args, **kwargs)

    def get_context(self, game):
        date_range = game.date_range_pretty
        context = {
            'game_id': game.game_id,
            'game_name': game.name,
            'date_range': date_range,
            'series_slug': self.requested_slug,
            'requested_game_id': self.requested_game_id,
        }
        return context


class LeaderboardView(SeriesPermissionView):

    def get(self, request, *args, **kwargs):
        try:
            game = Game.objects.get(game_id=self.game_id)
        except Game.DoesNotExist:
            raise Http404("Game does not exist")

        context = self.get_context(game)

        messages.info(request, "Login to follow your friends and join the conversation!")
        return render(request, 'leaderboard/leaderboard_view.html', context)


class ResultsView(SeriesPermissionView):

    def get(self, request, *args, **kwargs):
        try:
            game = Game.objects.get(game_id=self.game_id)
        except Game.DoesNotExist:
            raise Http404("Game does not exist")

        answer_tally = build_answer_tally(game)
        context = self.get_context(game)
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
            'host': game.hosts.first()
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
