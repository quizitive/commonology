import datetime
import pytz
from django.conf import settings

import redis

REDIS = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def our_now():
    # This results in a time that can be compared values in our database
    # even if saved by a human entering wall clock time into an admin field.
    # This is in the time zone specified in settings, for us it is 'America/New_York'.
    return datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
