import gspread
import logging
import os
from time import sleep
import datetime

from django.shortcuts import render
from django.views.generic.base import View
from django.http import Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.core.mail import send_mail

from game.forms import TabulatorForm
from game.models import Game, Team, Player
from game.utils import next_event
from game.leaderboard import build_filtered_leaderboard, build_answer_tally, player_rank_and_percentile_in_game
from game.gsheets_api import api_data_to_df, write_all_to_gdrive
from game.rollups import get_user_rollups, build_rollups_dict, build_answer_codes
from game.tasks import api_to_db, add


def index(request):
    event_text, event_time = next_event()
    context = {
        'event_time': event_time,
        'event_text': event_text
    }
    return render(request, 'game/index.html', context)


@permission_required('is_superuser')
def marc(request):
    m = os.environ.get('MARC', 'Ted')

    result = add.delay(3, 5)
    sleep(3)

    x = [i[1] for i in result.collect()][0]
    if 0 == x:
        x = "0 because the env var MARC was not defined for Celery."
    x = {'MARC': m, 'SumResult': x}

    return render(request, 'game/marc.html', x)


@permission_required('is_superuser')
def ted(request):
    return render(request, 'game/ted.html', {})


@login_required
@permission_required('is_superuser')
def mailtest(request):
    emailaddr = request.user.email
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Mail sent to {emailaddr} at {now}."

    send_mail(subject="Sending test.", message=message,
              from_email=None, recipient_list=[emailaddr])

    return render(request, 'game/mailtest.html',
                  {'message': message, "emailaddr": emailaddr})


@staff_member_required
def tabulator_form_view(request):
    context = {
        'fn': '',
        'msg': ''
    }
    form = TabulatorForm()
    if request.method == "POST":

        fn = request.POST.get('sheet_name')
        context['fn'] = fn
        form.fields['sheet_name'].initial = fn
        gc = gspread.service_account()
        update = request.POST.get('update_existing') == 'on'

        try:
            tabulate_results(fn, gc, update)
            context['msg'] = "The results have been updated, feel free to submit again."
        except gspread.exceptions.SpreadsheetNotFound:
            context['msg'] = "The Google Sheet entered does not exist, no changes were made"
        except gspread.exceptions.WorksheetNotFound:
            context['msg'] = "A tab was not found in the Google Sheet. Were the tabs renamed?"
        except Exception as e:
            context['msg'] = "An unexpected error occurred. Ping Ted."
            logging.error("Exception occurred", exc_info=True)

    context['form'] = form
    return render(request, 'game/tabulator_form.html', context)


def tabulate_results(filename, gc, update=False):
    """
    Reads from, tabulates, and prints output to the named Google Sheet
    :param filename: The name of the spreadsheet in Google Drive
    :param gc: An authenticated instance of gspread
    :param update: Whether or not to update existing answer records in the DB
    :return: None
    """
    sheet_doc = gc.open(filename)
    raw_data = sheet_doc.values_get(range='Form Responses 1').get('values')
    responses = api_data_to_df(raw_data)

    user_rollups = get_user_rollups(sheet_doc)
    rollups_dict = build_rollups_dict(user_rollups)
    answer_codes = build_answer_codes(responses, rollups_dict)

    # write to database
    api_to_db(
        filename,
        responses.to_json(),
        answer_codes,
        update
    )

    # calculate the question-by-question data and leaderboard
    game = Game.objects.get(sheet_name=filename)
    answer_tally = build_answer_tally(game)
    leaderboard = build_filtered_leaderboard(game, answer_tally)

    # write to google
    write_all_to_gdrive(sheet_doc, answer_tally, answer_codes, leaderboard)


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
        'team': team
    }

    return render(request, 'game/leaderboard.html', context)


class DashboardView(LoginRequiredMixin, View):

    template = 'game/dashboard.html'

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
        player, _ = Player.objects.get_or_create(user=user)
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
        return render(request, 'game/results.html', context)
