# Copyright 2026 Softwell S.r.l. - Genro Team
# SPDX-License-Identifier: Apache-2.0

"""Parse a date period written in natural language into two dates.

Port of GenroPy ``decodeDatePeriod`` (``gnr/core/gnrdate.py``) without Babel
and without global state: ``workdate`` and ``locale`` are always arguments.

Contract::

    parse_period(text, workdate, locale, pivot_year=20, locale_dir=None)
        -> DatePeriod(start: date | None, end: date | None)

``None`` on one side is an open bound; both ``None`` means no filter. Any
text that does not decode raises :class:`PeriodError` carrying ``value``
and ``locale``.

Splitting — the text is lowercased and stripped, commas are removed (so
``january 10, 2026`` is one date). Bounds are separated only by ``;`` or by
the ``from`` / ``to`` keywords (``dal ... al``, ``from ... to``):

- ``a;b`` → start ``a``, end ``b`` (either may be empty); more than one
  ``;`` is an error.
- a ``no_period`` keyword alone (``always``, ``sempre``, ``-``) or empty
  text → no bounds.
- ``<to> b`` → end only. ``[<from>] a <to> b`` → both. ``<from> a`` →
  start only. Otherwise the whole text is both start and end.

Each side decodes to a single date or to a span; the start side keeps the
first day of a span, the end side its last day. Forms, first match wins:

- year ``2024`` / ``24`` → the whole year;
- ``today`` / ``yesterday`` / ``tomorrow`` with optional ``+n`` / ``-n`` days;
- this/last/next week, optional ``+n`` / ``-n`` weeks → Monday..Sunday;
- this/last/next month, optional ``+n`` / ``-n`` months → whole month;
- quarter (``q1``, ``t1``, ``1st quarter``), year optional before or after;
- month (name, abbreviation or ``m1``..``m12``), optionally with a year or
  with a ``last`` / ``next`` word, before or after;
- day + month name: the day before the month with an optional year after
  (``10 gennaio 2026``), or month, day, year (``january 10 2026``); a
  single number after the month is always a year (``apr 07``, as legacy);
- weekday name → that day in the workdate's week;
- ISO ``YYYY-MM-DD``;
- numeric date in the locale ``date_order``: separators ``/ - .`` or space
  (a month over 12 swaps with a day up to 12, as Babel did: ``28/4/08`` is
  28 April in ``en`` too), or 6/8 digits without separators (no swap).

Keywords match whole words, never substrings. The ``articles`` words are
dropped from each bound (``la settimana scorsa``, ``lo scorso ottobre``);
any other unknown word is an error, and a bound made only of articles too.
Months win over weekdays on a shared abbreviation (``mar`` is March in
Italian).

Month year, when the month carries none:

- bare month → the workdate's year, on either side;
- ``<month> last`` → the latest such month up to the workdate's month
  included; ``<month> next`` → the first one from the workdate's month
  included.

Quarters follow the same rule. In a range, a bare month or quarter then
shifts against the other bound, as in the legacy:

- bare start, end with a year → the end's year, one year earlier when the
  start month is later (``from december to march 2025`` → 2024-12-01..);
- bare end, known start → not before the start: the start's year at least,
  one year later when the end month is earlier (``dicembre;marzo`` in April
  2026 → ..2027-03-31).

Two-digit years fall in the window ``workdate.year + pivot_year - 100`` ..
``workdate.year + pivot_year - 1``, for every form that carries a year.

Language data — one JSON per language in ``locales/`` (or ``locale_dir``):
``months``, ``weekdays``, ``quarters`` (name → number, weekday Monday = 0),
``keywords`` (key → list of phrases) and ``date_order`` (``"default"`` plus
optional region overrides, e.g. ``{"default": "MDY", "GB": "DMY"}``).
``it_IT`` resolves to ``it.json`` with region ``IT``. English keywords are
accepted in every language. A missing file or key raises
:class:`PeriodLocaleError` when the language is loaded; it is not a
:class:`PeriodError`, so catching bad input never hides bad configuration.

Example:
    parse_period("mese scorso", date(2026, 4, 15), "it")
    # -> DatePeriod(start=date(2026, 3, 1), end=date(2026, 3, 31))
"""

import calendar
import datetime
import json
import re
from pathlib import Path
from typing import NamedTuple

DEFAULT_LOCALE_DIR = Path(__file__).parent / "locales"
ENGLISH = "en"
REQUIRED_SECTIONS = ("months", "weekdays", "quarters", "keywords", "date_order")
REQUIRED_KEYWORDS = (
    "today", "yesterday", "tomorrow",
    "this_week", "last_week", "next_week",
    "this_month", "last_month", "next_month",
    "last", "next", "articles", "from", "to", "no_period",
)  # fmt: skip
DAY_SHIFTS = {"today": 0, "yesterday": -1, "tomorrow": 1}
WEEK_SHIFTS = {"this_week": 0, "last_week": -1, "next_week": 1}
MONTH_SHIFTS = {"this_month": 0, "last_month": -1, "next_month": 1}

YEAR_RE = re.compile(r"\d{4}|\d{2}")
DAY_RE = re.compile(r"\d{1,2}")
OFFSET_RE = re.compile(r"(?P<body>.+?)\s*(?P<sign>[+-])\s*(?P<amount>\d+)")
ISO_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
NUMERIC_DATE_RE = re.compile(r"(\d{1,4})[/\-. ]+(\d{1,4})[/\-. ]+(\d{1,4})")
DIGITS_DATE_RE = re.compile(r"\d{6}|\d{8}")
MONTH_NUMBER_RE = re.compile(r"m(\d{1,2})")


class PeriodError(ValueError):
    """The text is not a period the parser recognizes."""

    def __init__(self, value: str, locale: str) -> None:
        super().__init__(f"Unrecognized period {value!r} for locale {locale!r}")
        self.value = value
        self.locale = locale


class PeriodLocaleError(Exception):
    """A language file is missing or lacks a required key."""


class DatePeriod(NamedTuple):
    """Start and end of a period; ``None`` is an open bound."""

    start: datetime.date | None
    end: datetime.date | None


class MonthRef(NamedTuple):
    """A month not yet tied to a day: ``year`` is ``None`` when not given."""

    year: int | None
    month: int


class PeriodLocale:
    """The language data of one locale, read from its JSON file."""

    def __init__(self, locale: str, locale_dir: Path | str | None = None) -> None:
        language, _, region = locale.replace("-", "_").partition("_")
        self.language = language.lower()
        self.region = region.upper()
        directory = Path(locale_dir) if locale_dir else DEFAULT_LOCALE_DIR
        self.data = self.get_language_data(directory, self.language)
        if self.language == ENGLISH:
            self.english_keywords = self.data["keywords"]
        else:
            self.english_keywords = self.get_language_data(DEFAULT_LOCALE_DIR, ENGLISH)["keywords"]

    def get_language_data(self, directory: Path, language: str) -> dict:
        path = directory / f"{language}.json"
        if not path.is_file():
            raise PeriodLocaleError(f"No period language file for {language!r}: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        for section in REQUIRED_SECTIONS:
            if section not in data:
                raise PeriodLocaleError(f"{path}: missing section {section!r}")
        for key in REQUIRED_KEYWORDS:
            if key not in data["keywords"]:
                raise PeriodLocaleError(f"{path}: missing keyword {key!r}")
        if "default" not in data["date_order"]:
            raise PeriodLocaleError(f"{path}: missing date_order 'default'")
        return data

    @property
    def months(self) -> dict[str, int]:
        return self.data["months"]

    @property
    def weekdays(self) -> dict[str, int]:
        return self.data["weekdays"]

    @property
    def quarters(self) -> dict[str, int]:
        return self.data["quarters"]

    @property
    def date_order(self) -> str:
        orders = self.data["date_order"]
        return orders.get(self.region, orders["default"])

    def get_phrases(self, key: str) -> list[str]:
        phrases = list(self.data["keywords"][key])
        phrases.extend(p for p in self.english_keywords[key] if p not in phrases)
        return phrases

    def get_keyword(self, text: str, keys: list[str]) -> str | None:
        for key in keys:
            if text in self.get_phrases(key):
                return key
        return None

    def get_month_number(self, token: str) -> int | None:
        if token in self.months:
            return self.months[token]
        match = MONTH_NUMBER_RE.fullmatch(token)
        if match and 1 <= int(match[1]) <= 12:
            return int(match[1])
        return None


class PeriodParser:
    """Decodes one period text against a workdate; see the module docstring."""

    def __init__(
        self,
        text: str,
        workdate: datetime.date,
        locale: str,
        pivot_year: int = 20,
        locale_dir: Path | str | None = None,
    ) -> None:
        self.text = text
        self.workdate = workdate
        self.locale = locale
        self.pivot_year = pivot_year
        self.period_locale = PeriodLocale(locale, locale_dir)

    @property
    def period(self) -> DatePeriod:
        start_text, end_text = self.bound_texts
        end_bound = self.get_bound(end_text, is_end=True)
        start = self.get_start_date(self.get_bound(start_text, is_end=False), end_bound)
        return DatePeriod(start, self.get_end_date(end_bound, start))

    @property
    def unrecognized_error(self) -> PeriodError:
        return PeriodError(self.text, self.locale)

    @property
    def bound_texts(self) -> tuple[str, str]:
        text = self.text.lower().strip().replace(",", "")
        if ";" in text:
            parts = text.split(";")
            if len(parts) != 2:
                raise self.unrecognized_error
            return parts[0].strip(), parts[1].strip()
        if text in self.period_locale.get_phrases("no_period"):
            return "", ""
        to_words = self.period_locale.get_phrases("to")
        from_words = self.period_locale.get_phrases("from")
        for word in to_words:
            if text.startswith(f"{word} "):
                return "", text[len(word) + 1 :].strip()
        for word in to_words:
            separator = f" {word} "
            if separator in text:
                for from_word in from_words:
                    if text.startswith(f"{from_word} "):
                        text = text[len(from_word) + 1 :]
                        break
                parts = text.split(separator)
                if len(parts) != 2:
                    raise self.unrecognized_error
                return parts[0].strip(), parts[1].strip()
        for word in from_words:
            if text.startswith(f"{word} "):
                return text[len(word) + 1 :].strip(), ""
        return text, text

    def get_bound(self, text: str, is_end: bool) -> datetime.date | MonthRef | None:
        if not text:
            return None
        articles = self.period_locale.get_phrases("articles")
        text = " ".join(token for token in text.split() if token not in articles)
        if not text:
            raise self.unrecognized_error
        if YEAR_RE.fullmatch(text):
            year = self.get_year(text)
            return datetime.date(year, 12, 31) if is_end else datetime.date(year, 1, 1)
        bound = (
            self.get_keyword_date(text, is_end)
            or self.get_quarter(text, is_end)
            or self.get_month(text)
            or self.get_weekday_date(text)
            or self.get_numeric_date(text)
        )
        if bound is None:
            raise self.unrecognized_error
        return bound

    def get_keyword_date(self, text: str, is_end: bool) -> datetime.date | None:
        candidates = [(text, 0)]
        match = OFFSET_RE.fullmatch(text)
        if match:
            amount = int(match["amount"])
            candidates.append((match["body"], amount if match["sign"] == "+" else -amount))
        for body, amount in candidates:
            key = self.period_locale.get_keyword(body, [*DAY_SHIFTS, *WEEK_SHIFTS, *MONTH_SHIFTS])
            if key in DAY_SHIFTS:
                return self.workdate + datetime.timedelta(days=DAY_SHIFTS[key] + amount)
            if key in WEEK_SHIFTS:
                monday = self.workdate - datetime.timedelta(days=self.workdate.weekday())
                monday += datetime.timedelta(weeks=WEEK_SHIFTS[key] + amount)
                return monday + datetime.timedelta(days=6) if is_end else monday
            if key in MONTH_SHIFTS:
                total = (
                    self.workdate.year * 12 + self.workdate.month - 1 + MONTH_SHIFTS[key] + amount
                )
                year, month = divmod(total, 12)
                return (
                    self.get_month_end(year, month + 1)
                    if is_end
                    else datetime.date(year, month + 1, 1)
                )
        return None

    def get_quarter(self, text: str, is_end: bool) -> MonthRef | None:
        for name, number in sorted(
            self.period_locale.quarters.items(), key=lambda item: -len(item[0])
        ):
            if text == name:
                year = None
            elif text.startswith(name) and YEAR_RE.fullmatch(text[len(name) :].strip()):
                year = self.get_year(text[len(name) :].strip())
            elif text.endswith(name) and YEAR_RE.fullmatch(text[: -len(name)].strip()):
                year = self.get_year(text[: -len(name)].strip())
            else:
                continue
            return MonthRef(year, number * 3 if is_end else number * 3 - 2)
        return None

    def get_month(self, text: str) -> datetime.date | MonthRef | None:
        tokens = text.split()
        positions = [
            i for i, token in enumerate(tokens) if self.period_locale.get_month_number(token)
        ]
        if not positions:
            return None
        if len(positions) != 1:
            raise self.unrecognized_error
        position = positions[0]
        month = self.period_locale.get_month_number(tokens[position])
        assert month is not None
        before, after = tokens[:position], tokens[position + 1 :]
        others = before + after
        last_words = self.period_locale.get_phrases("last")
        next_words = self.period_locale.get_phrases("next")
        if len(others) == 1 and others[0] in last_words:
            return MonthRef(self.get_last_month_year(month), month)
        if len(others) == 1 and others[0] in next_words:
            return MonthRef(self.get_next_month_year(month), month)
        if not others:
            return MonthRef(None, month)
        if not before and len(after) == 1 and YEAR_RE.fullmatch(after[0]):
            return MonthRef(self.get_year(after[0]), month)
        if len(before) == 1 and DAY_RE.fullmatch(before[0]):
            if not after:
                return self.get_date(self.workdate.year, month, int(before[0]))
            if len(after) == 1 and YEAR_RE.fullmatch(after[0]):
                return self.get_date(self.get_year(after[0]), month, int(before[0]))
        if (
            not before
            and len(after) == 2
            and DAY_RE.fullmatch(after[0])
            and YEAR_RE.fullmatch(after[1])
        ):
            return self.get_date(self.get_year(after[1]), month, int(after[0]))
        raise self.unrecognized_error

    def get_last_month_year(self, month: int) -> int:
        return self.workdate.year if month <= self.workdate.month else self.workdate.year - 1

    def get_next_month_year(self, month: int) -> int:
        return self.workdate.year if month >= self.workdate.month else self.workdate.year + 1

    def get_weekday_date(self, text: str) -> datetime.date | None:
        if text not in self.period_locale.weekdays:
            return None
        return self.workdate + datetime.timedelta(
            days=self.period_locale.weekdays[text] - self.workdate.weekday()
        )

    def get_numeric_date(self, text: str) -> datetime.date | None:
        match = ISO_RE.fullmatch(text)
        if match:
            return self.get_date(int(match[1]), int(match[2]), int(match[3]))
        order = self.period_locale.date_order
        match = NUMERIC_DATE_RE.fullmatch(text)
        if match:
            parts = dict(zip(order, match.groups(), strict=True))
        elif DIGITS_DATE_RE.fullmatch(text):
            year_width = 4 if len(text) == 8 else 2
            parts = {}
            for letter in order:
                width = year_width if letter == "Y" else 2
                parts[letter], text = text[:width], text[width:]
        else:
            return None
        if not YEAR_RE.fullmatch(parts["Y"]) or len(parts["D"]) > 2 or len(parts["M"]) > 2:
            raise self.unrecognized_error
        day, month = int(parts["D"]), int(parts["M"])
        if match and month > 12 and day <= 12:
            day, month = month, day
        return self.get_date(self.get_year(parts["Y"]), month, day)

    def get_year(self, token: str) -> int:
        if len(token) == 4:
            return int(token)
        lowest = self.workdate.year + self.pivot_year - 100
        return lowest + (int(token) - lowest) % 100

    def get_date(self, year: int, month: int, day: int) -> datetime.date:
        try:
            return datetime.date(year, month, day)
        except ValueError:
            raise self.unrecognized_error from None

    def get_month_end(self, year: int, month: int) -> datetime.date:
        return datetime.date(year, month, calendar.monthrange(year, month)[1])

    def get_start_date(
        self, start: datetime.date | MonthRef | None, end: datetime.date | MonthRef | None
    ) -> datetime.date | None:
        if not isinstance(start, MonthRef):
            return start
        year = self.workdate.year if start.year is None else start.year
        end_year: int | None = None
        end_month = 0
        if isinstance(end, datetime.date | MonthRef):
            end_year, end_month = end.year, end.month
        if end_year:
            if year > end_year:
                year = end_year
            if year == end_year and start.month > end_month:
                year -= 1
        return datetime.date(year, start.month, 1)

    def get_end_date(
        self, end: datetime.date | MonthRef | None, start: datetime.date | None
    ) -> datetime.date | None:
        if not isinstance(end, MonthRef):
            return end
        year = self.workdate.year if end.year is None else end.year
        if start is not None:
            if year < start.year:
                year = start.year
            if year == start.year and start.month > end.month:
                year += 1
        return self.get_month_end(year, end.month)


def parse_period(
    text: str,
    workdate: datetime.date,
    locale: str,
    pivot_year: int = 20,
    locale_dir: Path | str | None = None,
) -> DatePeriod:
    """Parse ``text`` into a :class:`DatePeriod`; see the module docstring."""
    return PeriodParser(text, workdate, locale, pivot_year, locale_dir).period
