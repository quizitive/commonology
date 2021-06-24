import gspread
import logging

from django.conf import settings
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.core.signing import Signer, BadSignature
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.views.generic.base import View
from django.views.generic.edit import FormMixin
from project.views import CardFormView
from game.forms import TabulatorForm, QuestionAnswerForm
from game.models import Game, Series
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

    def _child_dispatch(self, request, *args, **kwargs):
        # implement this in views that inherit from this class if you need
        # a place to add additional dispatch logic after class variables
        # are instantiated but before the dispatch work is done
        pass

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
    player = None
    uuid = None

    def __call__(self, *args, **kwargs):
        pass

    def dispatch(self, request, *args, **kwargs):
        self.uuid = self.kwargs.get('uuid')
        return super().dispatch(request, *args, **kwargs)

    def render_game(self, request, player_email):
        # used to load a clean game form for a validated player
        signed_email = self.signer.sign(player_email)
        return render(request, 'game/game_form.html', self.get_context(self.game, signed_email))

    def get(self, request, game_id, *args, **kwargs):
        # todo: render a player's game responses
        # return render(request, 'game/game_form.html', self.get_context(self.game, None))
        return self.render_game(request, 'e@mail.com')

    def post(self, request, *args, **kwargs):

        # todo: this should maybe go back to the view Marc's working on?
        # make sure game is still open, and handle various scenarios
        if not self.game.is_active:

            # 1: This game has already been published, send all traffic to leaderboard
            if self.game.publish:
                header = "Game Over"
                msg = "This game is already scored, head on over to the results and join the conversation!"
                button_label = "The Results"
                return self._game_form_fail_card(request, header, msg, button_label)

            # 2: This user has already submitted answers for this game, send them to their answers
            # todo: need a static form view for players that have already answered
            if request.user.is_authenticated:
                if request.user.id in self.game.players.values_list('player', flat=True):
                    header = "Game Played"
                    msg = "You've already played this game! Your answers have been emailed to you."
                    form_action = reverse('home')
                    return self._game_form_fail_card(request, header, msg, None)

            # 3: This user isn't logged in and/or didn't play this game, send them home
            header = "Game Not Active"
            msg = "This game is no longer active, please try a different game."
            return self._game_form_fail_card(request, header, msg, None)

        # Make sure this is a real email that hasn't been tampered with
        signed_email = self.request.POST.get('email')
        if signed_email:
            try:
                email = self.signer.unsign(signed_email)
            except BadSignature:
                raise PermissionDenied
            try:
                player = Player.objects.get(email=email)
                # todo: player should be in the series! make sure they're added on validation
            except Player.DoesNotExist:
                raise PermissionDenied
            if player.id in self.game.players.values_list('player', flat=True):
                header = "Game Played"
                msg = "You've already played this game! Your answers have been emailed to you."
                return self._game_form_fail_card(request, header, msg, None)

        # build a dict with the form inputs
        form_data = {qid: answer
                     for qid, answer in
                     zip(self.request.POST.getlist('question_id'), self.request.POST.getlist('raw_string'))}

        forms = self.get_forms(self.game, form_data)
        if any([f.errors for f in forms.values()]):
            context = self.get_context(self.game, signed_email, forms)
            return render(request, 'game/game_form.html', context)

        # todo: save form data
        print("success!")

        # todo: a success screen
        return redirect('home')

    def test_func(self):
        # override super method, we don't want to restrict access to game form for
        # new players of a series. obtaining the unique url is validation enough
        return True

    def get_game(self):
        try:
            # todo: make this use game uuid
            return Game.objects.get(series__slug=self.slug, game_id=self.requested_game_id)
        except Game.DoesNotExist:
            raise Http404("Game does not exist")

    def get_context(self, game, signed_email, forms=None):
        context = super().get_context()
        context.update({
            'questions': self.questions_with_forms(game, forms),
            'email': signed_email
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

    def _game_form_fail_card(self, request, header, msg, button_label, form_action=None):
        # todo: probably deprecated
        if form_action is None:
            if self.slug == "commonology":
                form_action = reverse('leaderboard:current-leaderboard')
            else:
                form_action = reverse('series-leaderboard:current-leaderboard',
                                      kwargs={'series_slug': self.requested_slug})

        gc = GameEntryView()
        return gc.warning(
            request,
            header=header,
            message=msg,
            button_label=button_label,
            keep_form=False,
            form_method='get',
            form_action=form_action
        )

    def _redirect_to_play(self):
        # todo: probably deprecated
        if self.requested_slug:
            return redirect('series-game:play', series_slug=self.requested_slug, uuid=self.uuid)
        return redirect('game:play', uuid=self.uuid)


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
        if not g:
            return self.warning(request,
                                ('Sorry the next game has not started yet.  '
                                 'Join our list so we can let you know when it does.'),
                                keep_form=False)

        if request.user.is_authenticated:
            player = is_validated(request.user.email)
            # if not (slug == 'commonology' or player.series.filter(slug=slug).exists()):
            #     return self.warning(request, 'Sorry the game you requested is not available without an invitation.',
            #                         keep_form=False)

            # url = game_url(g.google_form_url, request.user.email)
            return GameFormView(request=request).dispatch(request, *args, **kwargs)

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
