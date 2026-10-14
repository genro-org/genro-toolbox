"""Bounded exhaustive checks for column/tuple alignment, including fetched rows.

Malformed initial rows are rejected; later shared-index growth remains supported.
"""

import itertools
import random
import sqlite3
from copy import deepcopy

import pytest

from genro_toolbox import NamedList

# Every ordered schema of 0..6 columns drawn from three aliases (1,093 schemas).
# Distinct position values expose swaps/overwrites even when aliases coincide.
SCHEMAS = [
    schema for width in range(7) for schema in itertools.product(("a", "b", "c"), repeat=width)
]
DUPLICATE_SCHEMAS = [schema for schema in SCHEMAS if len(set(schema)) < len(schema)]
UNIQUE_SCHEMAS = [
    schema for width in range(5) for schema in itertools.permutations(("a", "b", "c", "d"), width)
]


def make_row(schema, values):
    """Construct the name index exactly as an adapter does from cursor columns."""
    return NamedList({name: position for position, name in enumerate(schema)}, values)


@pytest.mark.parametrize("schema", SCHEMAS, ids=lambda schema: "-".join(schema) or "empty")
def test_every_schema_is_aligned_or_rejected_at_construction(schema):
    values = tuple(range(100, 100 + len(schema)))
    if len(set(schema)) != len(schema):
        with pytest.raises(ValueError, match="index positions"):
            make_row(schema, values)
        return
    row = make_row(schema, values)
    expected = dict(zip(schema, values, strict=True))
    assert tuple(row) == row.values() == values
    assert row[:] == list(values)
    assert len(row) == len(values)
    for position, value in enumerate(values):
        assert row[position] == value
        assert row[position - len(values)] == value
    for name, value in expected.items():
        assert row[name] == row.get(name) == value
    assert dict(row.iteritems()) == dict(row) == expected
    assert row.extractValues(list(expected)) == list(expected.values())
    assert row.keys() == list(schema)
    assert row.items() == list(zip(schema, values, strict=True))
    sibling = NamedList(row._index, values)
    row["extra"] = 99
    assert tuple(row) == values + (99,)
    assert tuple(sibling) == values
    assert sibling["extra"] is None


@pytest.mark.parametrize("schema", DUPLICATE_SCHEMAS, ids=lambda schema: "-".join(schema))
def test_every_duplicate_schema_is_rejected_even_without_initial_values(schema):
    index = {name: position for position, name in enumerate(schema)}
    before = dict(index)
    with pytest.raises(ValueError, match="index positions"):
        NamedList(index)
    assert index == before


@pytest.mark.parametrize("schema", UNIQUE_SCHEMAS, ids=lambda schema: "-".join(schema) or "empty")
@pytest.mark.parametrize("container", [list, tuple, iter])
def test_unique_columns_all_row_lengths_and_index_insertion_orders(schema, container):
    index = {schema[position]: position for position in reversed(range(len(schema)))}
    for size in range(len(schema) + 3):
        values = container(range(size))
        if size != len(schema):
            before = dict(index)
            with pytest.raises(ValueError, match="values length"):
                NamedList(index, values)
            assert index == before
            continue
        row = NamedList(index, values)
        expected = dict(zip(schema, range(size), strict=True))
        assert row._index is index
        assert tuple(row) == row.values() == tuple(range(size))
        assert row.keys() == list(schema)
        assert dict(row) == expected
        assert row.extractValues(schema) == list(expected.values())
        assert row.items() == list(expected.items())
        assert list(row.iteritems()) == list(reversed(list(expected.items())))


SQL_CASES = [
    ("SELECT 10 AS x, 20 AS x", (10, 20), {"x": 1}),
    ("SELECT 1 AS id, 10 AS x, 20 AS x", (1, 10, 20), {"id": 0, "x": 2}),
    ("SELECT 10 AS x, 20 AS x, 1 AS id", (10, 20, 1), {"x": 1, "id": 2}),
    ("SELECT 10 AS x, 20 AS y, 30 AS x", (10, 20, 30), {"x": 2, "y": 1}),
    ("SELECT 10 AS x, 20 AS x, 30 AS x", (10, 20, 30), {"x": 2}),
    ("SELECT NULL AS x, 20 AS x", (None, 20), {"x": 1}),
    ("SELECT 10 AS x, NULL AS x", (10, None), {"x": 1}),
    ("SELECT 10 AS x, 20 AS y", (10, 20), {"x": 0, "y": 1}),
]


@pytest.mark.parametrize("sql, expected_tuple, expected_index", SQL_CASES)
def test_real_sqlite_fetch_rejects_repeated_aliases(sql, expected_tuple, expected_index):
    with sqlite3.connect(":memory:") as connection:
        cursor = connection.execute(sql)
        fetched = cursor.fetchone()
        index = {column[0]: position for position, column in enumerate(cursor.description)}
    assert index == expected_index
    assert fetched == expected_tuple
    if len(index) < len(fetched):
        with pytest.raises(ValueError, match="index positions"):
            NamedList(index, fetched)
        assert fetched == expected_tuple and index == expected_index
    else:
        row = NamedList(index, fetched)
        assert tuple(row) == row.values() == fetched
        assert dict(row) == {name: fetched[position] for name, position in index.items()}
        row["extra"] = "new"
        assert tuple(row) == fetched + ("new",)


@pytest.mark.parametrize("fetch_method", ["fetchmany", "fetchall"])
def test_duplicate_alias_in_result_is_rejected_before_any_row_is_built(fetch_method):
    with sqlite3.connect(":memory:") as connection:
        cursor = connection.execute("SELECT 10 AS x, 20 AS x, 1 AS id UNION ALL SELECT 30, 40, 2")
        index = {column[0]: position for position, column in enumerate(cursor.description)}
        fetched = cursor.fetchmany(2) if fetch_method == "fetchmany" else cursor.fetchall()
    rows = []
    with pytest.raises(ValueError, match="index positions"):
        for values in fetched:
            rows.append(NamedList(index, values))
    assert rows == []
    assert index == {"x": 1, "id": 2}
    assert fetched == [(10, 20, 1), (30, 40, 2)]


def test_renaming_aliases_before_construction_keeps_every_column_independent():
    # This is what the original test called "duplicates": already unique names.
    row = make_row(("x", "x[2]", "id"), (10, 20, 1))
    row["extra"] = 99
    assert dict(row) == {"x": 10, "x[2]": 20, "id": 1, "extra": 99}
    assert tuple(row) == row.values() == (10, 20, 1, 99)


@pytest.mark.parametrize("seed", range(20))
def test_repeated_valid_mutations_keep_shared_results_aligned(seed):
    rng = random.Random(seed)
    names = ["a", "b", "c"]
    index = {name: position for position, name in enumerate(names)}
    rows = [NamedList(index, [None] * 3) for _ in range(4)]
    expected = [dict.fromkeys(names) for _ in rows]
    for step in range(100):
        target = rng.randrange(len(rows))
        if step % 9 == 0:
            name = f"new_{step}"
            names.append(name)
            for values in expected:
                values[name] = None
        else:
            name = rng.choice(names)
        value = rng.choice([None, step, f"value_{step}", (step, seed)])
        if step % 3 == 0:
            rows[target][name] = value
        elif step % 3 == 1:
            rows[target][names.index(name)] = value
        else:
            rows[target].update({name: value})
        expected[target][name] = value
        for row, values in zip(rows, expected, strict=True):
            assert dict(row) == values
            assert row.values() == tuple(values.values())
            assert tuple(row) == tuple(values.values())[: len(row)]
            assert row.keys() == names
        if step % 13 == 0:
            rows = deepcopy(rows)
            assert all(row._index is rows[0]._index for row in rows)


def test_regression_duplicate_dict_conversion_is_prevented_at_construction():
    with pytest.raises(ValueError, match="index positions"):
        make_row(("x", "x", "id"), (10, 20, 1))


def test_regression_initial_unnamed_values_are_rejected_before_field_addition():
    # Even if the caller compacts the index after losing a duplicate alias,
    # the remaining tuple values must not be accepted and overwritten later.
    with pytest.raises(ValueError, match=r"values length \(3\).*index length \(2\)"):
        NamedList({"x": 0, "id": 1}, (10, 20, 1))


def test_regression_new_shared_field_is_empty_in_untouched_row():
    first = make_row(("x", "x[2]", "id"), (10, 20, 1))
    second = NamedList(first._index, (30, 40, 2))
    first["extra"] = 99
    assert second["extra"] is None
    assert first["id"] == 1 and second["id"] == 2
    assert tuple(first) == (10, 20, 1, 99)
    assert tuple(second) == (30, 40, 2)
