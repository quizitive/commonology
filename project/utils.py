import datetime
import pytz
import functools
from django.conf import settings
from django.core.cache import caches


REDIS = caches['default']
if settings.IS_TEST:
    REDIS.key_prefix += '_test'


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
            REDIS.delete_many(keys)
            total_keys_deleted += len(keys)
    return total_keys_deleted


def quick_cache(func):
    """
    A decorator to cache the result of any function by its name and arguments. Example usage:

    @quick_cache
    def foo(a, b):
        return a + b

    foo(1, 2) ->  check redis for key `foo:1_2`, return cache result if found, otherwise execute foo and set value
    foo(1, 2, timeout=60 * 60) -> same as above, set explicit timeout
    foo(1, 2, force_refresh=True) -> always execute foo and set value, default timeout
    foo(1, 2, force_refresh=True, timeout=60 * 60) -> also works

    NOTE: Make sure arguments are unique! If passing a model instance, make
    sure the model has a unique __repr__ defined.
    """

    @functools.wraps(func)
    def wrapper(*args, force_refresh=False, timeout=600, **kwargs):
        redis_key = f'{func.__name__}:' + "_".join([repr(a) for a in args]) + "_".join(repr(k) for k in kwargs.values())
        if not force_refresh:
            cached_res = REDIS.get(redis_key)
            if cached_res:
                return cached_res
        res = func(*args, **kwargs)
        REDIS.set(redis_key, res, timeout=timeout)
        return res

    return wrapper
