"""
Genro-Toolbox - Essential utilities for the Genro ecosystem (Genro Kyō).

A lightweight, zero-dependency library providing core utilities.
"""

__version__ = "0.16.0"

from .decorators import extract_kwargs, metadata
from .dict_utils import dictExtract
from .signing import SignatureError, SignatureExpired, sign, verify
from .smartasync import (
    SmartLock,
    is_async_context,
    reset_smartasync_cache,
    set_async,
    set_sync,
    smartasync,
    smartawait,
    smartcontinuation,
)
from .smartretry import RETRY_PRESETS, retry_call, smartretry
from .smarttimer import cancel_timer, set_interval, set_timeout
from .string_utils import smartsplit
from .tags_match import RuleError, tags_match
from .typeutils import is_awaitable, safe_is_instance
from .uid import get_uuid

__all__ = [
    "extract_kwargs",
    "metadata",
    "dictExtract",
    "safe_is_instance",
    "is_awaitable",
    "tags_match",
    "RuleError",
    "get_uuid",
    "smartasync",
    "smartawait",
    "smartcontinuation",
    "SmartLock",
    "reset_smartasync_cache",
    "is_async_context",
    "set_sync",
    "set_async",
    "smartsplit",
    "set_timeout",
    "set_interval",
    "cancel_timer",
    "smartretry",
    "retry_call",
    "RETRY_PRESETS",
    "sign",
    "verify",
    "SignatureError",
    "SignatureExpired",
]
