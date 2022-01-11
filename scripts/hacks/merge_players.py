
import sys
import os
import django
from django.db import transaction


path = os.getcwd()
sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()


from users.models import Player, PendingEmail
from rewards.models import MailingAddress
from users.utils import player_log_entry
from chat.models import Comment


# # Use this to discover related fields
# for field in Player._meta.get_fields():
#     print(type(field), ' ', field.name)

# We'll use the term "unrelated" to mean fields that native to the Player
# model, i.e. not a foreign table or ManyToMany or ManyToOne fields.


from_email = 'sherri.sweren@gmail.com'
to_email = 'sherri@sweren.com'

from_p = Player.objects.get(email=from_email)
to_p = Player.objects.get(email=to_email)


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

    to_p.referrals.set(from_p.referrals.all())

    PendingEmail.objects.filter(email=from_email).delete()

    to_p.comments.set(from_p.comments.all())

    to_p.following.set(from_p.following.all())

    to_p.followers.set(from_p.followers.all())

    to_p.owned_series.set(from_p.owned_series.all())

    to_p.hosted_games.set(from_p.hosted_games.all())

    to_p.games_won.set(from_p.games_won.all())

    to_p.claim_set.set(from_p.claim_set.all())

    try:
        to_p.mailingaddress.set(from_p.mailingaddress.all())
    except MailingAddress.DoesNotExist:
        print("There is no mailing address.")


@transaction.atomic
def do_it():
    print(from_p)
    print(to_p)
    merge_related_fields(from_p, to_p)
    merge_unrelated_fields(from_p, to_p)
    from_p.is_active = False
    from_p.subscribed = False
    from_p.is_member = False
    from_p.reminder = False
    from_p.save()
    player_log_entry(from_p, f'Deactivated and moved to {to_p}')
    player_log_entry(to_p, f'{from_p} merged into {to_p}')


do_it()
