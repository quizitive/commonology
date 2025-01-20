import datetime
import dateutil

from django.shortcuts import render
from django.http import Http404, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe

from project.utils import our_now, slackit
from project.views import next_game_context

from game.models import Game, Question, Series
from game.views import BaseGameView
from game.utils import n_new_comments
from users.models import Player
from leaderboard.leaderboard import (
    build_answer_tally,
    player_leaderboard_message,
    player_score_rank_percentile,
    rank_string,
    score_string,
    visible_leaderboards,
)
from leaderboard.tasks import save_last_visit_t
from leaderboard.models import PlayerRankScore


class LeaderboardView(BaseGameView):

    def get_game(self):
        """Only allows staff to view historical games, sets self.game_id to published game with highest game_id"""

        # if no id is specified get the most recent published game for this series
        if not self.requested_game_id:
            game = (
                Game.objects.filter(leaderboard__publish_date__lte=our_now(), series__slug=self.slug)
                .order_by("-game_id")
                .first()
            )
        else:
            game = Game.objects.get(series__slug=self.slug, game_id=self.requested_game_id)

        if game is None:
            return None

        # staff and hosts can view unpublished games
        if self.request.user.is_staff or self.request.user in game.hosts.all():
            return game

        # no one else can
        if not game.has_leaderboard or not game.leaderboard.publish:
            raise Http404()

        # for now, limit leaderboards and results to last 10 games
        if game.leaderboard not in visible_leaderboards(slug=self.slug):
            raise Http404("Only the results for most recent 10 games can be viewed.")

        return game

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context["historical_leaderboards"] = visible_leaderboards(self.slug)
        request = self.request
        player = request.user

        if player.is_anonymous:
            t = None
        else:
            t = player.data.get(self._last_results_visit_key())

            if t:
                t = dateutil.parser.isoparse(t)
                t = t + datetime.timedelta(minutes=5)
        n_comments = n_new_comments(self.game, player, t)
        context["n_comments"] = n_comments

        if player.is_authenticated:
            # get the logged in player's stats for the game
            player_score, player_rank, player_percentile = player_score_rank_percentile(player, self.game)
            player_count = self.game.players_dict.count()
            context.update(
                {
                    "player_score": score_string(player_score),
                    "player_rank": player_rank or "N/A",
                    "player_percentile": score_string(player_percentile),
                    "player_count": player_count,
                    "player_message": player_leaderboard_message(self.game, player_rank, player_percentile),
                }
            )
        elif self._player_answers_from_session(request):
            # get stats from instant game in session
            player_score, player_rank, player_percentile = self._instant_game_score_rank(request)
            player_count = self.game.players_dict.count()
            player_message = (
                f"You scored {player_score} points, which ranks you "
                f"{rank_string(player_rank)} out of {player_count} live players. That's "
                f"better than {player_percentile}% of them! Join the live game to earn your spot "
                f"on the leaderboard."
            )
            context.update(
                {
                    "player_score": score_string(player_score),
                    "player_rank": player_rank or "N/A",
                    "player_message": mark_safe(player_message),
                    "player_percentile": score_string(player_percentile),
                    "player_count": player_count,
                    "is_instant": True,
                }
            )
            context.update(next_game_context())

        return context

    def _get_no_game_context(self):
        series = Series.objects.get(slug=self.slug)
        return {
            "series_slug": self.slug,
            "game_name": series.name,
            "no_games_yet": True,
        }

    def get(self, request, *args, **kwargs):

        if self.game is None:
            return render(request, "leaderboard/leaderboard_view.html", self._get_no_game_context())

        messages.info(request, "Login to follow your friends and join the conversation!")
        return render(request, "leaderboard/leaderboard_view.html", self.get_context(*args, **kwargs))

    def _last_results_visit_key(self):
        return f"results_last_visit_t:{self.slug}:{self.game.game_id}"

    def _player_answers_from_session(self, request):
        player_answers = request.session.get(f"game_{self.game.game_id}_answers", {})
        return player_answers

    def _instant_game_score_rank(self, request):
        answer_tally = build_answer_tally(self.game)
        qid_to_text = {str(q["id"]): q["text"] for q in self.game.questions.values("id", "text")}

        player_score = 0
        for qid, player_answer in self._player_answers_from_session(request).items():
            player_score += answer_tally[qid_to_text[qid]][player_answer]

        adjacent_rank = (
            PlayerRankScore.objects.filter(leaderboard__game=self.game, score__gt=player_score)
            .order_by("score")
            .first()
        )
        player_rank = adjacent_rank.rank + 1 if adjacent_rank else 1
        player_percentile = round(100 * (1 - player_rank / self.game.players_dict.count()))
        return player_score, player_rank, player_percentile


class ResultsView(LeaderboardView):

    def get(self, request, *args, **kwargs):
        game = self.get_game()
        if game is None:
            return render(request, "leaderboard/results.html", self._get_no_game_context())

        answer_tally = build_answer_tally(game)
        context = self.get_context()
        questions = (
            game.questions.exclude(type=Question.op)
            .order_by("number")
            .select_related("thread")
            .prefetch_related("thread__comments", "thread__comments__player")
        )

        if request.user.is_authenticated:
            player = request.user
            player_answers = self.game.leaderboard.qid_answer_dict(player.id)
            save_last_visit_t(player.id, self._last_results_visit_key(), our_now().isoformat())
        else:
            player_answers = self._player_answers_from_session(request)
            messages.info(request, "Login to follow your friends and join the conversation!")

        context.update(
            {
                "answer_tally": answer_tally,
                "player_answers": player_answers,
                "questions": questions,
                "host": game.hosts.filter(email="alex@commonologygame.com").first() or game.hosts.first(),
                "visible_comments": 5,
            }
        )

        return render(request, "leaderboard/results.html", context)


class HostNoteView(LeaderboardView):

    def get(self, request, *args, **kwargs):
        if self.game is None:
            return render(request, "leaderboard/host_note.html", self._get_no_game_context())

        context = self.get_context(*args, **kwargs)
        context.update(
            {
                "game_top_commentary": self.game.leaderboard.top_commentary,
                "game_bottom_commentary": self.game.leaderboard.bottom_commentary,
            }
        )
        return render(request, "leaderboard/host_note.html", context)


@login_required
def results_share_count_view(request):
    p = Player.objects.get(id=request.user.id)
    share_type = request.GET.get("type")
    if share_type == "image/png":
        content = "results"
    elif share_type == "text/plain":
        content = "play link"
    else:
        return HttpResponse("Invalid share")

    action_param = request.GET.get("action")
    if action_param == "api":
        action, dest = "shared", "with the web api"

    elif action_param == "clipboard":
        action, dest = "copied", "to clipboard"
    else:
        return HttpResponse("Invalid share")

    msg = f"Player {p.email} with display name: {p.display_name} just {action} their {content} {dest}"
    slackit(msg)
    return HttpResponse("Thanks for sharing!")
