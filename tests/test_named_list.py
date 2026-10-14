"""Characterize the frozen legacy contract, including its known limitations."""

from copy import deepcopy

import pytest

from genro_toolbox.named_list import NamedList


def test_public_import():
    from genro_toolbox import NamedList as PublicNamedList

    assert PublicNamedList is NamedList


def test_mixed_assignment_none_and_unpacking():
    row = NamedList({"codice": 0, "totale": 1}, ["ABC", 10])
    row["totale"] = 20
    assert row[1] == 20
    row[1] = 30
    assert row["totale"] == 30
    assert dict(row) == {"codice": "ABC", "totale": 30}
    code, total = row
    assert (code, total) == ("ABC", 30)
    row["totale"] = None
    assert row[1] is None
    assert row.get("totale", "fallback") is None
    assert row.get("missing", "fallback") == "fallback"
    assert row.get(10, "fallback") == "fallback"
    with pytest.raises(KeyError):
        row["missing"]


def test_constructor_copies_values_but_shares_index():
    index = {"a": 0, "b": 1}
    values = [[], 2]
    row = NamedList(index, values)
    assert row._index is index
    assert row is not values
    assert row[0] is values[0]
    row[1] = 3
    assert values[1] == 2
    assert NamedList(index) == [None, None]
    with pytest.raises(ValueError, match="values length"):
        NamedList(index, [])


def test_column_order_vs_index_insertion_order():
    row = NamedList({"b": 1, "a": 0}, [1, 2])
    assert row.keys() == ["a", "b"]
    assert row.items() == [("a", 1), ("b", 2)]
    assert list(dict(row).items()) == [("a", 1), ("b", 2)]
    # The legacy iteritems docstring claimed positional order incorrectly.
    assert list(row.iteritems()) == [("b", 2), ("a", 1)]
    assert str(row) == repr(row) == "[a=1,b=2]"


def test_shared_index_growth_and_short_rows():
    index = {"a": 0}
    first = NamedList(index, [1])
    second = NamedList(index, [2])
    first["b"] = 3
    first["c"] = 4
    assert second._index is first._index is index
    assert second.keys() == ["a", "b", "c"]
    assert "b" in second and second.has_key("c")
    assert second["b"] is None
    assert second.get("b", "fallback") is None
    assert dict(second) == {"a": 2, "b": None, "c": None}
    assert second.values() == (2, None, None)
    assert list(second) == [2]
    assert len(second) == 1
    assert second.extractItems(["b"]) == [("b", None)]
    assert second.extractValues(None) == [2, None, None]
    with pytest.raises(IndexError):
        second[1]
    for operation in (
        second.items,
        lambda: list(second.iteritems()),
        lambda: second.extractItems(None),
        lambda: repr(second),
        lambda: str(second),
    ):
        with pytest.raises(IndexError):
            operation()
    second["c"] = 5
    assert list(second) == [2, None, 5]
    assert list(first) == [1, 3, 4]
    second.update({"b": 6, "d": None})
    assert second.items() == [("a", 2), ("b", 6), ("c", 5), ("d", None)]
    assert first["d"] is None
    assert len(first) == 3


def test_positional_assignment_expands_to_shared_index_length():
    row = NamedList({"a": 0}, [1])
    sibling = NamedList(row._index, [10])
    sibling.update({"b": 20, "c": 30})
    row[1] = 2
    assert list(row) == [1, 2, None]
    with pytest.raises(IndexError):
        row[3] = 4


def test_equality_ignores_names_and_membership_checks_names():
    row = NamedList({"a": 0}, [10])
    assert row == [10]
    assert row == NamedList({"other": 0}, [10])
    assert row != {"a": 10}
    assert "a" in row and 10 not in row
    assert row.count(10) == 1 and row.index(10) == 0


def test_slices_and_structural_mutations_do_not_reindex():
    index = {"a": 0, "b": 1, "c": 2}
    row = NamedList(index, [1, 2, 3])
    assert type(row[:]) is list
    assert row[::-1] == [3, 2, 1]
    row[:1] = [10, 11]
    assert row == [10, 11, 2, 3]
    assert row["b"] == 11
    assert row.values() == (10, 11, 2, 3)
    assert dict(row) == {"a": 10, "b": 11, "c": 2}
    del row[0]
    assert row["a"] == 11
    row.remove(2)
    assert row == [11, 3]
    assert row["c"] is None
    with pytest.raises(TypeError):
        del row["a"]
    row.clear()
    assert len(row) == 0 and "a" in row
    assert index == {"a": 0, "b": 1, "c": 2}


def test_duplicate_names_are_rejected_instead_of_renamed_by_container():
    names = ["id", "value", "value"]
    index = {name: position for position, name in enumerate(names)}
    with pytest.raises(ValueError, match="index positions"):
        NamedList(index, [1, 10, 20])


def test_pop_warning_and_legacy_removal():
    row = NamedList({"a": 0, "b": 1}, [1, 2])
    with pytest.warns(DeprecationWarning, match="do not use pop in named tuple"):
        assert row.pop("a") == 1
    assert row["a"] == 2 and row["b"] is None
    assert row.keys() == ["a", "b"]
    with pytest.warns(DeprecationWarning), pytest.raises(KeyError):
        row.pop("missing", "ignored")
    with pytest.warns(DeprecationWarning):
        assert row.pop(1, "ignored") is None
    with pytest.warns(DeprecationWarning), pytest.raises(IndexError):
        row.pop(10)
    with pytest.warns(DeprecationWarning), pytest.raises(TypeError):
        row.pop()


@pytest.mark.parametrize("columns", [None, []])
def test_empty_extraction_means_all_columns(columns):
    row = NamedList({"a": 0, "b": 1}, [1, None])
    assert row.extractItems(columns) == [("a", 1), ("b", None)]
    assert row.extractValues(columns) == [1, None]


def test_deepcopy_one_row_is_independent():
    row = NamedList({"a": 0}, [{"nested": [1]}])
    clone = deepcopy(row)
    assert isinstance(clone, NamedList)
    assert clone == row
    assert clone._index is not row._index
    clone["a"]["nested"].append(2)
    clone["extra"] = 3
    assert row["a"] == {"nested": [1]}
    assert "extra" not in row


def test_deepcopy_result_preserves_internal_sharing_and_short_rows():
    index = {"a": 0}
    shared_value = {"nested": []}
    rows = [NamedList(index, [shared_value]), NamedList(index, [shared_value])]
    rows[0]["b"] = 1
    copied = deepcopy(rows)
    assert copied[0]._index is copied[1]._index
    assert copied[0]._index is not index
    assert copied[0][0] is copied[1][0]
    assert copied[0][0] is not shared_value
    assert len(copied[1]) == 1 and copied[1]["b"] is None
    copied[0]["a"]["nested"].append(2)
    assert copied[1]["a"]["nested"] == [2]
    assert shared_value == {"nested": []}
    copied[0]["c"] = 3
    assert "c" in copied[1] and "c" not in rows[0]
