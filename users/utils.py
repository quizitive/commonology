from datetime import datetime, timedelta
from .models import PendingEmail
from django.contrib.auth import get_user_model
from django.core.signing import Signer
import logging

logger = logging.getLogger(__name__)


def remove_pending_email_invitations(n=7):
    t = datetime.now() - timedelta(days=n)
    PendingEmail.objects.filter(created__lt=t).delete()


def sign_user(email, id):
    signed_email = Signer().sign(value=email)
    e, x = signed_email.split(':')
    x = ':'.join([str(id), x])
    return x


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


# used in social_auth pipeline
def add_display_name(strategy, details, backend, user=None, *args, **kwargs):
    if not user.display_name:
        user.display_name = f"{user.first_name} {user.last_name}".strip()
        user.save()
