"""Check stored values and shared index after errors, not just exception types."""

import pytest

from genro_toolbox import NamedList


class FetchError(Exception):
    pass


def interrupted_values():
    yield 99
    raise FetchError("fetch interrupted")


@pytest.mark.parametrize("width", range(1, 6))
def test_failed_assignment_at_index_boundary_pads_short_row(width):
    for length in range(width):
        index = {f"c{i}": i for i in range(length)}
        row = NamedList(index, tuple(range(length)))
        sibling = NamedList(index, tuple(range(length)))
        growing = NamedList(index, tuple(range(length)))
        growing.update({f"c{i}": i for i in range(length, width)})
        before = tuple(row)
        for position in (width, -width - 1):
            row[:] = before
            with pytest.raises(IndexError):
                row[position] = 99
            assert tuple(row) == before + (None,) * (width - length)
            assert tuple(sibling) == before
            assert row._index is sibling._index is index


@pytest.mark.parametrize("width", range(1, 6))
def test_assignment_far_beyond_index_does_not_mutate(width):
    index = {f"c{i}": i for i in range(width)}
    for length in range(width + 2):
        row = NamedList(index)
        row[:] = tuple(range(length))  # Later structural mutation remains supported.
        before = tuple(row)
        with pytest.raises(IndexError):
            row[width + 10] = 99
        assert tuple(row) == before
        assert row._index == index


@pytest.mark.parametrize("width", range(2, 6))
def test_negative_position_outside_short_row_can_become_valid_after_padding(width):
    row = NamedList({"c0": 0}, [10])
    growing = NamedList(row._index, [20])
    growing.update({f"c{i}": i for i in range(1, width)})
    with pytest.raises(IndexError):
        row[-width]
    row[-width] = 99
    assert tuple(row) == (99,) + (None,) * (width - 1)


@pytest.mark.parametrize(
    "selection, replacement, original_error",
    [
        (slice(None, None, 2), [7, 8, 9], ValueError),
        (slice(None, None, 0), [7], ValueError),
        (slice(None), 7, TypeError),
        (slice("invalid", None), [7], TypeError),
    ],
)
def test_slice_failures_are_masked_but_leave_values_and_index_unchanged(
    selection, replacement, original_error
):
    values = [1, 2, 3]
    with pytest.raises(original_error):
        values[selection] = replacement
    index = {"a": 0, "b": 1, "c": 2}
    row = NamedList(index, values)
    with pytest.raises(TypeError, match="not supported between instances") as failure:
        row[selection] = replacement
    assert isinstance(failure.value.__context__, original_error)
    assert tuple(row) == (1, 2, 3)
    assert dict(row) == {"a": 1, "b": 2, "c": 3}
    assert row._index is index


def test_interrupted_slice_consumption_preserves_row_but_masks_fetch_error():
    row = NamedList({"a": 0, "b": 1}, [1, 2])
    with pytest.raises(TypeError) as failure:
        row[:] = interrupted_values()
    assert isinstance(failure.value.__context__, FetchError)
    assert tuple(row) == (1, 2)
    assert dict(row) == {"a": 1, "b": 2}


def test_constructor_propagates_interrupted_fetch_without_mutating_caller_index():
    index = {"a": 0, "b": 1}
    sibling = NamedList(index, (1, 2))
    with pytest.raises(FetchError, match="fetch interrupted"):
        NamedList(index, interrupted_values())
    assert index == {"a": 0, "b": 1}
    assert tuple(sibling) == (1, 2)


def test_update_is_partial_and_publishes_new_shared_name_before_later_failure():
    index = {"a": 0, "b": 1}
    row = NamedList(index, (1, 2))
    sibling = NamedList(index, (3, 4))
    with pytest.raises(IndexError):
        row.update({"a": 10, "new": 20, 999: 30, "not_reached": 40})
    assert dict(row) == {"a": 10, "b": 2, "new": 20}
    assert tuple(sibling) == (3, 4)
    assert dict(sibling) == {"a": 3, "b": 4, "new": None}
    assert "not_reached" not in index
    with pytest.raises(IndexError):
        sibling.items()


def test_update_from_short_row_fails_before_any_target_assignment():
    source = NamedList({"a": 0}, [10])
    growing = NamedList(source._index, [20])
    growing["b"] = 30
    target = NamedList({"a": 0}, [1])
    with pytest.raises(IndexError):
        target.update(source)
    assert tuple(target) == (1,)
    assert target._index == {"a": 0}


def test_update_from_index_corrupted_after_construction_leaves_target_unchanged():
    source = NamedList({"x": 0, "x2": 1, "id": 2}, (10, 20, 1))
    # External mutation of the shared dict is still possible after validation.
    del source._index["x2"]
    source._index["x"] = 1
    target = NamedList({"a": 0}, [1])
    with pytest.raises(IndexError):
        target.update(source)
    assert tuple(target) == (1,)
    assert target._index == {"a": 0}


@pytest.mark.parametrize("operation", ["extend", "iadd"])
def test_interrupted_inherited_extension_leaves_extra_unnamed_values(operation):
    row = NamedList({"a": 0}, [1])
    with pytest.raises(FetchError):
        if operation == "extend":
            row.extend(interrupted_values())
        else:
            row += interrupted_values()
    assert tuple(row) == row.values() == (1, 99)
    assert dict(row) == {"a": 1}
    row["new"] = 7
    assert tuple(row) == (1, 7)  # The unnamed value is overwritten.


@pytest.mark.parametrize("position", [4, 100, -100])
def test_bad_index_reads_after_external_index_mutation_do_not_mutate_values(position):
    row = NamedList({"a": 0, "b": 1}, [10, 20])
    row._index["a"] = position
    if position > len(row._index):
        with pytest.raises(IndexError):
            row["a"]
        assert row.get("a", "fallback") == "fallback"
    else:
        assert row["a"] is None
        assert row.get("a", "fallback") is None
    assert tuple(row) == (10, 20)
    assert row._index == {"a": position, "b": 1}


def test_failed_new_field_extension_leaves_name_in_shared_index():
    class InterruptedRow(NamedList):
        def extend(self, values):
            raise FetchError("extension interrupted")

    index = {"a": 0}
    row = InterruptedRow(index, [1])
    sibling = NamedList(index, [2])
    with pytest.raises(FetchError):
        row["new"] = 99
    assert tuple(row) == (1,)
    assert tuple(sibling) == (2,)
    assert index == {"a": 0, "new": 1}
    assert row["new"] is sibling["new"] is None


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="Failed positional assignment pads a row shortened by shared-index growth",
)
def test_regression_failed_assignment_preserves_stored_tuple():
    row = NamedList({"a": 0}, [10])
    growing = NamedList(row._index, [20])
    growing["b"] = 30
    before = tuple(row)
    with pytest.raises(IndexError):
        row[2] = 99
    assert tuple(row) == before


@pytest.mark.xfail(
    strict=True,
    raises=TypeError,
    reason="Slice recovery masks the original fetch error with TypeError",
)
def test_regression_interrupted_slice_propagates_original_error():
    row = NamedList({"a": 0}, [1])
    with pytest.raises(FetchError):
        row[:] = interrupted_values()
