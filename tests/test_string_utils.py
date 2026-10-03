# Copyright 2026 Softwell S.r.l. - Genro Team
# SPDX-License-Identifier: Apache-2.0

"""Contract tests for smartsplit."""

from genro_toolbox import smartsplit


def test_splits_and_strips():
    assert smartsplit("a. b .c", ".") == ["a", "b", "c"]


def test_escaped_separator_is_kept_inside_the_item():
    assert smartsplit(r"a.b\.c.d", ".") == ["a", r"b\.c", "d"]


def test_no_separator_gives_one_item():
    assert smartsplit("abc", ".") == ["abc"]


def test_multi_character_separator():
    assert smartsplit(r"a::b\::c::d", "::") == ["a", r"b\::c", "d"]
