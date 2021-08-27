import time

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, Category, Header
from users.utils import sign_user, unsubscribe
import logging


logger = logging.getLogger(__name__)


def make_substitutions(e, code):
    x = sign_user(e, code)
    url = mark_safe(f"https://{settings.DOMAIN}/unsubscribe/{x}")
    game_url_args = f'r={code}'
    return {'-email-': e, '-unsubscribelink-': url, '-game_url_args-': game_url_args}


#
# Really good examples: https://github.com/sendgrid/sendgrid-python/blob/main/examples/helpers/mail_example.py
#
def sendgrid_send(subject, msg, email_list,
                  from_email=(settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_EMAIL_NAME),
                  send_at=None, categories=None, unsub_link=False, components=()):

    msg = render_to_string('mail/mail_base.html', context={'message': mark_safe(msg), 'components': components, 'unsub_link': unsub_link})

    # don't use sendgrid backend for tests
    if 'console' in settings.EMAIL_BACKEND or 'locmem' in settings.EMAIL_BACKEND:
        to_emails = [e for e, _ in email_list]
        send_mail(subject, msg, None, to_emails, html_message=msg)
        return len(to_emails), msg

    to_emails = [To(email=e, substitutions=make_substitutions(e, code)) for e, code in email_list]

    message = Mail(
        from_email=from_email,
        subject=subject,
        to_emails=to_emails,
        plain_text_content='Game is on.',
        html_content=msg,
        is_multiple=True)

    if send_at:
        message.send_at = send_at
    if unsub_link:
        message.header = Header("List-Unsubscribe", "<-unsubscribelink->")
    if categories:
        message.category = [Category(i) for i in categories]

    sendgrid_client = SendGridAPIClient(settings.EMAIL_HOST_PASSWORD)
    sendgrid_client.send(message)
    return len(to_emails), msg


def mass_mail(subject, msg, from_email, players, categories=None, components=()):
    if categories:
        categories = categories.split(', ')

    qs = players.filter(subscribed=True).all()

    # First batch in 10 seconds to be sure api call is received before that time.
    send_at = int(time.time()) + 10
    count = 0
    email_list = []
    total_count = 0
    for p in qs:
        count += 1
        email_list.append((p.email, p.code))

        if 0 == count % 500:
            total_count += 500
            sendgrid_send(subject, msg, email_list, from_email,
                          send_at=send_at, categories=categories, unsub_link=True, components=components)
            send_at += 100
            count = 0
            email_list = []

    if email_list:
        total_count += len(email_list)
        sendgrid_send(subject, msg, email_list, from_email,
                      send_at=send_at, categories=categories, unsub_link=True, components=components)

    logger.info(f"{total_count} recipients were just sent a blast with subject = {subject}.")
    return total_count


def deactivate_blocked_addresses():
    # https://github.com/sendgrid/sendgrid-python/blob/main/examples/suppression/suppression.py
    # https://github.com/sendgrid/sendgrid-python/blob/main/USAGE.md#suppression
    # https://sendgrid.api-docs.io/v3.0/bounces-api/retrieve-all-bounces

    sg = SendGridAPIClient(settings.EMAIL_HOST_PASSWORD)

    response = sg.client.suppression.blocks.get()
    assert(response.status_code == 200)

    for i in response.to_dict:
        unsubscribe(i['email'], i['reason'])

    response = sg.client.suppression.spam_reports.get()
    assert (response.status_code == 200)
    for i in response.to_dict:
        unsubscribe(i['email'], 'our mail was reported as spam')

    response = sg.client.suppression.invalid_emails.get()
    assert (response.status_code == 200)
    for i in response.to_dict:
        unsubscribe(i['email'], 'invalid address')

    response = sg.client.suppression.bounces.get()
    assert (response.status_code == 200)
    for i in response.to_dict:
        unsubscribe(i['email'], i['reason'])

    return
    # only do this in production --- doing this manually for now
    data = {'delete_all': False, 'emails': bad_emails}
    response = sg.client.supression.blocks.delete(request_body=data)
    assert(response.status_code == 200)

    # Need to repeat for spam_reports, invalid_emails, and bounces
