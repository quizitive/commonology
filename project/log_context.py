from typing import Generator

from contextlib import contextmanager
from contextvars import ContextVar
import logging


class LogContext(logging.Filter):

    context: ContextVar[dict] = ContextVar("context")

    def filter(self, record) -> bool:
        try:
            for key, val in self.context.get().items():
                if key not in record.__dict__:
                    # Only set the value if it doesn't already exist. This prevents overwriting core
                    # log record attributes such as 'message', 'levelname', etc, and allows
                    # users to override the value set by the context logger in downstream code.
                    setattr(record, key, val)
            return True
        except LookupError:
            # No context set!
            return True


@contextmanager
def log_context(**kwargs) -> Generator[None, None, None]:
    """
    A context manager which injects context-specific information into logs as "extra".

    Example:
        with log_context(foo="bar"):
            logger.info("Hello, world!")

        This will log "Hello, world!" with an extra field "foo" set to "bar".

    These fields can be overridden on individual log messages within the context manager.

    Example:
        with log_context(foo="bar"):
            logger.info("Hello, world!", extra={"foo": "baz"})

        This will log "Hello, world!" with an extra field "foo" set to "baz".
    """
    # get the current context if available, default to a empty dict
    current_context = LogContext.context.get({})
    # sync upstream context with new context
    merge_context = {**current_context, **kwargs}
    try:
        token = LogContext.context.set(merge_context)
        yield
    finally:
        # reset the context variable to the with the merged values
        LogContext.context.reset(token)
