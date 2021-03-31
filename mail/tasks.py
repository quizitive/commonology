from celery import shared_task
from project import settings
from .mailchimp_utils import Mailchimp


@shared_task
def add_to_mailchimp(email, is_subscribed=True):
    mc_client = Mailchimp(settings.MAILCHIMP_SERVER, settings.MAILCHIMP_API_KEY)
    if is_subscribed:
        status_code, status = mc_client.subscribe(email)
    else:
        status_code, status = mc_client.unsubscribe(email)
    print(f"add_to_mailchimp: {status_code}/{status}")