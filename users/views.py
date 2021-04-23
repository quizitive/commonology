from django.forms import HiddenInput
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, PasswordChangeView
from django.core.exceptions import ValidationError
from django.core.signing import Signer, BadSignature
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.views.generic.base import View
from django.views.generic.edit import FormMixin
from users.forms import PlayerProfileForm, PendingEmailForm, InviteFriendsForm, JoinForm
from users.models import PendingEmail
from users.utils import unsubscribe
from mail.sendgrid_utils import sendgrid_send

from .utils import remove_pending_email_invitations

User = get_user_model()


@login_required()
def user_logout(request):
    logout(request)
    return redirect(reverse('home'))


class UserCardFormView(FormMixin, View):
    """
    A base class with sensible defaults for our basic user form-in-card
    See template users/cards/base_users_card.html for additional template
    variables that can be set to customize form further.

    Common use case would be to define a form_class and override post()
    to handle form-specific functionality
    """
    # form_class = YourFormClass
    header = "Welcome To Commonology"
    custom_message = None
    button_label = "Ok"
    card_template = 'users/cards/base_users_card.html'
    page_template = 'users/base.html'

    def get(self, request, *args, **kwargs):
        return self.render(request, *args, **kwargs)

    def render(self, request, *args, **kwargs):
        return render(request, self.page_template, self.get_context_data(**kwargs))

    def get_context_data(self, *args, **kwargs):
        context = {
            'header': self.header,
            'form': self.format_form(self.get_form()),
            'card_template': self.card_template,
            'button_label': self.button_label,
            'custom_message': self.custom_message
            }
        context.update(kwargs)
        return super().get_context_data(**context)

    def get_form(self, form_class=None):
        form = super().get_form()
        return self.format_form(form)

    @staticmethod
    def format_form(form):
        for key, field in form.fields.items():
            if field.widget.__class__.__name__ == 'CheckboxInput':
                field.widget.attrs['class'] = 'w3-check'
            else:
                field.widget.attrs['class'] = 'w3-input'
        return form


class ProfileView(LoginRequiredMixin, UserCardFormView):

    form_class = PlayerProfileForm
    card_template = 'users/cards/profile_card.html'
    header = "Edit Profile"

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            if 'email' in form.changed_data:
                email = request.user.email
                user = form.save(commit=False)
                new_email = user.email
                user.email = email
                user.save()
                form.email = email

                messages.info(request,
                              f"We sent an email confirmation to {new_email} and will "
                              f"updated your profile once you have followed the confirmation link.")

                remove_pending_email_invitations()
                pe = PendingEmail(email=new_email, referrer=email)
                pe.save()
                self.send_change_confirm(request, pe)
            else:
                form.save()

            messages.info(request, "Your changes have been saved!")
        else:
            messages.error(request, "There was a problem saving your changes. Please try again.")

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

        return sendgrid_send('Email confirmation', msg, [(email, None)])


class JoinView(UserCardFormView):
    form_class = PendingEmailForm
    header = "Join Commonology"
    button_label = "Join"
    card_template = 'users/cards/join_card.html'
    custom_message = "Enter your email to join the game, follow your friends, and much more coming soon!"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        if not email:
            return redirect('login')

        try:
            user = User.objects.get(email=email)
            if user.is_member:
                messages.info(request, 'There is already an account with that email, please login.')
                return redirect('login')

        except User.DoesNotExist:
            pass

        remove_pending_email_invitations()
        pe = PendingEmail(email=email)
        pe.save()
        send_invite(request, pe)

        self.custom_message = f"We sent your unique join link to {email}. " \
                              f"Don't forget to check your spam or junk folder if need be. " \
                              f"You may close this window now."

        self.header = "Invitation Sent!"
        return self.render(request, form=None, button_label='Ok')


def make_uuid_url(request, uuid=None, name='/join/'):
    url = request.build_absolute_uri(name)
    if uuid:
        url += str(uuid)
    return url


def send_invite(request, pe):
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

    return sendgrid_send("You're Invited to Commonology", msg, [(email, None)])


class InviteFriendsView(LoginRequiredMixin, UserCardFormView):

    header = "Invite Friends"
    form_class = InviteFriendsForm
    button_label = "Send"

    def get(self, request, *args, **kwargs):
        messages.info(request, "Enter your friends' emails to invite them to Commonology!")
        return super().get(request)

    def post(self, request, *args, **kwargs):
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
                remove_pending_email_invitations()
                pe = PendingEmail(email=email, referrer=request.user.email)
                pe.save()
                send_invite(request, pe)
                messages.info(request, f"Invite successfully sent to {email}.")

        return redirect('invite')


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
            raw_password = form.clean_password2()
            user = authenticate(email=user.email, password=raw_password)
            login(request, user)
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
        custom_message = f"We've emailed you instructions for setting your password, " \
                         f"if an account exists with the email you entered. You should receive them shortly." \
                         f"\n\nIf you don't receive an email, please make sure you've entered the address" \
                         f" you registered with, and check your spam folder"

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


class PwdChangeView(UserCardFormView, PasswordChangeView):
    header = "Change Password"
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        messages.info(self.request, "Your password has been successfully updated.")
        return super().form_valid(form)


class UnsubscribeView(View):
    def get(self, request, token):
        i, t = token.split(':')
        context = {'header': 'Unsubscribe'}
        try:
            u = User.objects.filter(id=i).first()
        except User.DoesNotExist:
            context['custom_message'] = "You have been unsubscribed."
            return render(request, 'users/base.html', context)

        email = u.email
        t = ':'.join([email, t])
        try:
            e = Signer().unsign(t)
            unsubscribe(e)
            context['custom_message'] = f"You have been unsubscribed. If you did not mean to unsubscribe" \
                                        f"you can simply login and update your profile."
        except BadSignature:
            context['custom_message'] = "There is something wrong with your unsubscribe link."
        return render(request, 'users/base.html', context)
