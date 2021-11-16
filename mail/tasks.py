from celery import shared_task
from mail.utils import sendgrid_send


@shared_task(queue='serial')
def mail_task(subject, msg, email_list, components=()):
    sendgrid_send(subject, msg, email_list, components=components)
