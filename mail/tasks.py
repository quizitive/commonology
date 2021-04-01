from celery import shared_task
from project import settings
from .mailchimp_utils import Mailchimp
import logging

logger = logging.getLogger(__name__)


@shared_task
def add_to_mailchimp(email, is_subscribed=True):
    mc_client = Mailchimp(settings.MAILCHIMP_SERVER,
                          settings.MAILCHIMP_API_KEY,
                          list_id=settings.MAILCHIMP_EMAIL_LIST_ID)
    if is_subscribed:
        status_code, status = mc_client.subscribe(email)
        logger.info(f"{email} is subcribed in Mailchimp with {status_code} / {status}")

    else:
        status_code, status = mc_client.unsubscribe(email)
        logger.info(f"{email} is unsubcribed in Mailchimp with {status_code} / {status}")
