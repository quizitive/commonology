import gspread
import logging

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.base import View
from project.views import CardFormView
from project.utils import our_now
from game.forms import TabulatorForm, QuestionAnswerForm
from game.models import Game
from leaderboard.leaderboard import build_leaderboard_fromdb, build_answer_tally_fromdb
from game.gsheets_api import api_data_to_df, write_all_to_gdrive
from game.rollups import get_user_rollups, build_rollups_dict, build_answer_codes
from game.tasks import api_to_db
from users.models import PendingEmail, Player
from users.forms import PendingEmailForm
from users.utils import is_validated
from users.views import remove_pending_email_invitations
from mail.sendgrid_utils import sendgrid_send


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
    # NOTE: both of these call the method that rebuilds themself from db and clears the cache
    game = Game.objects.get(sheet_name=filename, series__slug=series_slug)
    answer_tally = build_answer_tally_fromdb(game)
    leaderboard = build_leaderboard_fromdb(game, answer_tally)

    # write to google
    write_all_to_gdrive(sheet_doc, answer_tally, answer_codes, leaderboard)


def find_latest_active_game(slug):
    t = our_now()
    g = Game.objects.filter(series__slug=slug, end__gte=t, start__lte=t).reverse().first()
    if g and not g.google_form_url:
        return None
    return g


# Ex. https://docs.google.com/forms/d/e/1FAIpQLSeGWLWt4VJ0-Pb9aGhEU9jukstTsGy97vlKgSVHykmLJB3jow/viewform?usp=pp_url&entry.1135425595=alex@commonologygame.com
def game_url(google_form_url, email):
    return google_form_url.replace('alex@commonologygame.com', email)


def send_confirm(request, slug, email):
    remove_pending_email_invitations()
    pe = PendingEmail(email=email)
    pe.save()

    domain = get_current_site(request)
    url = (f'https://{domain}/c/{slug}/play/{pe.uuid}')

    msg = render_to_string('game/validate_email.html', {'join_url': url})

    return sendgrid_send("Let's play Commonology", msg, [(email, None)])


# THIS SHOULD BE TEMPORARY UNTIL WE HOST OUR OWN FORMS
# The following GameEntryView class works and should be used instead.
# See https://github.com/quizitive/commonology/issues/288
# Also enable tests.TestPlayRequest and remove tests.TestPlayRequestWithoutValidation
class GameEntryWithoutValidationView(CardFormView):
    form_class = PendingEmailForm
    header = "Game starts here!"
    button_label = "Next"

    def message(self, request, msg):
        self.custom_message = msg
        return self.render(request, form=None, button_label='Next',
                           form_method="get", form_action='/')

    def get(self, request, *args, **kwargs):
        slug = kwargs.get('series_slug') or 'commonology'

        g = find_latest_active_game(slug)
        if slug == 'commonology':
            if not g:
                return self.message(request,
                                    'Sorry the next game has not started yet.  Join our list so we can let you know when it does.')
            else:
                return redirect(g.google_form_url)

        if not g:
            return self.message(request,
                                'Sorry the next game has not started yet. You should receive an email reminder when it is ready')

        if request.user.is_anonymous:
            return self.message(request,
                                'You must be logged in to play this version of the game.')
        else:
            player = is_validated(request.user.email)

        if player and player.series.filter(slug=slug).exists():
            return redirect(g.google_form_url)

        return self.message(request,
                            'Sorry the game you requested is not available without an invitation.')


class GameEntryView(CardFormView):
    form_class = PendingEmailForm
    header = "Game starts here!"
    button_label = "Next"
    custom_message = "Enter your email to play the game so we can send the results to you."

    def get(self, request, *args, **kwargs):
        slug = kwargs.get('series_slug') or 'commonology'
        g = find_latest_active_game(slug)
        if not g:
            return self.warning(request,
                                ('Sorry the next game has not started yet.  '
                                 'Join our list so we can let you know when it does.'),
                                keep_form=False)

        if request.user.is_authenticated:
            player = is_validated(request.user.email)
            if not (slug == 'commonology' or player.series.filter(slug=slug).exists()):
                return self.warning(request, 'Sorry the game you requested is not available without an invitation.',
                                    keep_form=False)

            url = game_url(g.google_form_url, request.user.email)
            return redirect(url)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'email' not in request.POST:
            # There was no form probably game is not active.
            return redirect('home')

        slug = kwargs.get('series_slug') or 'commonology'
        email = request.POST['email']
        player = is_validated(email)

        if player and player.series.filter(slug=slug).exists():
            g = find_latest_active_game(slug)
            if not g:
                return self.warning(request, 'Sorry the next game has not started yet.', keep_form=False)
            url = game_url(g.google_form_url, email)
            return redirect(url)
        else:
            if slug == 'commonology':
                send_confirm(request, slug, email)
                self.custom_message = f"We sent the game link to {email}. " \
                                      f"Don't forget to check your spam or junk folder if need be."

                self.header = "Game link sent!"
                return self.render(request, form=None, button_label='OK')

        return self.warning(request,
                            'Sorry the game you requested is not available without an invitation.',
                            keep_form=False)


class GameEntryValidationView(View):
    # c/<slug>/play/<uuid>
    def get(self, request, *args, **kwargs):
        slug = kwargs['series_slug']
        uuid = kwargs['uidb64']
        pe = PendingEmail.objects.filter(uuid__exact=uuid).get()
        if pe is None:
            gc = GameEntryView()
            return gc.warning(request, 'Seems like there was a problem with the validation link. Please try again.')

        email = pe.email
        try:
            p = Player.objects.get(email=email)
            if not p.is_active:
                p.is_active = True
                p.save()
        except Player.DoesNotExist:
            p = Player(email=email)
            p.save()

        g = find_latest_active_game(slug)
        if not g:
            gc = GameEntryView()
            return gc.warning(request, 'Sorry the next game has not started yet.', keep_form=False)

        url = game_url(g.google_form_url, email)
        return redirect(url)


class GameFormView(View):

    def get(self, request):
        game = Game.objects.get(series__slug='commonology', game_id=44)
        context = {
            'questions': game.questions.order_by('number')
        }
        return render(request, 'game/game_form.html', context)
