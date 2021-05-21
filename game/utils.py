from project.utils import our_now
import string
import random
import datetime

from project.utils import REDIS


# Get next game start or game end
def next_event():
    now = our_now()
    if now.weekday() in (3, 4) or (now.weekday() == 2 and now.hour >= 12):
        return 'The game ends in...', next_friday_1159(now).strftime("%Y-%m-%dT%H:%M:%S")
    return 'The next game begins in...', next_wed_noon(now).strftime("%Y-%m-%dT%H:%M:%S")


def next_wed_noon(now):
    next_wed = now
    while next_wed.weekday() != 2:
        next_wed = next_wed + datetime.timedelta(1)
    return next_wed.replace(hour=12, minute=00, second=00)


def next_friday_1159(now):
    next_fri = now
    while next_fri.weekday() != 4:
        next_fri = next_fri + datetime.timedelta(1)
    return next_fri.replace(hour=23, minute=59, second=59)


def create_key(k=7):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=k))


def clear_redis_trailing_wildcard(*patterns):
    """
    Accepts positional arguments of tuples, constructs a prefix with underscores,
    and deletes all matching keys with trailing wildcard
    e.g. clear_with_trailing_wildcard(('leaderboard', '32'), ('leaderboard','commonology','33'))
        => leaderboard_32*, leaderboard_commonology_33*
    """
    for p in patterns:
        prefix = "_".join(p)
        REDIS.delete(*REDIS.keys(f'{prefix}*'))
