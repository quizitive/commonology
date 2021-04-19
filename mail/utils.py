from django.conf import settings
from .mailchimp_utils import Mailchimp


def get_mc_client():
    return Mailchimp(settings.MAILCHIMP_SERVER,
                     settings.MAILCHIMP_API_KEY,
                     list_id=settings.MAILCHIMP_EMAIL_LIST_ID)


def make_absolute_urls(txt):
    domain = settings.DOMAIN
    urlroot = f"https://{domain}"
    items = ['/media/ckeditor_uploads/']
    for i in items:
        txt = txt.replace(i, f"{urlroot}{i}")
    return txt
