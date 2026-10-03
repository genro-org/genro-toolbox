"""
Dictionary utilities for Genro-Toolbox.

Provides utilities for dict manipulation used across the library.
"""

from collections.abc import Callable, Mapping
from typing import Any

_RESERVED_ATTR_NAMES = ["class"]


def filtered_dict(
    data: Mapping[str, Any] | None,
    filter_fn: Callable[[str, Any], bool] | None = None,
) -> dict[str, Any]:
    """
    Return a dict filtered through ``filter_fn``.

    Args:
        data: Mapping with the original values (can be None).
        filter_fn: Optional callable receiving ``(key, value)`` and returning
            True if the pair should be kept. When None, the mapping is copied.
    """
    if not data:
        return {}
    if filter_fn is None:
        return dict(data)
    return {k: v for k, v in data.items() if filter_fn(k, v)}


def dictExtract(source_dict, prefix, pop=False, slice_prefix=True):
    """Return a dict of the items with keys starting with prefix.

    :param source_dict: source dictionary
    :param prefix: the prefix of the items you need to extract
    :param pop: removes the items from the source dictionary
    :param slice_prefix: shortens the keys of the output dict removing the prefix
    :returns: a dict of the items with keys starting with prefix"""

    lprefix = len(prefix) if slice_prefix else 0

    extract_fn = source_dict.pop if pop else source_dict.get
    return {
        k[lprefix:] if k[lprefix:] not in _RESERVED_ATTR_NAMES else f"_{k[lprefix:]}": extract_fn(k)
        for k in list(source_dict.keys())
        if k.startswith(prefix)
    }
