# --------------------------------------------------------------------------
# package       : GenroPy core - see LICENSE for details
# module gnrlist : gnr list implementation
# Copyright (c) : 2004 - 2007 Softwell sas - Milano
# Written by    : Giovanni Porcari, Michele Bertoldi
#                 Saverio Porcari, Francesco Porcari , Francesco Cavazzana
# --------------------------------------------------------------------------
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0; see LICENSE.
# Ported from GenroPy gnrpy/gnr/core/gnrlist.py, commit
# fa35e5adfa6ad1b269f3a22a9b12c4c1ee6513ea.
# Modified 2026-10-14 for genro-toolbox: renamed GnrNamedList to NamedList, replaced
# the GenroPy dependency with its private deprecation decorator, formatted the code,
# removed an unused local and clarified the iteritems docstring.
# Constructor validation rejects inconsistent indices and initial row lengths.
# _deprecated comes from gnrpy/gnr/core/gnrdecorator.py at the same commit.
# ruff: noqa: UP031 - preserve legacy string conversion semantics
# See NOTICE for provenance.

"""Legacy mutable list with named access and a shareable column index.

Only Python's standard library is required. See the named-list user guide for
legacy limitations, especially structural mutations and short rows.
"""

import warnings


def _deprecated(message=None):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used

    :param func: the function to deprecate"""
    message = ": %s" % message if message else ""

    def decore(func):
        def wrapper(*args, **kwargs):
            warnings.warn(
                "Call to deprecated function %s%s" % (func.__name__, message),
                category=DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__dict__.update(func.__dict__)
        return wrapper

    return decore


class NamedList(list):
    """A list-like object that allows access to elements by both index and column name.

    This class combines list and dict-like interfaces, enabling both numeric and named
    access to elements. It's primarily used to represent rows from CSV, Excel, or XML files.

    :param index: dict mapping column names (str) to their position indices (int)
    :param values: optional iterable of initial values ordered according to the index mapping.
                   If None, initializes with None values for all columns.
    :raises ValueError: if positions are not unique plain integers spanning
                       0 through len(index)-1, or the supplied value count differs.

    Example:
        >>> index = {'name': 0, 'age': 1, 'city': 2}
        >>> row = NamedList(index, ['Alice', 30, 'NYC'])
        >>> row[0]           # Access by numeric index
        'Alice'
        >>> row['name']      # Access by column name
        'Alice'
        >>> row['email'] = 'alice@example.com'  # Add new column dynamically
        >>> 'name' in row    # Check column existence
        True

    The index is validated and retained by reference. Later index growth can
    leave other rows sharing it shorter than the index.
    """

    def __init__(self, index, values=None):
        size = len(index)
        positions = list(index.values())
        if any(type(position) is not int for position in positions) or set(positions) != set(
            range(size)
        ):
            raise ValueError("index positions must be unique integers from 0 to len(index) - 1")
        initial_values = [None] * size if values is None else list(values)
        if len(initial_values) != size:
            raise ValueError(
                f"values length ({len(initial_values)}) must match index length ({size})"
            )
        list.__init__(self, initial_values)
        self._index = index

    def __getitem__(self, x):
        if type(x) is int or type(x) is slice:
            return list.__getitem__(self, x)
        else:
            x = self._index[x]
            try:
                return list.__getitem__(self, x)
            except:  # noqa: E722 - preserve legacy exception handling
                if x > len(self._index):
                    raise

    def __contains__(self, what):
        return what in self._index

    def __setitem__(self, x, v):
        if type(x) not in (int, slice):
            n = self._index.get(x)
            if n is None:
                n = len(self._index)
                self._index[x] = n
            x = n
        try:
            list.__setitem__(self, x, v)
        except:  # noqa: E722 - preserve legacy exception handling
            n = len(self._index)
            if x > n:
                raise
            else:
                self.extend([None] * (n - len(self)))
                list.__setitem__(self, x, v)

    def __str__(self):
        return "[%s]" % ",".join(["%s=%s" % (k, v) for k, v in list(self.items())])

    def __repr__(self):
        return "[%s]" % ",".join(["%s=%s" % (k, v) for k, v in list(self.items())])

    def get(self, x, default=None):
        """Get value by column name or index, returning default if not found."""
        try:
            return self[x]
        except:  # noqa: E722 - preserve legacy exception handling
            return default

    def has_key(self, x):
        """Return True if the key is in the index, False otherwise."""
        return x in self._index

    def items(self):
        """Return (key, value) pairs ordered by column position."""
        items = list(self._index.items())
        result = [None] * len(items)
        for k, v in items:
            result[v] = (k, self[v])
        return result

    def iteritems(self):
        """Yield (key, value) pairs in index dictionary insertion order."""
        items = list(self._index.items())
        for k, v in items:
            yield (k, self[v])

    def keys(self):
        """Return column names ordered by position."""
        items = list(self._index.items())
        result = [None] * len(items)
        for k, v in items:
            result[v] = k
        return result

    @_deprecated(message="do not use pop in named tuple")
    def pop(self, x, dflt=None):
        """Remove and return value — deprecated, breaks column index mapping."""
        if type(x) is not int:
            x = self._index[x]
        try:
            return list.pop(self, x)
        except:  # noqa: E722 - preserve legacy exception handling
            if x > len(self._index):
                raise

    def update(self, d):
        """Update values from a dict."""
        for k, v in list(d.items()):
            self[k] = v

    def values(self):
        """Return all values as a tuple."""
        return tuple(self[:] + [None] * (len(self._index) - len(self)))

    def extractItems(self, columns):
        """Extract (key, value) pairs for specified columns (or all if None)."""
        if columns:
            return [(k, self[k]) for k in columns]
        else:
            return list(self.items())

    def extractValues(self, columns):
        """Extract values for specified columns (or all if None)."""
        if columns:
            return [self[k] for k in columns]
        else:
            return list(self.values())
