# Copyright 2026 Softwell S.r.l. - Genro Team
# SPDX-License-Identifier: Apache-2.0

"""Contract tests for genro_toolbox.dates.period_parser.

Every case of the legacy corpus (``tests/data/period_parser_corpus.json``,
built by ``scripts/build_period_parser_corpus.py``) must give the legacy
result, except the cases listed in ``period_parser_divergences.json``, which
must give the new value recorded there. A legacy error must be an error.
"""

import datetime
import json
import shutil
from pathlib import Path

import pytest

from genro_toolbox.dates import DatePeriod, PeriodError, PeriodLocaleError, parse_period

DATA = Path(__file__).parent / "data"
LOCALES = Path(__file__).parent.parent / "src" / "genro_toolbox" / "dates" / "locales"
WORKDATE = datetime.date(2026, 4, 15)


def load_cases() -> list[dict]:
    corpus = json.loads((DATA / "period_parser_corpus.json").read_text(encoding="utf-8"))
    divergences = json.loads((DATA / "period_parser_divergences.json").read_text(encoding="utf-8"))
    replaced = {(c["text"], c["locale"], c["workdate"]): c for c in divergences["cases"]}
    return [replaced.get((c["text"], c["locale"], c["workdate"]), c) for c in corpus["cases"]]


CASES = load_cases()


@pytest.mark.parametrize(
    "case", CASES, ids=[f"{c['locale']}|{c['workdate']}|{c['text']!r}" for c in CASES]
)
def test_corpus_case(case):
    workdate = datetime.date.fromisoformat(case["workdate"])
    if "error" in case:
        with pytest.raises((PeriodError, PeriodLocaleError)):
            parse_period(case["text"], workdate, case["locale"])
        return
    result = parse_period(case["text"], workdate, case["locale"])
    assert result == DatePeriod(
        datetime.date.fromisoformat(case["start"]) if case["start"] else None,
        datetime.date.fromisoformat(case["end"]) if case["end"] else None,
    )


def test_result_fields():
    result = parse_period("mese scorso", WORKDATE, "it")
    assert result.start == datetime.date(2026, 3, 1)
    assert result.end == datetime.date(2026, 3, 31)


def test_no_period_gives_no_bounds():
    assert parse_period("", WORKDATE, "it") == DatePeriod(None, None)


def test_error_reports_value_and_locale():
    with pytest.raises(PeriodError) as raised:
        parse_period("garbage", WORKDATE, "it")
    assert raised.value.value == "garbage"
    assert raised.value.locale == "it"
    assert "garbage" in str(raised.value)


def test_period_error_is_value_error():
    assert issubclass(PeriodError, ValueError)


def test_locale_error_is_not_period_error():
    assert not issubclass(PeriodLocaleError, PeriodError)


def test_unsupported_locale():
    with pytest.raises(PeriodLocaleError):
        parse_period("oggi", WORKDATE, "fr")


def test_pivot_year():
    assert parse_period("26", WORKDATE, "it").start == datetime.date(2026, 1, 1)
    assert parse_period("26", WORKDATE, "it", pivot_year=0).start == datetime.date(1926, 1, 1)
    assert parse_period("10/1/26", WORKDATE, "it", pivot_year=0).start == datetime.date(1926, 1, 10)


def test_external_locale_dir(tmp_path):
    shutil.copy(LOCALES / "it.json", tmp_path / "xx.json")
    assert parse_period("oggi", WORKDATE, "xx", locale_dir=tmp_path).start == WORKDATE


def test_external_locale_missing_key(tmp_path):
    data = json.loads((LOCALES / "it.json").read_text(encoding="utf-8"))
    del data["keywords"]
    (tmp_path / "xx.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(PeriodLocaleError) as raised:
        parse_period("oggi", WORKDATE, "xx", locale_dir=tmp_path)
    assert "keywords" in str(raised.value)
