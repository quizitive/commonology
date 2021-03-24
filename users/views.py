import os
import uuid
from django.forms import HiddenInput
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.views import PasswordResetDoneView
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.views.generic.base import View
from users.forms import PlayerProfileForm, PendingEmailForm, JoinForm
from users.models import PendingEmail

from .utils import remove_pending_email_invitations

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

    return render(request, "users/confirm_sent.html", context={'email': email})


def join_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            return redirect('login')
        return confirm_or_login(request, email)

    context = {'form': PendingEmailForm}
    return render(request, "users/join.html", context)


@login_required()
def send_invite_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        context = {"email": email}
        try:
            User.objects.get(email=email)
            return render(request, "users/has_account.html", context)
        except (User.DoesNotExist):
            remove_pending_email_invitations()
            pe = PendingEmail(email=email, referrer=request.user.email)
            pe.save()
            send_invite(request, pe)
            return render(request, "users/invite_sent.html", context)

        return redirect('/')

    context = {'form': PendingEmailForm}
    return render(request, "users/invite.html", context)


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
        return render(request, 'users/join_fail.html', {})


def make_uuid_url(request, uuid=None):
    url = request.build_absolute_uri('/join/')
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
            referrer_str = f'{referrer.first_name} {referrer.last_name}, whose email address is {referrer.email} requested this invitation.'

        else:
            referrer_str = f'Your friend whose email address is {referrer.email} requested this invitation.'

    context = {'referrer_str': referrer_str, 'join_url': join_url}
    msg = render_to_string('users/invite_email.html', context)

    return send_mail(subject='Join us', message=msg,
                     from_email=None, recipient_list=[email])


class PwdResetDoneView(PasswordResetDoneView):

    def get(self, request, *args, **kwargs):
        messages.info(request, "We've emailed you instructions for setting your password, "
                      "if an account exists with the email you entered. You should receive them shortly.")
        messages.info(request, "If you don't receive an email, please make sure you've entered the address"
                      " you registered with, and check your spam folder")
        return render(request, 'registration/password_reset_done.html')

    def post(self, request, *args, **kwargs):
        return redirect('login')
