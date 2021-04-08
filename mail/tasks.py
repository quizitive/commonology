from celery import shared_task
from .utils import get_mc_client
import logging

logger = logging.getLogger(__name__)


@shared_task(queue='serial')
def update_mailing_list(email, is_subscribed=True):
    mc_client = get_mc_client()

    if is_subscribed:
        status_code, status = mc_client.subscribe(email)
    else:
        status_code, status = mc_client.unsubscribe(email)

    msg = f"{email} is {status} in Mailchimp with {status_code}"
    if 200 == status_code:
        logger.info(msg)
    else:
        logger.error(msg)
