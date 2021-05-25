import datetime
import pytz
from django.conf import settings

import redis
import fakeredis


if settings.IS_TEST:
    REDIS = fakeredis.FakeStrictRedis()
else:
    REDIS = redis.Redis(host='localhost', port=6379, db=0)


def our_now():
    # This results in a time that can be compared values in our database
    # even if saved by a human entering wall clock time into an admin field.
    # This is in the time zone specified in settings, for us it is 'America/New_York'.
    return datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))


def redis_delete_patterns(*patterns):
    """
    Accepts positional arguments of patterns and deletes all matching keys with trailing wildcard
    """
    total_keys_deleted = 0
    for p in patterns:
        keys = REDIS.keys(f'{p}*')
        if keys:
            REDIS.delete(*keys)
            total_keys_deleted += len(keys)
    return total_keys_deleted
