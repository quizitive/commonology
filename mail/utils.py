from django.conf import settings
from .mailchimp_utils import Mailchimp


def get_mc_client():
    print(settings.MAILCHIMP_EMAIL_LIST_ID)
    return Mailchimp(settings.MAILCHIMP_SERVER,
                     settings.MAILCHIMP_API_KEY,
                     list_id=settings.MAILCHIMP_EMAIL_LIST_ID)
