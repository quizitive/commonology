import time

import python_http_client.exceptions
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, Category, Header
from users.models import Player
from users.utils import sign_user, unsubscribe
from game.utils import find_latest_active_game

import logging


logger = logging.getLogger(__name__)


def make_absolute_urls(txt):
    domain = settings.DOMAIN
    urlroot = f"https://{domain}"
    items = ['/media/ckeditor_uploads/']
    for i in items:
        txt = txt.replace(i, f"{urlroot}{i}")
    return txt


def send_one(player, subject, note):
    sendgrid_send(subject, note, [(player.email, player.code)])


def make_substitutions(e, code):
    x = sign_user(e, code)
    url = mark_safe(f"https://{settings.DOMAIN}/unsubscribe/{x}")
    game_url_args = f'r={code}'
    return {'-email-': e, '-unsubscribelink-': url, '-game_url_args-': game_url_args}


#
# Really good examples: https://github.com/sendgrid/sendgrid-python/blob/main/examples/helpers/mail_example.py
#
#
def sendgrid_send(subject, msg, email_list,
                  from_email=(settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_EMAIL_NAME),
                  send_at=None, categories=None, unsub_link=False, components=(),
                  force_sendgrid=False):

    msg = render_to_string('mail/mail_base.html', context={'message': mark_safe(msg), 'components': components, 'unsub_link': unsub_link})

    # don't use sendgrid backend for tests
    if (not force_sendgrid) and ('console' in settings.EMAIL_BACKEND or 'locmem' in settings.EMAIL_BACKEND):
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


def mass_mail(obj):
    msg = make_absolute_urls(obj.message)
    from_email = (obj.from_email, obj.from_name)

    if obj.series.slug == 'everyone':
        players = Player.objects
    else:
        players = obj.series.players

    if obj.categories:
        categories = obj.categories.split(', ')
    else:
        categories = []

    components = obj.components.all()

    qs = players.filter(subscribed=True)

    if obj.reminder and (g := find_latest_active_game(obj.series.slug)):
        played_dont_remind = g.players.filter(reminder=False)
        if played_dont_remind:
            qs = qs.exclude(id__in=played_dont_remind)

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
            sendgrid_send(obj.subject, msg, email_list, from_email,
                          send_at=send_at, categories=categories, unsub_link=True, components=components)
            send_at += 100
            count = 0
            email_list = []

    if email_list:
        total_count += len(email_list)
        sendgrid_send(obj.subject, msg, email_list, from_email,
                      send_at=send_at, categories=categories, unsub_link=True, components=components)

    logger.info(f"{total_count} recipients were just sent a blast with subject = {obj.subject}.")
    return total_count


def deactivate_blocked_addresses():
    # https://github.com/sendgrid/sendgrid-python/blob/main/examples/suppression/suppression.py
    # https://github.com/sendgrid/sendgrid-python/blob/main/USAGE.md#suppression
    # https://sendgrid.api-docs.io/v3.0/bounces-api/retrieve-all-bounces

    sg = SendGridAPIClient(settings.EMAIL_HOST_PASSWORD)

    def do():
        response = sg.client.suppression._(name).get()
        assert (response.status_code == 200)
        emails = []
        for i in response.to_dict:
            email = i['email']
            unsubscribe(email, f'our mail was reported in SendGrid {name} suppressions.')
            emails.append(email)
        return emails

    def remove(emails):
        if not emails:
            return

        try:
            response = sg.client.suppression._(name).delete(
                request_body={'delete_all': True})
        except python_http_client.exceptions.NotFoundError:
            f"removing {emails} from Sendgrid suppressions: NOT FOUND"
            return

        print(f"removing {emails} from Sendgrid suppressions: {response.status_code}")

    for name in 'spam_reports', 'bounces', 'invalid_emails', 'blocks':
        emails = do()
        remove(emails)
