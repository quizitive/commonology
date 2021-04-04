from datetime import datetime, timedelta
from .models import PendingEmail
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login, logout, get_user_model

User = get_user_model()


def remove_pending_email_invitations(n=7):
    t = datetime.now() - timedelta(days=n)
    PendingEmail.objects.filter(created__lt=t).delete()


def unsubscribe(email):
    User = get_user_model()
    u = User.objects.get(email=email)
    u.subscribed = False
    u.save()


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
            referrer_str = f'{referrer.first_name} {referrer.last_name}, ' \
                           f'whose email address is {referrer.email} requested this invitation.'

        else:
            referrer_str = f'Your friend whose email address is {referrer.email} requested this invitation.'

    context = {'referrer_str': referrer_str, 'join_url': join_url}
    msg = render_to_string('users/invite_email.html', context)

    return send_mail(subject='Join us', message=msg,
                     from_email=None, recipient_list=[email])
