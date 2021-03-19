import os
import uuid
from django.forms import HiddenInput
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
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
        User.objects.get(email=email)
        return redirect('login/', msg='You already have an account.')
    except (User.DoesNotExist):
        remove_pending_email_invitations()
        pe = PendingEmail(email=email)
        pe.save()
        send_invite(request, pe)
        return render(request, "users/confirm_sent.html", context={'email': email})


def join_view(request):
    flag = os.environ.get('INHIBIT_JOIN_VIEW', 'False')
    if flag.lower() == 'true':
        return redirect('/')

    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        email = request.POST['email']
        return confirm_or_login(request, email)

    context = {'form': PendingEmailForm}
    return render(request, "users/join.html", context)


@login_required()
def send_invite_view(request):
    print(f"Marc Schwarzschild - entering send_invite_view.")
    if request.method == 'POST':
        email = request.POST['email']
        context = {"email": email}
        try:
            User.objects.get(email=email)
            print(f"Marc Schwarzschild - {email} has account already.")
            return render(request, "users/has_account.html", context)
        except (User.DoesNotExist):
            remove_pending_email_invitations()
            pe = PendingEmail(email=email, referrer=request.user.email)
            pe.save()
            print(f"Marc Schwarzschild - Just saved {email} to PendingUsers.")
            send_invite(request, pe)
            return render(request, "users/invite_sent.html", context)

        return redirect('/')

    print(f"Marc Schwarzschild - leaving as get send_invite_view.")
    context = {'form': PendingEmailForm}
    return render(request, "users/invite.html", context)


def email_confirmed_view(request, uidb64):
    uidb64 = uuid.UUID(uidb64)
    if request.method == 'POST':
        form = JoinForm(request.POST)
        if form.is_valid():
            email = request.POST['email']

            pe = PendingEmail.objects.filter(email__exact=email).filter(uuid=uidb64).first()

            if pe is None:
                return render(request, "users/join_fail.html")

            user = form.save(commit=False)
            user.referrer = pe.referrer
            user.save()
            raw_password = form.clean_password2()
            user = authenticate(email=user.email, password=raw_password)
            login(request, user)
            PendingEmail.objects.filter(email__iexact=user.email).delete()
            return redirect('/')
        return render(request, "users/register.html", {"form": form})

    try:
        pe = PendingEmail.objects.filter(uuid__exact=uidb64).first()
        if pe is None:
            return render(request, "users/join_fail.html")

        email = pe.email

        try:
            User.objects.get(email=email)
            return redirect('login/', msg='You already have an account.')
        except (User.DoesNotExist):
            form = JoinForm(initial={'email': pe.email, 'referrer': pe.referrer})
            form.fields['email'].widget.attrs['readonly'] = True
            form.fields['email'].widget = HiddenInput()
            return render(request, "users/register.html", {"form": form, "email": email})

    except PendingEmail.DoesNotExist:
        return render(request, "users/join_fail.html")
    except ValidationError:
        return render(request, "users/join_fail.html")


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
