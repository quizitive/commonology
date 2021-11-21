from celery import shared_task
from mail.utils import sendgrid_send


@shared_task(queue='serial')
def mail_task(subject, msg, email_list, top_components=(), bottom_components=()):
    sendgrid_send(subject, msg, email_list, top_components=top_components, bottom_components=bottom_components)
