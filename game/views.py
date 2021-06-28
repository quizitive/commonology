import gspread
import logging
from numpy import base_repr

from django.conf import settings
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.core.signing import Signer, BadSignature
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.base import View
from django.views.generic.edit import FormMixin
from project.views import CardFormView
from game.forms import TabulatorForm, QuestionAnswerForm
from game.models import Game, Series, Answer
from game.gsheets_api import api_data_to_df, write_all_to_gdrive
from game.rollups import get_user_rollups, build_rollups_dict, build_answer_codes
from game.tasks import api_to_db
from game.utils import find_latest_active_game, find_hosted_game
from leaderboard.leaderboard import build_leaderboard_fromdb, build_answer_tally_fromdb
from users.models import PendingEmail, Player
from users.forms import PendingEmailForm
from users.utils import is_validated
from users.views import remove_pending_email_invitations
from mail.sendgrid_utils import sendgrid_send


class SeriesPermissionMixin(UserPassesTestMixin):
    """
    A mixin to validate that a user can access series assets.
    Will return true for players of that series or for any public series.
    """

    slug = 'commonology'

    def dispatch(self, request, *args, **kwargs):
        self.slug = kwargs.get('slug') or self.slug
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        if self.request.user.is_staff:
            return True
        series = Series.objects.get(slug=self.slug)
        if series.public:
            return True
        return series.players.filter(id=self.request.user.id).exists()


class BaseGameView(SeriesPermissionMixin, View):
    game = None

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

        self.requested_game_id = kwargs.get('game_id')
        self.game = self.get_game()

        return super().dispatch(request, *args, **kwargs)

    def get_game(self):
        """Implement this method to define game permission logic"""
        raise NotImplementedError

    def get_context(self, *args, **kwargs):
        date_range = self.game.date_range_pretty
        context = {
            'game_id': self.game.game_id,
            'game_name': self.game.name,
            'date_range': date_range,
            'series_slug': self.requested_slug,
            'requested_game_id': self.requested_game_id,
        }
        return context


class GameFormView(FormMixin, BaseGameView):
    signer = Signer()
    request = None
    game = None
    player = None

    def render_game(self, request, *args, **kwargs):
        # called when an validated player passes though GameEntryView
        psid = self.sign_game_player()
        self.requested_slug = self.game.series.slug
        return render(request, 'game/game_form.html', self.get_context(self.game, psid))

    def get(self, request, *args, **kwargs):
        # todo: render a player's game responses
        if (psid := kwargs.get('player_signed_id')) is None:
            raise PermissionDenied

        game, player = self.get_game_and_player(psid)

        form_data = {
            str(qid): answer
            for qid, answer in Answer.objects.filter(
                question__game=self.game,
                player=player
            ).values_list('question', 'raw_string')
        }
        forms = self.get_forms(self.game, form_data)
        context = self.get_context(self.game, None, forms)
        # todo: disable button, etc
        return render(request, 'game/game_form.html', context)

    def post(self, request, *args, **kwargs):

        # Make sure this is a real submission that hasn't been tampered with
        if (psid := self.request.POST.get('psid')) is None:
            raise PermissionDenied

        game, player = self.get_game_and_player(psid)

        if player.id in self.game.players.values_list('player', flat=True):
            header = "Game Played"
            msg = "You've already played this game! Your answers have been emailed to you."
            raise PermissionDenied

        # build a dict with the form inputs
        form_data = {
            qid: answer
            for qid, answer in
            zip(self.request.POST.getlist('question_id'), self.request.POST.getlist('raw_string'))
        }

        forms = self.get_forms(self.game, form_data)
        if any([f.errors for f in forms.values()]):
            context = self.get_context(self.game, psid, forms)
            return render(request, 'game/game_form.html', context)

        # todo: save form data
        print("success!")

        # todo: a success screen
        # todo: email answers link
        return redirect('home')

    def test_func(self):
        # override super method, we don't want to restrict access to game form for
        # new players of a series, obtaining the unique url is validation enough
        return True

    def get_game(self):
        # self.game will be set if view is instantiated from GameEntryView
        if self.game is not None:
            return self.game
        # otherwise use url to define self.game
        try:
            return Game.objects.get(series__slug=self.slug, game_id=self.requested_game_id)
        except Game.DoesNotExist:
            raise Http404("Game does not exist")

    def get_context(self, game, psid, forms=None):
        context = super().get_context()
        context.update({
            'questions': self.questions_with_forms(game, forms),
            'psid': psid
        })
        return context

    def get_forms(self, game, form_data=()):
        """Get all the game question forms, empty or populated with form_data from post.
           Any form data submitted with question_id not in this game will be ignored,
           likewise any question without data (e.g. incomplete forms) will be handled"""
        form_data = form_data or {}
        if form_data:
            forms = {q.id: QuestionAnswerForm(
                question_id=q.id,
                auto_id=f'%s_{q.id}',
                initial={'question_id': q.id, 'raw_string': form_data.get(str(q.id))},
                data={'question_id': q.id, 'raw_string': form_data.get(str(q.id))}
            )
                for q in game.questions.order_by('number')
            }
        else:
            forms = {q.id: QuestionAnswerForm(
                question_id=q.id,
                auto_id=f'%s_{q.id}'
            )
                for q in game.questions.order_by('number')
            }
        return forms

    def questions_with_forms(self, game, forms=None):
        forms = forms or self.get_forms(game)
        questions_with_forms = [
            (q, forms[q.id]) for q in game.questions.order_by('number')
        ]
        return questions_with_forms

    def get_game_and_player(self, psid):
        """Parses unique psid to get game and player object, raises PermissionDenied on all errors"""
        try:
            game, player = self.unsign_game_player(psid)
        except (BadSignature, Player.DoesNotExist, Game.DoesNotExist):
            raise PermissionDenied
        return game, player

    def unsign_game_player(self, pac):
        b36_gid, b36_pid = self.signer.unsign(pac).split("-")
        return Game.objects.get(id=int(b36_gid, 36)), Player.objects.get(id=int(b36_pid, 36))

    def sign_game_player(self):
        return self.signer.sign(f"{base_repr(self.game.id, 36)}-{base_repr(self.player.id, 36)}")


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
        game_id = request.GET.get('game_id')

        if game_id:
            if request.user.is_anonymous:
                return self.message(request,
                                    'I think you are a game host trying to preview a game.  You must login first')
            # /c/rambus/play?game_id=2
            g = find_hosted_game(slug, game_id, request.user)
        else:
            g = find_latest_active_game(slug)

        if slug == 'commonology':
            if not g:
                return self.message(request,
                                    'Sorry the next game has not started yet.  Join our list so we can let you know when it does.')
            else:
                return GameFormView(request=request).dispatch(request, *args, **kwargs)

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
        player, _ = Player.objects.get_or_create(email='digifuzi@gmail.com')
        return GameFormView(game=g, player=player).render_game(request)
        if not g:
            return self.warning(request,
                                ('Sorry the next game has not started yet.  '
                                 'Join our list so we can let you know when it does.'),
                                keep_form=False)

        # if request.user.is_authenticated:
        #     player = is_validated(request.user.email)
        #     # if not (slug == 'commonology' or player.series.filter(slug=slug).exists()):
        #     #     return self.warning(request, 'Sorry the game you requested is not available without an invitation.',
        #     #                         keep_form=False)
        #
        #     # url = game_url(g.google_form_url, request.user.email)
        #     return GameFormView(request=request).dispatch(request, *args, **kwargs)

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
            return GameFormView(player=player).get(request)
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
        except Player.DoesNotExist:
            p = Player(email=email)
        p.series.add(Series.objects.get(slug=slug))
        p.save()

        g = find_latest_active_game(slug)
        if not g:
            gc = GameEntryView()
            return gc.warning(request, 'Sorry the next game has not started yet.', keep_form=False)

        url = game_url(g.google_form_url, email)
        return redirect(url)


# ---- To be deprecated once we host forms ---- #
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
