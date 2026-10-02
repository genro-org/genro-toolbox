# Copyright 2026 Softwell S.r.l. - Genro Team
# SPDX-License-Identifier: Apache-2.0

"""Build the legacy corpus for ``genro_toolbox.dates.period_parser``.

Runs GenroPy ``decodeDatePeriod`` on every input × workdate × locale and
writes what it returns to ``tests/data/period_parser_corpus.json``. The
tests replay that file; they never import GenroPy.

Not part of the package and not run in CI. It needs GenroPy and Babel, so it
runs with the GenroPy interpreter on a clean export of the legacy ref::

    git -C <genropy> archive <ref> gnrpy | tar -x -C <tmpdir>
    PYTHONPATH=<tmpdir>/gnrpy python scripts/build_period_parser_corpus.py \\
        --legacy-ref <ref> --legacy-commit <sha>

Each case records ``start`` and ``end`` as ISO strings (``null`` for an open
bound), or ``error`` with the exception class name. A two-digit year alone
depends on the system date in the legacy, so the run date is recorded too.
"""

import argparse
import datetime
import json
from pathlib import Path

import babel
from gnr.core.gnrdate import decodeDatePeriod

OUTPUT = Path(__file__).resolve().parent.parent / "tests" / "data" / "period_parser_corpus.json"

WORKDATES = [
    datetime.date(2026, 4, 15),  # Wednesday, mid-year
    datetime.date(2026, 1, 5),  # Monday in January
    datetime.date(2026, 12, 31),  # last day of the year
    datetime.date(2024, 2, 29),  # leap day
    datetime.date(2026, 3, 1),  # Sunday
    datetime.date(2008, 4, 25),  # workdate of the legacy test suite
]

IT_LOCALES = ["it", "it_IT"]
EN_LOCALES = ["en", "en_US", "en_GB"]

IT_INPUTS = [
    # values found in applications
    "oggi",
    "oggi+1",
    "oggi-30;",
    "oggi-180;",
    "oggi;oggi+7",
    "oggi;oggi+30",
    "questa settimana",
    "settimana scorsa",
    "questo mese",
    "mese scorso",
    "2024",
    # keywords and offsets
    "ieri",
    "domani",
    "ieri+2",
    "oggi + 3",
    "oggi - 3",
    "settimana",
    "settimana prossima",
    "settimana+2",
    "mese",
    "mese prossimo",
    "mese+2",
    "mese scorso-1",
    "MESE SCORSO",
    # years
    "2007",
    "24",
    "07",
    "96",
    "46",
    "47",
    "99",
    # months
    "gennaio",
    "giugno",
    "dicembre",
    "gen",
    "mag",
    "set",
    "m3",
    "gennaio 2024",
    "gen 24",
    "dic 25",
    "febbraio 2024",
    "ottobre scorso",
    "ottobre prossimo",
    "marzo scorso",
    "lo scorso ottobre",
    # quarters
    "t1",
    "q1",
    "q1 2024",
    "2024q1",
    "1° trimestre",
    "1º trimestre",
    "202401",
    # weekdays
    "lunedì",
    "lun",
    "domenica",
    # ranges
    "dicembre;marzo",
    "marzo;gennaio",
    "luglio;settembre",
    "2023;2024",
    "2024;",
    ";2024",
    "  ;2024",
    "oggi;",
    ";",
    "dicembre a marzo 2025",
    "da dicembre a marzo 2025",
    "da dicembre a mar 06",
    "da dicembre a questo mese",
    "da settimana scorsa al mese prossimo",
    "da dicembre",
    "a dicembre",
    "dal 23-12-07 a aprile",
    "da lunedì a oggi",
    "dal 1/1/24 al 31/3/24",
    "dal gennaio",
    "al marzo",
    "a marzo",
    "da oggi-30",
    "da oggi a oggi+7",
    "gennaio e marzo",
    "tra gennaio e marzo",
    "01012008 a 31012008",
    "010108 a 310108",
    "2024,2025",
    # dates
    "2026-01-10",
    "2026-01-10;2026-02-01",
    "2008-01-02",
    "10/01/2026",
    "10/1/26",
    "10 1 26",
    "02/01/08",
    "02/01/2008",
    "02-01-2008",
    "02 01 2008",
    "100126",
    "10012026",
    "02012008",
    "020108",
    "10/1/46",
    "10/1/47",
    "10/1/99",
    "2024-1-5",
    "2024-13-01",
    "31/2/2024",
    "10 gennaio 2026",
    "1/2",
    # no period
    "-",
    "sempre",
    "senza periodo",
    "",
    "   ",
    # expected failures
    "garbage",
    "settimane",
    "oggi+",
    "oggi+x",
    "a;b;c",
    "oggi alle 10:00",
]

EN_INPUTS = [
    # values found in applications
    "today",
    "today+1",
    "today;today+7",
    "today;today+30",
    "from last month to last month + 11",
    # keywords and offsets
    "yesterday",
    "tomorrow",
    "this week",
    "week",
    "last week",
    "next week",
    "this month",
    "month",
    "last month",
    "next month",
    "months",
    # years and months
    "2007",
    "07",
    "96",
    "february",
    "april 2007",
    "apr 07",
    "december",
    "m12",
    "last october",
    "october last",
    # quarters
    "q1",
    "Q1",
    "Q1 2024",
    "2024Q1",
    "1st quarter",
    "from 1st quarter to 2nd quarter",
    "from Q1 to Q2",
    "202401",
    # weekdays
    "monday",
    "mon",
    "from monday to friday",
    # ranges
    "2024-01-01;2024-03-01",
    "2008-01-02 to 2008-02-02",
    "from january to march",
    "january to march 2024",
    "between january and march",
    "from today",
    "to today",
    "to tomorrow",
    "to january",
    "to april",
    "to december",
    "to december 2007",
    "from tomorrow + 2",
    "from december 07",
    "from december",
    "from february",
    "from february to today",
    "december to today",
    "from december 06 to march",
    "from december to march 06",
    "from december to this month",
    "between december and this month",
    "from last week to next month",
    "january;march",
    "from 2024 to 2025",
    # dates
    "2026-01-10",
    "04/28/2008",
    "4/28/08",
    "28 4 08",
    "4 28 08",
    "28/4/08",
    "02/01/08",
    "january 10, 2026",
    "02 01, 2007",
    # no period
    "no period",
    "always",
    # expected failures
    "garbage",
    "today at 10:00",
]

EXTRA_CASES = [
    ("02/01/08", "en_AU"),  # legacy test suite
    ("janvier", "fr"),
    ("aujourd'hui", "fr"),
    ("today", "it"),
    ("this week", "it"),
]


class CorpusBuilder:
    """Collects the legacy output for every case and writes the corpus file."""

    def __init__(self, legacy_ref: str, legacy_commit: str) -> None:
        self.legacy_ref = legacy_ref
        self.legacy_commit = legacy_commit
        self.cases: list[dict] = []

    def add_case(self, text: str, workdate: datetime.date, locale: str) -> None:
        case: dict = {"text": text, "workdate": workdate.isoformat(), "locale": locale}
        try:
            start, end = decodeDatePeriod(text, workdate=workdate, locale=locale, returnDate=True)
        except Exception as error:
            case["error"] = type(error).__name__
        else:
            case["start"] = start.isoformat() if start else None
            case["end"] = end.isoformat() if end else None
        self.cases.append(case)

    def add_inputs(self, inputs: list[str], locales: list[str]) -> None:
        for text in inputs:
            for locale in locales:
                for workdate in WORKDATES:
                    self.add_case(text, workdate, locale)

    def write_corpus(self) -> None:
        corpus = {
            "meta": {
                "legacy_ref": self.legacy_ref,
                "legacy_commit": self.legacy_commit,
                "babel_version": babel.__version__,
                "generated_on": datetime.date.today().isoformat(),
                "case_count": len(self.cases),
            },
            "cases": self.cases,
        }
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(corpus, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the legacy period parser corpus.")
    parser.add_argument("--legacy-ref", required=True)
    parser.add_argument("--legacy-commit", required=True)
    args = parser.parse_args()
    builder = CorpusBuilder(args.legacy_ref, args.legacy_commit)
    builder.add_inputs(IT_INPUTS, IT_LOCALES)
    builder.add_inputs(EN_INPUTS, EN_LOCALES)
    for text, locale in EXTRA_CASES:
        for workdate in WORKDATES:
            builder.add_case(text, workdate, locale)
    builder.write_corpus()
    print(f"{len(builder.cases)} cases written to {OUTPUT}")
