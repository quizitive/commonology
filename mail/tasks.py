import time
from django.db import connection
from celery import shared_task
from .utils import get_mc_client
from .sendgrid_utils import sendgrid_send
import logging

logger = logging.getLogger(__name__)


def update_mailing_list_subscribed(email, subscribed=True):

    # Do not call API for tests
    if connection.settings_dict['NAME'].startswith('test_'):
        return

    if subscribed:
        update_mailing_list.delay(email, action='subscribe')
    else:
        update_mailing_list.delay(email, action='archived')


@shared_task(queue='serial')
def update_mailing_list(email, action='subscribe'):
    mc_client = get_mc_client()

    if 'subscribe' == action:
        status_code, status = mc_client.subscribe(email)
    elif 'unsubscribe' == action:
        status_code, status = mc_client.unsubscribe(email)
    else:
        status = 'archived'
        status_code = mc_client.archive(email)

    msg = f"{email} is {status} in Mailchimp with {status_code}"
    if status_code in (200, 204):
        logger.info(msg)
    else:
        logger.error(msg)


@shared_task(queue='serial')
def mass_mail(subject, msg, from_email, email_list=None):
    if email_list:
        sendgrid_send(subject, msg, email_list, from_email)
        print(msg)
        print(from_email)
        print(email_list)
    else:
        t = int(time.time())
