from datetime import datetime, timedelta
from project.utils import quick_cache
from .models import PendingEmail, Player
from django.contrib.auth import get_user_model
from django.core.signing import Signer
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, CHANGE
from django.db.models import Count
from django.utils.timezone import make_aware
from game.models import Series
import logging

logger = logging.getLogger(__name__)


def remove_pending_email_invitations(n=7):
    t = make_aware(datetime.now()) - timedelta(days=n)
    PendingEmail.objects.filter(created__lt=t).delete()


def sign_user(email, id):
    signed_email = Signer().sign(value=email)
    e, x = signed_email.split(':')
    x = ':'.join([str(id), x])
    return x


def unsubscribe(email, reason='user asked'):
    User = get_user_model()
    try:
        u = User.objects.get(email=email)
        if u.subscribed:
            u.subscribed = False
            u.save()
            player_log_entry(u, f"{email} unsubscribed because {reason}.")
    except User.DoesNotExist:
        print(f"Trying to unsubscribe but {email} does not exist.")


def subscribe(email):
    User = get_user_model()
    u = User.objects.get(email=email)
    u.subscribed = True
    u.save()
    player_log_entry(u, f"{email} just subscribed.")


# used in social_auth pipeline
def add_additional_fields(strategy, details, backend, user=None, *args, **kwargs):
    if not user.display_name:
        user.display_name = f"{user.first_name} {user.last_name}".strip()

    user.is_member = True
    user.save()
    Series.objects.get(slug='commonology').players.add(user)


def is_validated(email):
    User = get_user_model()
    try:
        u = User.objects.get(email=email)
    except User.DoesNotExist:
        return None

    if u.is_active:
        return u

    return None


def player_log_entry(player, message):
    return LogEntry.objects.log_action(user_id=player.id,
                                       content_type_id=ContentType.objects.get_for_model(player).pk,
                                       object_id=player.id,
                                       object_repr=str(player.email),
                                       action_flag=CHANGE,
                                       change_message=message)


def get_player(code):
    return Player.objects.filter(_code=code).first()


@quick_cache()
def players_with_referral_badge(threshold=3):
    return Player.objects.annotate(
        ref_count=Count("referrals")).filter(ref_count__gte=threshold).values_list("id", flat=True)
