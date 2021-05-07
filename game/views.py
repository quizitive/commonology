import gspread
import logging

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from game.forms import TabulatorForm
from game.models import Game
from game.utils import next_event
from leaderboard.leaderboard import build_filtered_leaderboard, build_answer_tally
from game.gsheets_api import api_data_to_df, write_all_to_gdrive
from game.rollups import get_user_rollups, build_rollups_dict, build_answer_codes
from game.tasks import api_to_db


def index(request):
    if request.user.is_authenticated:
        return redirect('leaderboard:current-leaderboard')
    event_text, event_time = next_event()
    context = {
        'event_time': event_time,
        'event_text': event_text
    }
    return render(request, 'game/index.html', context)


def about_view(request):
    return render(request, 'game/about.html', {})


@staff_member_required
def tabulator_form_view(request):
    context = {
        'fn': '',
        'msg': ''
    }
    form = TabulatorForm(list(request.user.hosted_series.values_list('slug', 'name')))
    if request.method == "POST":

        series = request.POST.get('series')
        fn = request.POST.get('sheet_name')
        context['fn'] = fn
        form.fields['sheet_name'].initial = fn
        gc = gspread.service_account(settings.GOOGLE_GSPREAD_API_CONFIG)
        update = request.POST.get('update_existing') == 'on'

        try:
            tabulate_results(series, fn, gc, update)
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


def tabulate_results(series_slug, filename, gc, update=False):
    """
    Reads from, tabulates, and prints output to the named Google Sheet
    :param series_slug: The slug of the series to which this game belongs
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
        series_slug,
        filename,
        responses.to_json(),
        answer_codes,
        update
    )

    # calculate the question-by-question data and leaderboard
    game = Game.objects.get(sheet_name=filename, series__slug=series_slug)
    answer_tally = build_answer_tally(game)
    leaderboard = build_filtered_leaderboard(game, answer_tally)

    # write to google
    write_all_to_gdrive(sheet_doc, answer_tally, answer_codes, leaderboard)
