import os
import uuid
from django.forms import HiddenInput
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView
from django.core.exceptions import ValidationError
from django.views.generic.base import View
from users.forms import PlayerProfileForm, PendingEmailForm, JoinForm
from users.models import PendingEmail
from users.htmx import InviteFriendsHTMXView

from .utils import remove_pending_email_invitations, send_invite

User = get_user_model()


@login_required()
def user_logout(request):
    logout(request)
    return redirect(reverse('home'))


def profile_view(request):
    if request.user.id is None:
        user_form = PlayerProfileForm(data=request.POST or None)
    else:
        email = request.user.email
        cu = User.objects.get(email=email)
        user_form = PlayerProfileForm(instance=cu, data=request.POST or None)
    if request.method == 'POST' and user_form.is_valid():
        user_form.save()
    return render(request, "users/profile.html", {"user_form": user_form})


def confirm_or_login(request, email):
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

    messages.info(request, f"An invitation email was sent to {email}. "
                           f"Don't forget to check your spam or junk folder if need be. "
                           f"Please follow the instructions in that message to join in the fun.")

    context = {'header': "Invitation sent!", 'email': email}
    return render(request, "users/base.html", context)


def join_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            return redirect('login')
        return confirm_or_login(request, email)

    context = {
        'form': PendingEmailForm,
        'header': "Join the Community!",
        'button_label': "Join"
    }
    return render(request, "users/join.html", context)


class InviteFriendsView(LoginRequiredMixin, View):

    header = "Invite Friends"
    form = PendingEmailForm()
    card_template = 'users/cards/invite_card.html'
    page_template = 'users/base.html'

    def get(self, request, *args, **kwargs):
        messages.info(request, "Enter your friends' emails to invite them to Commonology!")
        context = self._context()
        return render(request, self.page_template, context)

    def post(self, request, *args, **kwargs):
        emails = request.POST['email'].split(",")
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
            except (User.DoesNotExist):
                remove_pending_email_invitations()
                pe = PendingEmail(email=email, referrer=request.user.email)
                pe.save()
                send_invite(request, pe)
                messages.info(request, f"Invite successfully sent to {email}.")

        return render(request, "users/base.html", self._context())

    def _context(self):
        self.form.fields['email'].widget.attrs['class'] = 'w3-input w3-border'
        context = {
            'header': self.header,
            'form': self.form,
            'card_template': self.card_template
        }
        return context


class EmailConfirmedView(View):

    def get(self, request, uidb64, *args, **kwargs):
        try:
            pe = PendingEmail.objects.filter(uuid__exact=uidb64).first()
            if pe is None:
                return self._join_fail(request)

            email = pe.email

            try:
                User.objects.get(email=email)
                return redirect('login/', msg='You already have an account.')
            except User.DoesNotExist:
                form = JoinForm(initial={'email': pe.email, 'referrer': pe.referrer})
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
        messages.info(request, "We've emailed you instructions for setting your password, "
                      "if an account exists with the email you entered. You should receive them shortly.")
        messages.info(request, "If you don't receive an email, please make sure you've entered the address"
                      " you registered with, and check your spam folder")

        context = {'header': "Reset Password"}
        return render(request, 'users/base.html', context)

    def post(self, request, *args, **kwargs):
        return redirect('/login/')


class PwdResetConfirmView(PasswordResetConfirmView):

    def post(self, request, *args, **kwargs):
        self.success_url = reverse('login')
        if self.form_valid:
            messages.info(request, "Your password has been successfully changed.")
        else:
            messages.warning(request, "There was an error updating your password, please try again.")
        return super().post(request, args, kwargs)
