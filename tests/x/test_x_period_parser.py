# Copyright 2026 Softwell S.r.l. - Genro Team
# SPDX-License-Identifier: Apache-2.0

"""Implementation tests for genro_toolbox.dates.period_parser.

They photograph the current decoding rules and the language-file checks; they
may change together with the implementation.
"""

import datetime
import json
from pathlib import Path

import pytest

from genro_toolbox.dates import DatePeriod, PeriodError, PeriodLocaleError, parse_period

LOCALES = Path(__file__).parent.parent.parent / "src" / "genro_toolbox" / "dates" / "locales"
WORKDATE = datetime.date(2026, 4, 15)


def day(year: int, month: int, number: int) -> datetime.date:
    return datetime.date(year, month, number)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("10 gennaio", DatePeriod(day(2026, 1, 10), day(2026, 1, 10))),
        ("gennaio scorso", DatePeriod(day(2026, 1, 1), day(2026, 1, 31))),
        ("aprile prossimo", DatePeriod(day(2026, 4, 1), day(2026, 4, 30))),
        ("marzo prossimo", DatePeriod(day(2027, 3, 1), day(2027, 3, 31))),
        ("la settimana scorsa", DatePeriod(day(2026, 4, 6), day(2026, 4, 12))),
        ("il mese scorso", DatePeriod(day(2026, 3, 1), day(2026, 3, 31))),
        ("dalla settimana scorsa al mese prossimo", DatePeriod(day(2026, 4, 6), day(2026, 5, 31))),
        ("la", None),
        ("la bella settimana scorsa", None),
        ("t2 2025", DatePeriod(day(2025, 4, 1), day(2025, 6, 30))),
        ("da 2025 a gennaio 2024", DatePeriod(day(2025, 1, 1), day(2025, 1, 31))),
        ("mese-4", DatePeriod(day(2025, 12, 1), day(2025, 12, 31))),
        ("settimana scorsa-1", DatePeriod(day(2026, 3, 30), day(2026, 4, 5))),
    ],
)
def test_italian_forms(text, expected):
    if expected is None:
        with pytest.raises(PeriodError):
            parse_period(text, WORKDATE, "it")
    else:
        assert parse_period(text, WORKDATE, "it") == expected


@pytest.mark.parametrize(
    "text",
    [
        "gennaio a marzo a aprile",
        "gennaio febbraio",
        "gennaio pippo",
        "gennaio scorso 2024",
        "10 gennaio 2026 x",
        "1/13/2008/1",
        "123/1/2008",
        "1/1/202",
        "31/02/2024",
    ],
)
def test_rejected_forms(text):
    with pytest.raises(PeriodError):
        parse_period(text, WORKDATE, "it")


def test_month_over_twelve_swaps_only_with_separators():
    assert parse_period("1/13/08", WORKDATE, "it").start == day(2008, 1, 13)
    with pytest.raises(PeriodError):
        parse_period("011308", WORKDATE, "it")


def test_region_and_separator_in_locale():
    assert parse_period("2/1/08", WORKDATE, "en-gb").start == day(2008, 1, 2)
    assert parse_period("2/1/08", WORKDATE, "en_US").start == day(2008, 2, 1)


def test_english_keywords_in_italian():
    assert parse_period("from today to tomorrow", WORKDATE, "it") == DatePeriod(
        WORKDATE, day(2026, 4, 16)
    )


def test_italian_keywords_not_in_english():
    with pytest.raises(PeriodError):
        parse_period("oggi", WORKDATE, "en")


def test_pivot_window_follows_workdate():
    assert parse_period("30", day(2008, 4, 25), "it").start == day(1930, 1, 1)
    assert parse_period("27", day(2008, 4, 25), "it").start == day(2027, 1, 1)


@pytest.mark.parametrize(
    "remove, message",
    [
        (lambda data: data["keywords"].pop("articles"), "articles"),
        (lambda data: data["date_order"].pop("default"), "default"),
        (lambda data: data.pop("months"), "months"),
    ],
)
def test_language_file_checks(tmp_path, remove, message):
    data = json.loads((LOCALES / "it.json").read_text(encoding="utf-8"))
    remove(data)
    (tmp_path / "xx.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(PeriodLocaleError, match=message):
        parse_period("oggi", WORKDATE, "xx", locale_dir=tmp_path)
