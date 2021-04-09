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
        # status_code, status = mc_client.unsubscribe(email)
        status = 'archived'
        status_code = mc_client.archive(email)

    msg = f"{email} is {status} in Mailchimp with {status_code}"
    if status_code in (200, 204):
        logger.info(msg)
    else:
        logger.error(msg)
