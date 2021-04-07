from datetime import datetime, timedelta
from .models import PendingEmail
from django.contrib.auth import get_user_model
from mail.tasks import update_mailing_list


def remove_pending_email_invitations(n=7):
    t = datetime.now() - timedelta(days=n)
    PendingEmail.objects.filter(created__lt=t).delete()


def unsubscribe(email):
    User = get_user_model()
    u = User.objects.get(email=email)
    u.subscribed = False
    u.save()
    update_mailing_list.delay(email, is_subscribed=False)
