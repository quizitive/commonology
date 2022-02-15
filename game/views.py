from os import environ as env
import gspread
import logging
from numpy import base_repr

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.core.signing import Signer, BadSignature
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.views.generic.base import View
from django.views.generic.edit import FormMixin
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse

from project.views import CardFormView
from project.utils import slackit, our_now
from project.card_views import recaptcha_check
from game.forms import TabulatorForm, QuestionAnswerForm, GameDisplayNameForm, QuestionSuggestionForm, AwardCertificateForm
from game.models import Game, Series, Question, Answer
from game.gsheets_api import write_new_responses_to_gdrive
from game.rollups import autorollup_question_answer
from game.utils import find_latest_public_game, find_latest_published_game, write_winner_certificate
from leaderboard.leaderboard import tabulate_results, winners_of_game
from users.models import PendingEmail, Player
from users.forms import PendingEmailForm
from users.views import remove_pending_email_invitations
from users.utils import get_player
from mail.tasks import mail_task
from rewards.utils import check_for_reward
from components.models import Component


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
            'game': self.game,
            'game_id': self.game.game_id,
            'game_name': self.game.name,
            'date_range': date_range,
            'series_slug': self.requested_slug,
            'requested_game_id': self.requested_game_id,
        }
        return context


class PSIDMixin:
    """A mixin with utility functions to sign and unsign a player and game ID combination"""
    signer = Signer()

    def sign_game_player(self, game, player):
        return self.signer.sign(f"{base_repr(game.id, 36)}-{base_repr(player.id, 36)}")

    def build_signed_url(self, game, player):
        return f'/c/{game.series.slug}/game/{game.game_id}/{self.sign_game_player(game, player)}'

    def unsign_game_player(self, psid):
        """Parses unique psid to get game and player object, raises PermissionDenied on all errors"""
        try:
            b36_gid, b36_pid = self.signer.unsign(psid).split("-")
            return Game.objects.get(id=int(b36_gid, 36)), Player.objects.get(id=int(b36_pid, 36))
        except (BadSignature, Player.DoesNotExist, Game.DoesNotExist):
            raise PermissionDenied


class GameFormView(FormMixin, PSIDMixin, BaseGameView):

    def render_game(self, request, game, player, editable=True):
        # called when an validated player passes though GameEntryView
        if editable:
            psid = self.sign_game_player(game, player)
            dn_form = self.display_name_form(player.display_name)
        else:
            psid = ''
            dn_form = self.display_name_form('Reviewer')

        self.requested_slug = self.slug = game.series.slug
        self.game = game
        return render(request, 'game/game_form.html',
                      self.get_context(game, player.id, psid, dn_form, editable=editable))

    def get(self, request, *args, **kwargs):
        # any request without a player_signed_id gets redirected to GameEntryView
        if (psid := kwargs.get('player_signed_id')) is None:
            return redirect('game:uuidplay', game_uuid=self.game.uuid)

        game, player = self.unsign_game_player(psid)

        dn_form = self.display_name_form(player.display_name, editable=False)
        form_data = {
            str(qid): answer
            for qid, answer in Answer.objects.filter(
                question__game=game,
                player=player
            ).values_list('question', 'raw_string')
        }
        forms = self._build_game_forms(game, form_data, editable=False)
        context = self.get_context(game, player.id, None, dn_form, forms, False)
        return render(request, 'game/game_form.html', context)

    def post(self, request, *args, **kwargs):
        recaptcha_check(request)

        # make sure this is a real submission that hasn't been tampered with
        if (psid := self.request.POST.get('psid')) is None:
            raise PermissionDenied
        game, player = self.unsign_game_player(psid)

        if player.id in self.game.players_dict.values_list('player', flat=True):
            return self.render_answers_submitted_card(request, 'duplicate', player, game)

        dn_form = self.display_name_form(self.request.POST.get('display_name'))
        game_forms = self._build_game_forms_post(player)

        if any([not f.is_valid() for f in game_forms.values()]):
            context = self.get_context(self.game, player.id, psid, dn_form, game_forms)
            return render(request, 'game/game_form.html', context)

        player.display_name = self.request.POST.get('display_name')
        player.save()

        self._save_forms(game_forms)
        self.email_player_success(request, game, player)
        write_new_responses_to_gdrive.delay(game.id)

        check_for_reward(player)

        return self.render_answers_submitted_card(request, 'success', player, game)

    @cached_property
    def questions(self):
        return self.game.questions.order_by('number')

    def _build_game_forms_post(self, player):
        # build a dict with the form inputs from POST request
        form_data = {
            qid: answer
            for qid, answer in
            zip(self.request.POST.getlist('question'), self.request.POST.getlist('raw_string'))
        }
        return self._build_game_forms(self.game, form_data, player)

    @transaction.atomic
    def _save_forms(self, forms):
        for form in forms.values():
            form.save()

    def render_answers_submitted_card(self, request, msg, player, game):
        msgs = {
            'success': {
                "header": "Success!",
                "custom_message": mark_safe(
                    f"<b>Your answers have been submitted.</b> You can see them now by clicking "
                    f"the button below, and we've emailed the link to <b>{player.email}</b>.<br/>"),
            },
            'duplicate': {
                "header": "You've already played!",
                "custom_message": mark_safe(f"You have already submitted answers for this game. "
                                            f"You can see them again by clicking the button below.\n<br/>"),
            }
        }
        return CardFormView(
            page_template='game/game_card_view.html',
            card_template='game/cards/game_complete_card.html',
        ).render(
            request,
            button_label="View my answers",
            form_class=None,
            form_method='get',
            form_action=f'/c/{game.series.slug}/game/{game.game_id}/{self.sign_game_player(game, player)}',
            player_code=f'?r={player.code}',
            player_id=player.id,
            title=f'Answers Submitted',
            **msgs[msg]
        )

    def email_player_success(self, request, game, player):
        answers_url = self.build_signed_url(game, player)
        domain = get_current_site(request)
        email_context = {
            'game_name': game.name,
            'url': f'https://{domain}{answers_url}'
        }
        answers_msg = render_to_string('game/game_complete_email.html', email_context)
        referral_link = Component.objects.filter(name="Referral Link", locations__app_name='mail').first()
        mail_task(f'{game.name}', answers_msg, [(player.email, player.code)], bottom_components=(referral_link,))

    def test_func(self):
        # override super method, which requires users to be logged in
        # this view can be accessed by anonymous users with a psid
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

    def get_game_rules(self):
        try:
            game_rules = Component.objects.get(name=f'Game Rules | {self.slug}')
        except Component.DoesNotExist:
            game_rules = None
        return game_rules

    def get_context(self, game, player_id=None, psid=None, dn_form=None, forms=None, editable=True, replay=False):
        context = super().get_context()
        if settings.RECAPTCHA3_INHIBIT:
            recaptcha_key = False
        else:
            recaptcha_key = settings.RECAPTCHA3_KEY

        context.update({
            'game': game,
            'top_components': game.top_components.all(),
            'game_rules': self.get_game_rules(),
            'dn_form': dn_form,
            'questions': self.questions_with_forms(game, forms),
            'psid': psid,
            'player_id': player_id,
            'editable': editable,  # flag to disable forms and js and hide submit button
            'replay': replay,
            'recaptcha_key': recaptcha_key,
        })
        return context

    def _build_game_forms(self, game, form_data=(), player=None, editable=True):
        """Build all the game question forms, empty or populated with form_data from post.
           Any form data submitted with a question not in this game will be ignored,
           likewise any question without data (e.g. incomplete forms) will be handled"""
        form_data = form_data or {}
        if form_data:
            forms = {q.id: QuestionAnswerForm(
                question=q,
                editable=editable,
                auto_id=f'%s_{q.id}',
                initial={'raw_string': form_data.get(str(q.id))},
                data={'question': q,
                      'raw_string': form_data.get(str(q.id)),
                      'player': player}
            )
                for q in self.questions
            }
        else:
            forms = {q.id: QuestionAnswerForm(
                question=q,
                auto_id=f'%s_{q.id}'
            )
                for q in self.questions
            }
        return forms

    def questions_with_forms(self, game, forms=None):
        forms = forms or self._build_game_forms(game)
        questions_with_forms = [
            (q, forms[q.id]) for q in self.questions.order_by('number')
        ]
        return questions_with_forms

    def display_name_form(self, display_name, editable=True):
        return GameDisplayNameForm(
            editable=editable,
            initial={'display_name': display_name}
        )


class InstantGameView(GameFormView):

    def get_game(self):
        return find_latest_published_game(self.slug)

    @cached_property
    def questions(self):
        return self.game.questions.exclude(type__in=(Question.op, Question.ov)).order_by('number')

    def get(self, request, *args, **kwargs):
        forms = self._build_game_forms(self.game)
        context = self.get_context(self.game, forms=forms, editable=True, replay=True)
        return render(request, 'game/game_form.html', context)

    def post(self, request, *args, **kwargs):
        game_forms = self._build_game_forms_post(None)
        context = self.get_context(self.game, None, None, forms=game_forms, editable=True, replay=True)

        if any([not f.is_valid() for f in game_forms.values()]):
            return render(request, 'game/game_form.html', context)

        self._autocode_responses_and_save_to_session(request, game_forms)

        if self.slug == "commonology":
            return redirect('leaderboard:current-results')
        else:
            return redirect('series-leaderboard:current-results', self.slug)

    def _autocode_responses_and_save_to_session(self, request, game_forms):
        request.session[f"game_{self.game.game_id}_answers"] = {}
        for question in self.questions.prefetch_related('coded_answers'):
            game_form = game_forms[question.id]
            raw_player_answer = game_form.data.get('raw_string')
            # this is the magic line that does the auto-rollups of inputs
            coded_player_answer = autorollup_question_answer(question, raw_player_answer)
            request.session[f"game_{self.game.game_id}_answers"][question.id] = coded_player_answer

    def get_game_rules(self):
        try:
            game_rules = Component.objects.get(name=f'Instant Game Rules | {self.slug}')
        except Component.DoesNotExist:
            game_rules = None
        return game_rules


# Ex. https://docs.google.com/forms/d/e/1FAIpQLSeGWLWt4VJ0-Pb9aGhEU9jukstTsGy97vlKgSVHykmLJB3jow/viewform?usp=pp_url&entry.1135425595=alex@commonologygame.com
def game_url(google_form_url, email):
    return google_form_url.replace('alex@commonologygame.com', email)


def send_confirm(request, g, email, referrer_id=None):
    remove_pending_email_invitations()
    referrer = get_player(referrer_id)
    pe = PendingEmail(email=email, referrer=referrer)
    pe.save()

    slug = g.series.slug
    game_uuid = g.uuid

    domain = get_current_site(request)
    url = f'https://{domain}/c/{slug}/play/{game_uuid}/{pe.uuid}/'

    msg = render_to_string('game/validate_email.html', {'join_url': url})

    return mail_task("Let's play Commonology", msg, [(email, None)])


def render_game(request, game, user=None, editable=True):
    if user:
        request.session['user_id'] = user.id
    else:
        user = request.user
    if editable:
        game.series.players.add(user)
    return GameFormView().render_game(request, game, user, editable)


class GameEntryView(PSIDMixin, CardFormView):
    form_class = PendingEmailForm
    header = "Game starts here!"
    button_label = "Submit"
    custom_message = "Enter your email address to play."
    page_template = "game/game_card_view.html"

    def message(self, request, msg):
        return self.render_message(request, msg, form=None, button_label='Ok', title='Play',
                                   form_method="get", form_action='/')

    def leaderboard(self, request, msg='Seems like the game finished.  See the leaderboard.', slug='commonology'):
        return self.render_message(request, msg, form=None, button_label='Leaderboard', title='Play',
                                   form_method="get", form_action=f'/c/{slug}/leaderboard/')

    def join(self, request, msg):
        return self.render_message(request, msg, form=None, button_label='Join', title='Play',
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
                return self.message(request,
                                    'Cannot find an active game.  We will let you know when the next game begins.')
            elif game_uuid:
                return self.message(request, 'Cannot find an active game.  Perhaps you have a bad link.')
            else:
                if slug is None or slug == 'commonology':
                    msg = 'Next game begins on Wednesday at noon.  Join so we can send you an invitation when it starts.'
                else:
                    msg = 'Cannot find an active game.  Join so we can let you know when the next game begins.'
                return self.join(request, msg)

        slug = g.series.slug

        # Backward compatibility
        if g.google_form_url:
            return redirect(g.google_form_url)

        is_active = g.is_active
        is_host = user in g.series.hosts.all()

        if is_host:
            # May be a host previewing a game
            return render_game(request, g)

        if not is_active and g.has_leaderboard and g.leaderboard.publish:
            return self.leaderboard(request, slug=slug)

        if g.user_played(user):
            return self.render_message(
                request,
                message=f"You have already submitted answers for this game. "
                        f"You can see them again by clicking the button below.",
                form=None,
                button_label="View my answers",
                header="You've already played!",
                form_method='get',
                form_action=f'/c/{g.series.slug}/game/{g.game_id}/{self.sign_game_player(g, user)}',
            )

        if game_uuid and g.not_started_yet:
            return render_game(request, g, editable=False)

        if not is_active:
            return self.message(request, msg='Seems like the game finished but has not been scored yet.')

        if user.is_authenticated:
            return render_game(request, g)

        return super().get(request, title=f'Play', *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # The get method already determined that:
        #    1. There is an active game for the given slug
        #    2. The player is not logged in
        #    3. The player is not the host

        recaptcha_check(request)

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

        if not self.get_form().is_valid():
            return self.render(request, *args, **kwargs)

        email = request.POST['email']

        referrer_id = request.session.get('r')

        p = get_player(referrer_id)
        if p and not p.is_active:
            return self.render_message(
                request,
                f"The account associated with this email has been deactivated. For more information, "
                f"please contact us using the contact form.",
                form=None,
                button_label=None
            )

        if p and (p.email == email):
            return render_game(request, g, p)

        send_confirm(request, g, email, referrer_id)
        custom_message = mark_safe(f"<b>We sent a game link to {email}. </b>"
                                   f"Don't forget to check your spam or junk folder if need be. "
                                   f"By the way, if you were logged in you'd be playing already.")

        self.header = "Game link sent!"
        return self.render_message(request, custom_message, form=None,
                                   form_method='get', form_action='', button_label=None)


class GameEntryValidationView(PSIDMixin, CardFormView):
    form_class = PendingEmailForm
    header = "Email validated here!"
    button_label = "Next"
    custom_message = ''
    page_template = "game/game_card_view.html"

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
            return self.warning(request, 'That game does not exist.  Perhaps you are using the wrong link.',
                                form=None)

        if not g.is_active:
            # This should rarely happy because GameEntryView.get() confirmed there is an active game.
            # However, someone could try to use a confirm link too late.
            return self.warning(request, 'Sorry the next game is no longer active.', form=None)

        if request.user.is_authenticated:
            if g.user_played(request.user):
                return self._user_played(request, g, request.user)
            return render_game(request, g)

        pe = PendingEmail.objects.filter(uuid__exact=pending_uuid).first()
        if pe is None:
            return self.message(request, 'Seems like there was a problem with the validation link. Please try again.')

        email = pe.email
        try:
            p = Player.objects.get(email=email)
        except Player.DoesNotExist:
            p = Player(email=email, referrer=pe.referrer)
            p.save()

        if g.user_played(p):
            return self._user_played(request, g, p)

        return render_game(request, g, p)

    def _user_played(self, request, g, user):
        return self.info(
            request,
            form=None,
            button_label="View my answers",
            header="You've already played!",
            form_method='get',
            form_action=f'/c/{g.series.slug}/game/{g.game_id}/{self.sign_game_player(g, user)}',
            message=f"You have already submitted answers for this game. "
                    f"You can see them again by clicking the button below.",
        )


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
        update = request.POST.get('update_existing') == 'on'
        game = Game.objects.get(sheet_name=fn, series__slug=series)

        try:
            tabulate_results(game, update)
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


class QuestionSuggestionView(LoginRequiredMixin, CardFormView):
    form_class = QuestionSuggestionForm
    header = "Suggest a Question"
    custom_message = f"Suggest a question for a future game! Please supply " \
                     f"some example answers."
    button_label = "Submit"

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            p = request.user
            msg = f"A new question has been suggested on the site:\n\n" \
                  f"Player display name: {p.display_name}\n" \
                  f"Player name (first & last): {p.first_name} {p.last_name}\n" \
                  f"Player email: {p.email}\n\n" + form.data['suggestion']
            subject = "New Question Suggestion"
            email = "concierge@commonologygame.com"
            slackit(msg)
            send_mail(subject=subject, message=msg,
                      from_email=None, recipient_list=[email])
            messages.info(request, message=f"Thank you, your question has successfully been submitted. "
                                           f"Feel free to suggest another.")
            return redirect('game:question-suggest')
        return self.get(request, *args, **kwargs)


class AwardCertificateView(LoginRequiredMixin, BaseGameView):
    def get_game(self):
        try:
            return Game.objects.get(game_id=self.requested_game_id, series__slug=self.slug)
        except ObjectDoesNotExist:
            return None

    def get(self, request, game_id, *args, **kwargs):
        if not self.game:
            msg = f'That game does not exist.'
            return render(request, 'single_card_view.html', context={'custom_message': msg})

        player = request.user

        if player not in winners_of_game(self.game):
            msg = f'You did not win game number {game_id}'
            return render(request, 'single_card_view.html', context={'custom_message': msg})

        if env.get('GITHUB_COMMONOLOGY_CI_TEST'):
            response = HttpResponse('pdf', content_type='application/pdf')
            return(response)

        game_number = self.game.game_id
        name = player.display_name
        date = our_now().date()

        filename = write_winner_certificate(name, date, str(game_number))
        fs = FileSystemStorage(location=settings.WINNER_ROOT)

        if not fs.exists(filename):
            msg = f'For some reason we could not make the award certificate.'
            return render(request, 'single_card_view.html', context={'custom_message': msg})

        with fs.open(filename) as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class AwardCertificateFormView(UserPassesTestMixin, CardFormView):

    def test_func(self):
        return self.request.user.is_staff

    form_class = AwardCertificateForm
    header = "Award Certificate Form"
    button_label = 'Submit'

    def post(self, request, *args, **kwargs):
        self.custom_message = ''
        form = self.get_form()

        if form.is_valid():
            name = form.data['name']
            n = form.data['game_number']

            date = our_now().date()

            filename = write_winner_certificate(name, date, n)
            fs = FileSystemStorage(location=settings.WINNER_ROOT)

            try:
                with fs.open(filename) as pdf:
                    response = HttpResponse(pdf, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={filename}'
                return response
            except IOError:
                self.custom_message = f'For some reason we could not make the award certificate.'

        return self.render(request)
