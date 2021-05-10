from django.conf import settings


def make_absolute_urls(txt):
    domain = settings.DOMAIN
    urlroot = f"https://{domain}"
    items = ['/media/ckeditor_uploads/']
    for i in items:
        txt = txt.replace(i, f"{urlroot}{i}")
    return txt
