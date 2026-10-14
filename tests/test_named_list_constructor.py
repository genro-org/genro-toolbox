"""Constructor validation must reject inconsistent input before publishing it."""

from itertools import product

import pytest

from genro_toolbox import NamedList


@pytest.mark.parametrize("values", [None, [10, 20]])
@pytest.mark.parametrize(
    "positions",
    list(product(range(-1, 4), repeat=2))
    + [(False, 1), (0, True), (0.0, 1), (0, 1.0), ("0", 1), (None, 1), ([], 1), ({}, 1)],
)
def test_index_positions_must_be_unique_plain_integers_covering_every_column(positions, values):
    index = dict(zip(("a", "b"), positions, strict=True))
    if all(type(p) is int for p in positions) and positions in ((0, 1), (1, 0)):
        row = NamedList(index, values)
        assert row._index is index
        assert tuple(row) == ((None, None) if values is None else (10, 20))
    else:
        with pytest.raises(ValueError, match="index positions"):
            NamedList(index, values)
    assert tuple(index.values()) == positions


@pytest.mark.parametrize("values", [None, [], (), iter(())])
def test_empty_index_accepts_only_empty_initial_storage(values):
    index = {}
    row = NamedList(index, values)
    assert row._index is index
    assert tuple(row) == ()
    assert dict(row) == {}


def test_generator_is_consumed_once_and_nested_values_are_not_copied():
    nested = []
    yielded = []

    def values():
        for value in (nested, None):
            yielded.append(value)
            yield value

    row = NamedList({"a": 0, "b": 1}, values())
    assert yielded == [nested, None]
    assert row[0] is nested
    assert row[1] is None


def test_invalid_index_is_rejected_before_consuming_initial_values():
    def values():
        pytest.fail("invalid index must be rejected before consuming values")
        yield 10

    with pytest.raises(ValueError, match="index positions"):
        NamedList({"a": 1}, values())


@pytest.mark.parametrize("index, values", [({"a": 1}, [10]), ({"a": 0}, []), ({}, [10])])
def test_failed_reinitialization_preserves_original_row_and_shared_index(index, values):
    original_index = {"original": 0}
    row = NamedList(original_index, [99])
    sibling = NamedList(original_index, [88])
    with pytest.raises(ValueError):
        row.__init__(index, values)
    assert row._index is sibling._index is original_index
    assert dict(row) == {"original": 99}
    assert dict(sibling) == {"original": 88}


def test_interrupted_reinitialization_preserves_original_values_and_index():
    row = NamedList({"a": 0}, [99])
    original_index = row._index

    def values():
        yield 10
        raise RuntimeError("interrupted")

    with pytest.raises(RuntimeError, match="interrupted"):
        row.__init__({"b": 0, "c": 1}, values())
    assert row._index is original_index
    assert dict(row) == {"a": 99}


def test_shared_growth_allows_existing_short_rows_but_not_new_short_rows():
    index = {"a": 0}
    first = NamedList(index, [10])
    second = NamedList(index, [20])
    first["b"] = 30
    assert second["b"] is None
    assert tuple(second) == (20,)
    with pytest.raises(ValueError, match=r"values length \(1\).*index length \(2\)"):
        NamedList(index, [40])
    assert NamedList(index) == [None, None]
    assert dict(NamedList(index, [40, 50])) == {"a": 40, "b": 50}
    assert first._index is second._index is index
