from datetime import datetime, timedelta
from .models import PendingEmail
from django.contrib.auth import get_user_model
from django.core.signing import Signer
import logging

logger = logging.getLogger(__name__)


def remove_pending_email_invitations(n=7):
    t = datetime.now() - timedelta(days=n)
    PendingEmail.objects.filter(created__lt=t).delete()


def make_unsubscribe_link(request, u):
    signed_email = Signer().sign(value=u.email)
    e, x = signed_email.split(':')
    x = ':'.join([str(u.id), x])
    url_root = request.build_absolute_uri('unsubscribe')
    return f"{url_root}/{x}"


def unsubscribe(email):
    User = get_user_model()
    u = User.objects.get(email=email)
    u.subscribed = False
    u.save()
    logger.info(f"{email} just unsubscribed.")


def subscribe(email):
    User = get_user_model()
    u = User.objects.get(email=email)
    u.subscribed = True
    u.save()
    logger.info(f"{email} just subscribed.")
