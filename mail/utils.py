from django.conf import settings
from mail.sendgrid_utils import sendgrid_send


def make_absolute_urls(txt):
    domain = settings.DOMAIN
    urlroot = f"https://{domain}"
    items = ['/media/ckeditor_uploads/']
    for i in items:
        txt = txt.replace(i, f"{urlroot}{i}")
    return txt


def send_one(player, subject, note):
    sendgrid_send(subject, note, [(player.email, player.code)])
