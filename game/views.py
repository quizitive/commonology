import gspread
import logging

from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.base import View
from project.views import CardFormView
from game.forms import TabulatorForm
from game.models import Game, Series
from game.gsheets_api import api_data_to_df, write_all_to_gdrive
from game.rollups import get_user_rollups, build_rollups_dict, build_answer_codes
from game.tasks import api_to_db
from game.utils import find_latest_public_game
from leaderboard.leaderboard import build_leaderboard_fromdb, build_answer_tally_fromdb
from users.models import PendingEmail, Player
from users.forms import PendingEmailForm
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


# Ex. https://docs.google.com/forms/d/e/1FAIpQLSeGWLWt4VJ0-Pb9aGhEU9jukstTsGy97vlKgSVHykmLJB3jow/viewform?usp=pp_url&entry.1135425595=alex@commonologygame.com
def game_url(google_form_url, email):
    return google_form_url.replace('alex@commonologygame.com', email)


def send_confirm(request, g, email):
    remove_pending_email_invitations()
    pe = PendingEmail(email=email)
    pe.save()

    slug = g.series.slug
    game_uuid = g.uuid

    domain = get_current_site(request)
    url = (f'https://{domain}/c/{slug}/play/{game_uuid}/{pe.uuid}')

    msg = render_to_string('game/validate_email.html', {'join_url': url})

    return sendgrid_send("Let's play Commonology", msg, [(email, None)])


def render_game(request, game, user=None):
    slug = game.series.slug

    if user:
        request.session['user_id'] = user.id
    else:
        user = request.user

    if not user.series.filter(slug=slug).exists():
        series = Series.objects.filter(slug=slug).first()
        series.players.add(user)
    return HttpResponse(f'stub function that would render {game.name} for {user}')


class GameEntryView(CardFormView):
    form_class = PendingEmailForm
    header = "Game starts here!"
    button_label = "Next"
    custom_message = "Enter your email to play the game so we can send the results to you."

    def message(self, request, msg):
        self.custom_message = msg
        return self.render(request, form=None, button_label='Home',
                           form_method="get", form_action='/')

    def leaderboard(self, request, msg='Seems like the game finished.  See the leaderboard.', slug='commonology'):
        self.custom_message = msg
        return self.render(request, form=None, button_label='Leaderboard',
                           form_method="get", form_action=f'/c/{slug}/leaderboard/')

    def join(self, request, msg):
        self.custom_message = msg
        return self.render(request, form=None, button_label='Join',
                           form_method="get", form_action='/join/')

    def get(self, request, *args, **kwargs):
        slug = kwargs.get('series_slug') or 'commonology'
        game_uuid = kwargs.get('game_uuid')
        user = request.user

        if not game_uuid:
            g = find_latest_public_game(slug)
        else:
            g = Game.objects.filter(uuid=game_uuid).first()

        if g is None:
            if user.is_authenticated:
                return self.message(request, 'Cannot find an active game.  We will let you know when the next game begins.')
            elif game_uuid:
                return self.message(request, 'Cannot find an active game.  Perhaps you have a bad link.')
            else:
                return self.join(request, 'Cannot find active game.  Join so we can let you know when the next game begins.')

        slug = g.series.slug

        # Backward compatibility
        if g.google_form_url:
            return redirect(g.google_form_url)

        is_active = g.is_active
        is_host = user in g.series.hosts.all()

        if is_host:
            # May be a host previewing a game
            return render_game(request, g)

        if not is_active and g.publish:
            return self.leaderboard(request, slug=slug)

        if g.user_played(user):
            return self.message(request, 'You played already.  Your answers have been emailed to you.')

        if not is_active:
            return self.message(request, msg='Seems like the game finished but has not been scored yet.')

        if user.is_authenticated:
            return render_game(request, g)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # The get method already determined that:
        #    1. There is an active game for the given slug
        #    2. The player is not logged in
        #    3. The player is not the host

        if 'email' not in request.POST:
            return redirect('home')

        game_uuid = kwargs.get('game_uuid')

        if game_uuid:
            g = Game.objects.filter(uuid=game_uuid).first()
        else:
            slug = kwargs.get('series_slug') or 'commonology'
            g = find_latest_public_game(slug)

        if g is None:
            return self.message(request, 'Cannot find game.  Perhaps you have a bad link.')

        email = request.POST['email']

        send_confirm(request, g, email)
        self.custom_message = f"We sent the game link to {email}. " \
                              f"Don't forget to check your spam or junk folder if need be. " \
                              f"By the way, if you were logged in you'd be playing already."

        self.header = "Game link sent!"
        return self.render(request, form=None, button_label='OK')


class GameEntryValidationView(CardFormView):
    form_class = PendingEmailForm
    header = "Email validated here!"
    button_label = "Next"
    custom_message = ''

    def message(self, request, msg):
        self.custom_message = msg
        return self.render(request, form=None, button_label='Home',
                           form_method="get", form_action='/')

    # c/<slug>/play/<game_uuid>/<pending_uuid>
    def get(self, request, *args, **kwargs):
        game_uuid = kwargs['game_uuid']
        pending_uuid = kwargs['pending_uuid']

        g = Game.objects.filter(uuid=game_uuid).first()
        if not g:
            return self.warning(request, 'That game does not exist.  Perhaps you are using the wrong link.', keep_form=False)

        if not g.is_active:
            # This should rarely happy because GameEntryView.get() confirmed there is an active game.
            # However, someone could try to use a confirm link too late.
            return self.warning(request, 'Sorry the next game is no longer active.', keep_form=False)

        if request.user.is_authenticated:
            return render_game(request, g)

        pe = PendingEmail.objects.filter(uuid__exact=pending_uuid).first()
        if pe is None:
            return self.message(request, 'Seems like there was a problem with the validation link. Please try again.')

        email = pe.email
        try:
            p = Player.objects.get(email=email)
            if not p.is_active:
                p.is_active = True
                p.save()
        except Player.DoesNotExist:
            p = Player(email=email)
            p.save()

        return render_game(request, g, p)
