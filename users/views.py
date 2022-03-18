from django.conf import settings
from django.forms import HiddenInput
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.views.generic.base import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, PasswordChangeView
from django.core.exceptions import ValidationError
from django.core.signing import Signer, BadSignature
from django.core.validators import validate_email
from django.template.loader import render_to_string
from project.card_views import recaptcha_check, BaseCardView, CardFormView
from users.forms import PlayerProfileForm, PendingEmailForm, JoinForm
from users.models import PendingEmail, Player
from users.utils import unsubscribe, sign_user
from mail.tasks import mail_task
from project.utils import redis_delete_patterns
from game.models import Series
from .utils import remove_pending_email_invitations

User = get_user_model()


@login_required()
def user_logout(request):
    logout(request)
    return redirect(reverse('home'))


def create_and_send_confirm(request, player):
    remove_pending_email_invitations()
    email = player.email
    pe = PendingEmail.objects.create(email=email)

    domain = get_current_site(request)
    url = f'https://{domain}/validate_email/{pe.uuid}/'

    msg = render_to_string('users/validate_email.html', {'url': url})

    return mail_task("Let's play Commonology", msg, [(email, None)])


class CustomLoginView(auth_views.LoginView, CardFormView):
    card_template = "registration/login.html"

    def form_valid(self, form):
        u = form.get_user()
        if u is None:
            # The form clean_username() method should have guaranteed an active player
            email = form.cleaned_data['username']
            p = Player.objects.get(email=email)
            create_and_send_confirm(self.request, p)

            msg = f'An email validation link was sent to {email}. ' \
                  f'Please check your email and use that link to continue logging into Commonology. ' \
                  f'Sometimes, unfortunately, those messages go to a spam or junk folder.'
            self.custom_message = msg
            return super(CardFormView, self).get(self.request, form=None, button_label=None)

        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, CardFormView):
    form_class = PlayerProfileForm
    card_template = 'users/cards/profile_card.html'
    header = "Edit Profile"

    def post(self, request, *args, **kwargs):
        recaptcha_check(request)

        form = self.get_form()

        if not form.is_valid():
            messages.error(request, "There was a problem saving your changes. Please try again.")
            return self.render(request)

        user = form.save(commit=False)
        if 'email' in form.changed_data:
            email = request.user.email
            new_email = user.email
            user.email = email
            user.save()
            form.email = email

            messages.info(request,
                          f"We sent an email confirmation to {new_email} and will "
                          f"updated your profile once you have followed the confirmation link.")

            remove_pending_email_invitations()
            referrer = Player.objects.get(email=email)
            pe = PendingEmail(email=new_email, referrer=referrer)
            pe.save()
            self.send_change_confirm(request, pe)
            return self.render(request)

        if 'display_name' in form.changed_data:
            # we need to clear leaderboards this person appears on from cache to propagate change
            played_game_ids = user.game_ids
            redis_delete_patterns(*[f'leaderboard_{g["game_id"]}' for g in played_game_ids])

        form.save()
        messages.info(request, "Your changes have been saved!")
        return self.render(request)

    def get_form(self, form_class=None):
        email = self.request.user.email
        cu = User.objects.get(email=email)
        form = self.form_class(instance=cu, data=self.request.POST or None)
        return self.format_form(form)

    @staticmethod
    def send_change_confirm(request, pe):
        email = pe.email
        confirm_url = make_uuid_url(request, uuid=pe.uuid, name='/email_change_confirm/')

        context = {'confirm_url': confirm_url}
        msg = render_to_string('users/email_change.html', context)

        return mail_task('Email confirmation', msg, [(email, None)])


class JoinView(CardFormView):
    form_class = PendingEmailForm
    header = "Join Commonology"
    button_label = "Join"
    card_template = 'users/cards/join_card.html'
    custom_message = "A new game goes live every Wednesday at 12pm EST. Join us to get notified!"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        recaptcha_check(request)

        if not self.get_form().is_valid():
            return self.render(request, *args, **kwargs)

        email = request.POST['email']

        if not email:
            return redirect('login')

        try:
            user = User.objects.get(email=email)
            if user.is_member:
                messages.info(request, 'There is already an account with that email, please login.')
                return redirect('login')

        except User.DoesNotExist:
            pass

        referrer = request.session.get('r')
        if referrer:
            referrer = Player.objects.filter(_code=referrer).first()
        send_invite(request, email, referrer=referrer)

        self.custom_message = f"We sent your unique join link to {email}. " \
                              f"Don't forget to check your spam or junk folder if need be. " \
                              f"You may close this window now."

        self.header = "Invitation Sent!"
        return self.info(request,
                         message=self.custom_message,
                         form=None,
                         form_method='get',
                         form_action='/',
                         button_label='Ok')


def make_uuid_url(request, uuid=None, name='/join/', slug=None):
    if slug:
        return request.build_absolute_uri(f'c/{slug}/{name}/{uuid}')
    else:
        url = request.build_absolute_uri(name)
    if uuid:
        url += str(uuid)
    return url


def send_invite(request, email, referrer=None):
    remove_pending_email_invitations()

    pe = PendingEmail(email=email, referrer=referrer)
    pe.save()

    email = pe.email
    join_url = make_uuid_url(request, uuid=pe.uuid)
    referrer_str = ""
    if pe.referrer:
        referrer = User.objects.filter(email=pe.referrer).first()
        if referrer is None:
            # Do not send invite if referrer does not exist.
            return 0

        if referrer.first_name and referrer.last_name:
            referrer_str = f'{referrer.first_name} {referrer.last_name} has invited you to join Commonology.'

        else:
            referrer_str = f'Your friend {referrer.email} has invited you to Commonology.'

        more_info_str = mark_safe(f"Head over to our <a href='https://commonologygame.com/about/'>"
                                  f"about page</a> to learn more.")

    else:
        referrer_str = f"You requested a join link for Commonology."
        more_info_str = ""

    context = {'referrer_str': referrer_str, 'join_url': join_url, 'more_info_str': more_info_str}
    msg = render_to_string('emails/invite_email.html', context)

    return mail_task("You're Invited to Commonology", msg, [(email, None)])


class InviteFriendsView(LoginRequiredMixin, BaseCardView):
    header = "Invite Friends"
    button_label = ""
    card_template = "users/cards/invite_card.html"

    def post(self, request, *args, **kwargs):
        recaptcha_check(request)
        emails = request.POST['emails'].split(",")
        emails = [e.strip().lower() for e in emails]
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                messages.warning(request, f"{email} is not a valid email")
                continue

            try:
                User.objects.get(email=email)
                # can't join if user exists
                messages.warning(request, f"User {email} already exists")
            except User.DoesNotExist:
                send_invite(request, email, request.user)
                messages.info(request, f"Invite successfully sent to {email}.")

        return redirect('invite')

    def get_context_data(self, *args, **kwargs):
        players_referred = self.request.user.players_referred
        return super().get_context_data(
            *args,
            player_code=f'?r={self.request.user.code}',
            players_referred=players_referred,
            referral_count=players_referred.count(),
            reward_threshold=settings.REWARD_THRESHOLD,
            can_claim=players_referred.count() >= settings.REWARD_THRESHOLD,
            share_message=f"Join me at Commonology. New game every Wednesday at 12pm ET!\n"
                          f"https://commonologygame.com/play?r={self.request.user.code}",
            **kwargs
        )


class EmailConfirmedView(View):

    def get(self, request, uidb64, *args, **kwargs):
        try:
            pe = PendingEmail.objects.filter(uuid__exact=uidb64).first()
            if pe is None:
                return self._join_fail(request)

            email = pe.email

            try:
                user = User.objects.get(email=email)
                if user.is_member:
                    messages.info(request, 'You already have an account.')
                    return redirect('/login/')
                display_name = user.display_name
            except User.DoesNotExist:
                display_name = ''
                user = User(email=email, referrer=pe.referrer)
                user.save()

            form = JoinForm(initial={'email': pe.email, 'referrer': pe.referrer, 'display_name': display_name})
            messages.info(request, mark_safe(f"Email: {pe.email}<br/>(you can change this after signing up)"))
            return render(request, "users/register.html", {"form": self._format_form(form), "email": email})

        except PendingEmail.DoesNotExist:
            return self._join_fail(request)
        except ValidationError:
            return self._join_fail(request)

    def post(self, request, uidb64, *args, **kwargs):
        email = request.POST.get('email')

        # if the player is already in our database, update that record
        try:
            user = User.objects.get(email=email)
            form = JoinForm(request.POST, instance=user)
        except User.DoesNotExist:
            form = JoinForm(request.POST)

        if not email:
            return redirect('home')

        if form.is_valid():

            pe = PendingEmail.objects.filter(email__exact=email).filter(uuid=uidb64).first()
            if pe is None:
                return self._join_fail(request)

            user = form.save(commit=False)
            user.referrer = pe.referrer
            user.is_member = True
            user.save()
            Series.objects.get(slug='commonology').players.add(user)
            raw_password = form.clean_password2()
            user = authenticate(email=user.email, password=raw_password)
            auth_login(request, user)
            PendingEmail.objects.filter(email__iexact=user.email).delete()

            return redirect('/')

        messages.info(request, mark_safe(f"Email: {email}<br/>(you can change this after signing up)"))
        return render(request, "users/register.html", {"form": self._format_form(form)})

    @staticmethod
    def _format_form(form):
        for key, field in form.fields.items():
            field.widget.attrs['class'] = 'w3-input'
            field.widget.attrs['style'] = 'background:none;'
        form.fields['email'].widget.attrs['readonly'] = True
        form.fields['email'].widget = HiddenInput()
        return form

    def _join_fail(self, request):
        messages.error(request, "It seems the url link we sent you has something wrong with it. "
                                "Please try one more time.")
        messages.error(request, "If that does not work then please do not give up on us. Send us a help message.")
        context = {'header': "Join Fail"}
        return render(request, 'users/base.html', context)


class PwdResetRequestSentView(PasswordResetDoneView):

    def get(self, request, *args, **kwargs):
        custom_message = mark_safe(
            f"We've emailed you instructions for setting your password, "
            f"if an account exists with the email you entered. You should receive them shortly."
            f"<br/><br/>If you don't receive an email, please make sure you've entered the address"
            f" you registered with, and check your spam folder")

        context = {'header': "Reset Password", 'custom_message': custom_message}
        return render(request, 'users/base.html', context)

    def post(self, request, *args, **kwargs):
        return redirect('/login/')


class PwdResetConfirmView(PasswordResetConfirmView):

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.success_url = reverse('login')
        if form.is_valid():
            messages.info(request, "Your password has been successfully changed.")
        else:
            messages.warning(request, "There was an error updating your password, please try again.")
        return super().post(request, args, kwargs)


class EmailChangeConfirmedView(View):

    def get(self, request, uidb64):
        try:
            pe = PendingEmail.objects.filter(uuid__exact=uidb64).first()

            if pe is None:
                return self._confirm_fail(request)

            new_email = pe.email  # This is what is confirmed and what we want it to be.

            try:
                current_email = pe.referrer
                user = User.objects.get(email=current_email)
                user.email = new_email
                user.save()
                return redirect(reverse('profile'))
            except User.DoesNotExist:
                return self._confirm_fail(request)

        except PendingEmail.DoesNotExist:
            return self._confirm_fail(request)
        except ValidationError:
            return self._confirm_fail(request)

    def _confirm_fail(self, request):
        messages.error(request, "It seems the url link we sent you has something wrong with it. "
                                "Please try to change your email one more time.")
        messages.error(request, "If that does not work then please do not give up on us. Send us a help message.")
        context = {'header': "Email Change Fail"}
        return render(request, 'users/base.html', context)


class PwdChangeView(CardFormView, PasswordChangeView):
    header = "Change Password"
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        messages.info(self.request, "Your password has been successfully updated.")
        return super().form_valid(form)


def send_unsubscribed_notice(request, player):
    email = player.email
    protocol = 'HTTPS'
    domain = request.META['SERVER_NAME']

    signed_code = sign_user(player.email, player.code)

    context = {'signed_code': signed_code, 'protocol': protocol, 'domain': domain}
    msg = render_to_string('emails/unsubscribe_email.html', context)

    return mail_task("Unsubscribed", msg, [(email, None)])


class UnsubscribeView(View):
    def get(self, request, token):
        i, t = token.split(':')
        context = {'header': 'Unsubscribe'}

        if i == 'None':
            # This means it was an unsubscribe from an invite email.
            context['custom_message'] = \
                f"It seems you received an unwanted invite from a friend. " \
                f"You have not been added to any subscription lists so there is nothing more to do. " \
                f"However, if this was a mistake and you do want to join please use the Join Commonology button " \
                f"in the invite email you received.  Or visit our home page and join there.  Thank you!"
            return render(request, 'users/base.html', context)

        try:
            u = User.objects.filter(_code=i).first()
        except User.DoesNotExist:
            context['custom_message'] = "You are not subscribed."
            return render(request, 'users/base.html', context)

        email = u.email
        t = ':'.join([email, t])
        try:
            e = Signer().unsign(t)
            unsubscribe(e)
            context['custom_message'] = f"You have been unsubscribed. If you did not mean to unsubscribe " \
                                        f"you can simply login and update your profile."
            send_unsubscribed_notice(request, u)
        except BadSignature:
            context['custom_message'] = "There is something wrong with your unsubscribe link."
        return render(request, 'users/base.html', context)

    def post(self, request, *args, **kwargs):
        return redirect(reverse('home'))


class SubscribeView(View):
    def get(self, request, token):
        i, t = token.split(':')
        context = {'header': 'Subscribe'}

        bad_msg = f"There is something wrong with the link you used. " \
                  f"If you wish to re-subscribe then please log in and " \
                  f"and check subscribed in your profile settings. You can " \
                  f"change your profile by selecting your name in the dropdown " \
                  f"menu on the top right of our site.  Sorry for the inconvenience."

        try:
            u = User.objects.filter(_code=i).first()
        except User.DoesNotExist:
            context['custom_message'] = bad_msg
            return render(request, 'users/base.html', context)

        email = u.email
        t = ':'.join([email, t])
        try:
            e = Signer().unsign(t)
            if u.email == e:
                u.subscribed = True
                u.save()
            context['custom_message'] = f"You have re-subscribed."
        except BadSignature:
            context['custom_message'] = bad_msg
        return render(request, 'users/base.html', context)

    def post(self, request, *args, **kwargs):
        return redirect(reverse('home'))


class ValidateEmailView(View):
    # Use to validate email for passwordless login

    def get(self, request, uidb64, *args, **kwargs):
        try:
            pe = PendingEmail.objects.filter(uuid__exact=uidb64).first()
            if pe is None:
                return self.login_fail(request)

            email = pe.email

            p = Player.objects.get(email=email)
            login(request, p, backend='django.contrib.auth.backends.ModelBackend')
            return redirect(reverse('home'))

        except Player.DoesNotExist:
            return self.login_fail(request)
        except PendingEmail.DoesNotExist:
            return self.login_fail(request)
        except ValidationError:
            return self.login_fail(request)

    @staticmethod
    def login_fail(request):
        messages.error(request, "It seems the url link we sent you has something wrong with it. "
                                "Please try one more time.")
        messages.error(request, "If that does not work then please do not give up on us. Send us a help message.")
        context = {'header': "Login Fail"}
        return render(request, 'users/base.html', context)
