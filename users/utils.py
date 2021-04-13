from datetime import datetime, timedelta
from .models import PendingEmail
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)


def remove_pending_email_invitations(n=7):
    t = datetime.now() - timedelta(days=n)
    PendingEmail.objects.filter(created__lt=t).delete()


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
