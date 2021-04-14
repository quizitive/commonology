from django.forms import HiddenInput
from django.urls import reverse, reverse_lazy
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, PasswordChangeView
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.views.generic.base import View
from django.views.generic.edit import FormMixin
from users.forms import PlayerProfileForm, PendingEmailForm, InviteFriendsForm, JoinForm
from users.models import PendingEmail
from mail.tasks import update_mailing_list_subscribed

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

        return send_mail(subject='Email confirmation', from_email=None,
                         message=msg, recipient_list=[email])


class JoinView(UserCardFormView):
    form_class = PendingEmailForm
    header = "Join Commonology"
    button_label = "Join"
    card_template = 'users/cards/join_card.html'
    custom_message = "Enter your email to join the game, follow your friends, and much more coming soon!"

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
            referrer_str = f'{referrer.first_name} {referrer.last_name}, ' \
                           f'whose email address is {referrer.email} requested this invitation.'

        else:
            referrer_str = f'Your friend whose email address is {referrer.email} requested this invitation.'

    context = {'referrer_str': referrer_str, 'join_url': join_url}
    msg = render_to_string('users/invite_email.html', context)

    return send_mail(subject='Join us', message=msg,
                     from_email=None, recipient_list=[email])


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
            messages.info(request, f"Email: {pe.email} (you can change this after signing up)")
            return render(request, "users/register.html", {"form": self._format_form(form), "email": email})

        except PendingEmail.DoesNotExist:
            return self._join_fail(request)
        except ValidationError:
            return self._join_fail(request)

    def post(self, request, uidb64, *args, **kwargs):
        form = JoinForm(request.POST)
        email = request.POST.get('email')
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

            update_mailing_list_subscribed(email)

            return redirect('/')

        messages.info(request, f"Email: {email} (you can change this after signing up)")
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
                update_mailing_list_subscribed(current_email, subscribed=False)
                update_mailing_list_subscribed(new_email, subscribed=True)
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
