# NamedList

Available since version **0.18.0**.

`NamedList` ports the legacy GenroPy `GnrNamedList` subclass of `list`, without GenroPy,
SQL or driver dependencies. It holds mutable values and an explicit mapping
from column names to positions. Cursor handling belongs to the caller.

```python
from genro_toolbox import NamedList

index = {"codice": 0, "totale": 1}
row = NamedList(index, ["ABC", 10])
assert row["codice"] == row[0] == "ABC"
row["totale"] = 20
assert row[1] == 20
row[1] = 30
assert row["totale"] == 30
assert list(row) == ["ABC", 30]
code, total = row
assert dict(row) == {"codice": "ABC", "totale": 30}
```

The class is also available from `genro_toolbox.named_list`.

## Construction and mutation

`NamedList(index, values=None)` validates the input before initializing the row
and retains `index` by reference. Its positions must be unique plain Python
integers covering exactly `0 .. len(index)-1`, in any dictionary insertion
order. Gaps, duplicate positions, negative positions, booleans, floats and
other position types raise `ValueError`.

Omitting `values`, or supplying `None`, creates `len(index)` entries containing
`None`. Otherwise, the iterable is materialized once and its length must equal
`len(index)`; short or long input raises `ValueError` with both lengths.
An empty iterable is valid only with an empty index. Nested values are not
copied. Iteration errors propagate without initializing or changing the row,
and invalid input does not mutate the caller's index.

This is an intentional tightening of the legacy constructor. Rows may still
become shorter later when another row adds names to their shared index.
A newly constructed row must match the index's current size, even if existing
rows sharing it are shorter.

Integer positions, including negative ones, and slices behave like list
access. A slice returns a plain list. Legacy dispatch recognizes exact
`int` and `slice` types: `bool` and subclasses of `int` are treated as index
dictionary keys instead. Named assignment updates an existing position or
adds a new name at `len(index)`, extending this row with `None` as needed.
Positional assignment beyond the physical row can also pad it up to the
index length, but cannot extend it beyond that length.

Iteration, unpacking, `len`, equality and list ordering operate on stored
values. Equality ignores column names: `NamedList({"x": 0}, [1]) == [1]`.
In contrast, `name in row` and `has_key(name)` test names in the index;
`index(value)` and `count(value)` remain list operations on values.

## Methods

| Operation | Legacy behavior |
| --- | --- |
| `get(key, default=None)` | Named or positional access; returns the default on any exception. A stored or implicit `None` does not select the default. |
| `keys()` | A list of column names in position order. |
| `items()` | A list of `(name, value)` pairs in position order, using positional access. |
| `iteritems()` | A generator of pairs in the index dictionary's insertion order, using positional access. |
| `values()` | A tuple of stored values, padded with `None` to the index length; extra values are retained. |
| `update(mapping)` | Assigns each pair from `mapping.items()` by key; returns `None`. |
| `extractItems(columns)` | Requested `(key, value)` pairs in requested order; a falsy argument, including `None` or `[]`, calls `items()`. |
| `extractValues(columns)` | Requested values as a list; a falsy argument returns `list(values())`. |
| `has_key(key)` | Tests index membership. |
| `str(row)`, `repr(row)` | Formats `items()` as `[name=value,...]`, without string quoting. |
| `dict(row)` | Uses `keys()` and named access; preserves column position order. This is an explicit conversion, while ordinary iteration yields values. |

## Shared indices and short rows

```python
index = {"name": 0}
first = NamedList(index, ["Alice"])
second = NamedList(index, ["Bob"])
first["city"] = "Milano"

assert second.keys() == ["name", "city"]
assert second["city"] is None
assert second.get("city", "unknown") is None
assert dict(second) == {"name": "Bob", "city": None}
assert second.values() == ("Bob", None)
assert list(second) == ["Bob"]
assert len(second) == 1

second["city"] = "Roma"  # only this row's storage is extended
assert first["city"] == "Milano"
```

Adding a name affects every row that shares the index, but does not extend
their stored values. On a short row, an indexed name whose position is
missing normally reads as `None`; positional access raises `IndexError`.
Consequently `items()`, consuming `iteritems()`, `extractItems(None)`,
`str()` and `repr()` can raise `IndexError`. `values()`, named extraction
and `dict(row)` can still supply implicit `None` values. These differences
are preserved, not normalized by the port.

## Copying

`copy.deepcopy(row)` copies the values, nested mutable objects and index,
so subsequent mutations do not affect the original row.
`copy.deepcopy(rows)` copies a whole result in one operation and preserves
sharing *inside* that copy: rows that shared one index still share the
copied index; nested values shared by rows remain shared within the copy.
The copied graph is independent of the original. Short rows remain short.
Copying each row with a separate `deepcopy` call does not preserve sharing
between the copies. Inherited `row.copy()` and slicing return plain lists.

## Preserved limitations

- Structural list operations do not maintain the index. Slice assignment,
  `del row[position]`, `remove`, `clear`, `append`, `extend`, `insert`,
  `reverse`, `sort`, `+=` and `*=` can shift, remove or add values without
  updating names. `del row[name]` is unsupported. Use fixed positions or
  named assignment to retain the correspondence.
- `pop(x, dflt=None)` is already deprecated upstream and emits
  `DeprecationWarning`. The position/name argument is required, `dflt` is
  ignored, and the index is never adjusted. Missing names raise `KeyError`;
  out-of-range positions at most `len(index)` (including overly negative
  ones) return `None`, while larger positions raise `IndexError`.
- Duplicate names are not disambiguated. The legacy duplicate-column test
  supplies **already renamed** keys (`value`, `value[2]`, `value[3]`). An index
  built from repeated cursor aliases loses entries and is rejected by the
  constructor, either for invalid positions or a mismatched value count.
- Validation applies at construction. Direct external changes to the shared
  index can still corrupt its positions. The legacy broad exception handlers
  remain in later operations, including `get()` swallowing exceptions.

## Alignment validation and remaining hazards

A cursor executing `SELECT 10 AS x, 20 AS x, 1 AS id` returns `(10, 20, 1)`.
An adapter building an index from its description produces `{"x": 1, "id": 2}`:
two names for three values. Previously, adding another field could overwrite
`id` and expose unrelated values in sibling rows. Construction now fails:

```python
try:
    NamedList({"x": 1, "id": 2}, (10, 20, 1))
except ValueError:
    pass  # Invalid index: position 0 is missing and position 2 is outside it.
```

Even compacting that index to `{"x": 0, "id": 1}` does not accept a three-value
row: the length check rejects it. The constructor cannot recover the original
column names or detect data that the caller has already discarded while also
compacting the index and values. Supply explicit unique names for all columns.

`tests/test_named_list_alignment.py` covers:

- All 1,093 ordered schemas of 0–6 columns drawn from three aliases: valid
  schemas retain every value; duplicate schemas fail during construction.
- Every duplicate schema without initial values, to check index validation
  independently of the value count.
- All permutations of up to four distinct names, reversed index insertion
  order, short/exact/long inputs, and list, tuple and iterator inputs.
- Actual SQLite `fetchone`, `fetchmany` and `fetchall`, adjacent and separated
  duplicate aliases, triplicates, unique trailing columns and `NULL` values.
- Twenty reproducible sequences of 100 assignments, updates, shared-index
  growth and whole-result deepcopies, checked against per-row dictionaries.

`tests/test_named_list_constructor.py` checks malformed positions, empty input,
iterator consumption, failed reinitialization, and the difference between
existing rows shortened by shared-index growth and newly constructed rows.

`tests/test_named_list_errors.py` checks the row and shared index after later
failures. Two safety regressions remain `xfail(strict=True)`: an out-of-range
assignment can pad a row shortened by shared-index growth before raising, and
slice recovery can mask an original error with `TypeError`. These are known
unresolved failures outside constructor validation. Inherited extension with
an interrupted iterator can retain partially appended unnamed values, and
`update()` retains assignments completed before an error.

The three duplicate-alias safety regressions are now ordinary passing tests:
invalid construction is rejected, and adding fields to valid shared rows
preserves existing values. SQLite tests demonstrate the generic container
contract; they are not integration tests of Asqueel drivers.

## Provenance

Ported from [GenroPy at fa35e5adfa6ad1b269f3a22a9b12c4c1ee6513ea](https://github.com/genropy/genropy/tree/fa35e5adfa6ad1b269f3a22a9b12c4c1ee6513ea):
`gnrpy/gnr/core/gnrlist.py`, the deprecation decorator from
`gnrpy/gnr/core/gnrdecorator.py`, and the eight `test_GnrNamedList*` tests in
`gnrpy/tests/core/gnrlist_test.py`. Copyright (c) 2004–2007 Softwell sas,
Milano; authors Giovanni Porcari, Michele Bertoldi, Saverio Porcari,
Francesco Porcari and Francesco Cavazzana. This port is distributed under Apache-2.0; see `LICENSE` and `NOTICE`.

The eight legacy tests were first run successfully against the frozen
source, before introducing the Toolbox implementation. Additional
characterization tests were also checked against that source. The existing
tests had no failures, but left these ambiguities untested: short-row
mapping methods, `iteritems()` insertion order (contrary to its original
docstring), actual duplicate names, structural mutations and deepcopy.
The agreed constructor checks deliberately reject inconsistent initial input
that the legacy accepted. Other legacy behaviors remain characterized by tests.
The implementation changes are the public name `NamedList`, constructor
validation, import isolation, formatting, a private copy of the deprecation
decorator, removal of an unused local, and clarification of the `iteritems()`
docstring. SQL cursor adapters remain outside Toolbox.
