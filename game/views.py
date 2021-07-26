import gspread
import logging
from numpy import base_repr

from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.core.signing import Signer, BadSignature
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.safestring import mark_safe
from django.views.generic.base import View
from django.views.generic.edit import FormMixin
from project.views import CardFormView
from game.charts import PlayerTrendChart, PlayersAndMembersDataset
from game.forms import TabulatorForm, QuestionAnswerForm, GameDisplayNameForm
from game.models import Game, Series, Answer
from game.utils import find_latest_public_game
from leaderboard.leaderboard import tabulate_results
from users.models import PendingEmail, Player
from users.forms import PendingEmailForm
from users.views import remove_pending_email_invitations
from users.utils import get_player
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

    def render_game(self, request, game, player):
        # called when an validated player passes though GameEntryView
        psid = self.sign_game_player(game, player)
        dn_form = self.display_name_form(player.display_name)
        self.requested_slug = game.series.slug
        self.game = game
        return render(request, 'game/game_form.html', self.get_context(game, psid, dn_form))

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
        forms = self.get_game_forms(game, form_data, editable=False)
        context = self.get_context(game, None, dn_form, forms, False)
        return render(request, 'game/game_form.html', context)

    def post(self, request, *args, **kwargs):
        # make sure this is a real submission that hasn't been tampered with
        if (psid := self.request.POST.get('psid')) is None:
            raise PermissionDenied
        game, player = self.unsign_game_player(psid)

        if player.id in self.game.players.values_list('player', flat=True):
            return self.render_answers_submitted_card(request, 'duplicate', player, game)

        dn_form = self.display_name_form(self.request.POST.get('display_name'))
        # build a dict with the form inputs
        form_data = {
            qid: answer
            for qid, answer in
            zip(self.request.POST.getlist('question'), self.request.POST.getlist('raw_string'))
        }

        forms = self.get_game_forms(self.game, form_data, player)
        if any([f.errors for f in forms.values()]):
            context = self.get_context(self.game, psid, dn_form, forms)
            return render(request, 'game/game_form.html', context)

        player.display_name = self.request.POST.get('display_name')
        player.save()

        for form in forms.values():
            form.save()

        self.email_player_success(request, game, player)

        return self.render_answers_submitted_card(request, 'success', player, game)

    def render_answers_submitted_card(self, request, msg, player, game):
        msgs = {
            'success': {
                "header": "Success!",
                "custom_message": mark_safe(f"<b>Your answers have been submitted.</b> You can see them now by clicking "
                                  f"the button below, and we've emailed the link to <b>{player.email}</b>."),
            },
            'duplicate': {
                "header": "You've already played!",
                "custom_message": f"You have already submitted answers for this game. "
                                  f"You can see them again by clicking the button below.",
            }
        }
        return CardFormView().render(
            request,
            button_label="View my answers",
            form_class=None,
            form_method='get',
            form_action=f'/c/{game.series.slug}/game/{game.game_id}/{self.sign_game_player(game, player)}',
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
        sendgrid_send(f'{game.name}', answers_msg, [(player.email, None)])

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

    def get_context(self, game, psid, dn_form, forms=None, editable=True):
        context = super().get_context()
        context.update({
            'game': game,
            'dn_form': dn_form,
            'questions': self.questions_with_forms(game, forms),
            'psid': psid,
            'editable': editable  # flag to disable forms and js and hide submit button
        })
        return context

    def get_game_forms(self, game, form_data=(), player=None, editable=True):
        """Get all the game question forms, empty or populated with form_data from post.
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
                for q in game.questions.order_by('number')
            }
        else:
            forms = {q.id: QuestionAnswerForm(
                question=q,
                auto_id=f'%s_{q.id}'
            )
                for q in game.questions.order_by('number')
            }
        return forms

    def questions_with_forms(self, game, forms=None):
        forms = forms or self.get_game_forms(game)
        questions_with_forms = [
            (q, forms[q.id]) for q in game.questions.order_by('number')
        ]
        return questions_with_forms

    def display_name_form(self, display_name, editable=True):
        return GameDisplayNameForm(
            editable=editable,
            initial={'display_name': display_name}
        )


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
    url = (f'https://{domain}/c/{slug}/play/{game_uuid}/{pe.uuid}')

    msg = render_to_string('game/validate_email.html', {'join_url': url})

    return sendgrid_send("Let's play Commonology", msg, [(email, None)])


def render_game(request, game, user=None):
    if user:
        request.session['user_id'] = user.id
    else:
        user = request.user
    game.series.players.add(user)
    return GameFormView().render_game(request, game, user)


class GameEntryView(PSIDMixin, CardFormView):
    form_class = PendingEmailForm
    header = "Game starts here!"
    button_label = "Submit"
    custom_message = "Enter your email address to play."

    def message(self, request, msg):
        return self.render_message(request, msg, form=None, button_label='Ok',
                           form_method="get", form_action='/')

    def leaderboard(self, request, msg='Seems like the game finished.  See the leaderboard.', slug='commonology'):
        return self.render_message(request, msg, form=None, button_label='Leaderboard',
                           form_method="get", form_action=f'/c/{slug}/leaderboard/')

    def join(self, request, msg):
        return self.render_message(request, msg, form=None, button_label='Join',
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
                return self.join(request, 'Cannot find an active game.  Join so we can let you know when the next game begins.')

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

        referrer_id = request.GET.get('r')

        p = get_player(referrer_id)
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
            if g.user_played(request.user):
                return self._user_played(request, g, request.user)
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


@staff_member_required
def stats_view(request):
    chart_1 = PlayerTrendChart(
        PlayersAndMembersDataset, slug='commonology', name="chart_3", since_game=38)
    chart_2 = PlayerTrendChart(
        PlayersAndMembersDataset, slug='commonology', name="chart_2", since_game=38, agg_period=4)
    context = {
        "chart_1": chart_1,
        "chart_2": chart_2,
    }
    return render(request, 'game/stats.html', context)


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
