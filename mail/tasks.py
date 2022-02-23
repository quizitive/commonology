from celery import shared_task
from django.template.loader import render_to_string
from components.models import SponsorComponent
from mail.utils import sendgrid_send


@shared_task(queue='serial')
def mail_task(subject, msg, email_list, top_components=(), bottom_components=()):
    sendgrid_send(subject, msg, email_list, top_components=top_components, bottom_components=bottom_components)


def send_refer_thankyou(player):
    msg = render_to_string('mail/refer_thankyou_email.html', {'player': player.name})
    return mail_task("Thank you for the referral.", msg, [(player.referrer.email, None)])
