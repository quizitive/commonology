import time
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from users.models import Player
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sendgrid.helpers.mail import To

from users.utils import sign_user


def make_substitutions(e, i):
    x = sign_user(e, i)
    url = mark_safe(f"https://{settings.DOMAIN}/unsubscribe/{x}")
    return {'-email-': e, '-unsubscribelink-': url}


def sendgrid_send(subject, msg, email_list,
                  from_email=(settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_EMAIL_NAME),
                  send_at=None):

    to_emails = [To(email=e, substitutions=make_substitutions(e, id)) for e, id in email_list]

    msg = render_to_string('mail/mail_base.html', context={'message': mark_safe(msg)})

    message = Mail(
        from_email=from_email,
        subject=subject,
        to_emails=to_emails,
        plain_text_content='Game is on.',
        html_content=msg,
        is_multiple=True)

    if send_at:
        message.send_at = send_at

    try:
        sendgrid_client = SendGridAPIClient(settings.EMAIL_HOST_PASSWORD)

        response = sendgrid_client.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)


def mass_mail(subject, msg, from_email, email_list=None):
    if email_list:
        sendgrid_send(subject, msg, email_list, from_email)
        print(msg)
        print(from_email)
        print(email_list)
    else:
        qs = Player.objects.all()
        send_at = int(time.time()) + 10
        count = 0
        email_list = []

        # todo: remove these three lines lines
        email_list = [('ms@koplon.com', 33), ('popsalooloo@yahoo.com', 72)]
        sendgrid_send(subject, msg, email_list, from_email, send_at=send_at)
        return

        for p in qs:
            count += 1
            email_list.append((p.email, p.id))

            if 0 == count % 500:
                sendgrid_send(subject, msg, email_list, from_email, send_at=send_at)
                send_at += 900
                count = 0
                email_list = []

        if email_list:
            sendgrid_send(subject, msg, email_list, from_email, send_at=send_at)
