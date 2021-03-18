from datetime import datetime, timedelta
from .models import PendingEmail


def remove_pending_email_invitations(n=7):
    t = datetime.now() - timedelta(days=n)
    PendingEmail.objects.filter(created__lt=t).delete()


def unsubscribe(email):
    print(f"Unsubscribe not implemented yet: {email}")
