
from datetime import datetime, timedelta

from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.signing import Signer
from django.db.models import Count
from django.utils.timezone import make_aware
from project.utils import quick_cache
from .models import PendingEmail, Player
from rewards.models import MailingAddress
from project.utils import log_entry
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
    r_code = strategy.session.get('r')
    if r_code and user.referrer is None:
        referrer = Player.objects.filter(_code=r_code).first()
        user.referrer = referrer
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
    return log_entry(player, message)


def get_player(code):
    return Player.objects.filter(_code=code).first()


@quick_cache()
def players_with_referral_badge(threshold=3):
    return Player.objects.annotate(
        ref_count=Count("referrals")).filter(ref_count__gte=threshold).values_list("id", flat=True)


@transaction.atomic
def merge_players(from_email, to_email):
    # # Use this to discover related fields
    # for field in Player._meta.get_fields():
    #     print(type(field), ' ', field.name)

    # We'll use the term "unrelated" to mean fields that native to the Player
    # model, i.e. not a foreign table or ManyToMany or ManyToOne fields.

    def merge_unrelated_fields(f, t):

        # skip id, password, last_login, is_superuser, is_staff, email, _code, data
        if f.is_active:
            t.is_active = True

        if f.date_joined < t.date_joined:
            t.date_joined = f.date_joined

        if not t.first_name and f.first_name:
            t.first_name = f.first_name

        if not t.last_name and f.last_name:
            t.last_name = f.last_name

        if not t.location and f.location:
            t.location = f.location

        if not t.birth_date and f.birth_date:
            t.birth_date = f.birth_date

        if f.subscribed:
            t.subscribed = True

        if f.reminder:
            t.reminder = True

        if f.referrer and not t.referrer:
            t.referrer = f.referrer

        if f.display_name and not t.display_name:
            t.display_name = f.display_name

        if f.is_member:
            t.is_member = True

        t.save()

    def merge_related_fields(from_p, to_p):
        to_p.answers.set(from_p.answers.all())

        to_p.rank_scores.set(from_p.rank_scores.all())

        to_p.referrals.set(from_p.referrals.all())

        PendingEmail.objects.filter(email=from_p.email).delete()

        to_p.comments.set(from_p.comments.all())

        to_p.following.set(from_p.following.all())

        to_p.followers.set(from_p.followers.all())

        to_p.owned_series.set(from_p.owned_series.all())

        to_p.hosted_games.set(from_p.hosted_games.all())

        to_p.claim_set.set(from_p.claim_set.all())

        to_p.request_set.set(from_p.request_set.all())

        try:
            to_p.mailingaddress.set(from_p.mailingaddress.all())
        except MailingAddress.DoesNotExist:
            pass

    from_p = Player.objects.get(email=from_email)
    to_p = Player.objects.get(email=to_email)

    merge_related_fields(from_p, to_p)
    merge_unrelated_fields(from_p, to_p)
    from_p.is_active = False
    from_p.subscribed = False
    from_p.is_member = False
    from_p.reminder = False
    from_p.save()
    player_log_entry(from_p, f'Deactivated and moved to {to_p}')
    player_log_entry(to_p, f'{from_p} merged into {to_p}')
