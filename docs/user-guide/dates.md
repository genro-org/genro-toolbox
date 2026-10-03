# dates.parse_period — natural-language date periods

Parse a date period written in natural language into a start and an end date.

## Overview

`parse_period` reads texts such as `"mese scorso"`, `"oggi-30;"` or
`"from january to march"` and returns a `DatePeriod(start, end)`. Relative
expressions refer to a **workdate** you pass in; the **locale** selects the
language. Nothing is read from the system date or the system locale.

- Either bound may be `None`: the period is open on that side.
- Both `None` means no period (no filter).
- Unrecognized text raises `PeriodError`, which carries the value.

It ports GenroPy `decodeDatePeriod` without Babel; the differences are listed
at the end of this page.

## Basic Usage

```python
from datetime import date
from genro_toolbox.dates import parse_period

wd = date(2026, 4, 15)

parse_period("mese scorso", wd, "it")
# DatePeriod(start=date(2026, 3, 1), end=date(2026, 3, 31))

parse_period("oggi-30;", wd, "it")
# DatePeriod(start=date(2026, 3, 16), end=None)

parse_period("", wd, "it")
# DatePeriod(start=None, end=None)
```

## Ranges

| Form | Example | Result (workdate 2026-04-15) |
|---|---|---|
| `a;b` | `today;today+7` | 2026-04-15 .. 2026-04-22 |
| `from a to b` | `from january to march` | 2026-01-01 .. 2026-03-31 |
| `dal a al b` | `dal 1/1/24 al 31/3/24` | 2024-01-01 .. 2024-03-31 |
| `between a and b` / `tra a e b` | `tra gennaio e marzo` | 2026-01-01 .. 2026-03-31 |
| start only | `from today`, `da oggi-30` | 2026-04-15 .. None |
| end only | `to december`, `a marzo` | None .. 2026-03-31 |
| no period | `always`, `sempre`, `-` | None .. None |

Commas are removed: `january 10, 2026` is one date.

## Single Expressions

A single expression that is a span gives its first day as start and its last
day as end.

| Form | Examples |
|---|---|
| year | `2024`, `24` |
| day, with offset in days | `today`, `oggi+1`, `yesterday`, `domani - 2` |
| week (Monday..Sunday), offset in weeks | `this week`, `settimana scorsa`, `next week+2` |
| month, offset in months | `this month`, `mese scorso`, `last month + 11` |
| quarter | `q1`, `t1`, `1st quarter`, `Q1 2024`, `2024Q1` |
| month name | `gennaio`, `apr 07`, `april 2007`, `m3` |
| month with last/next | `ottobre scorso`, `lo scorso ottobre`, `next march` |
| day and month name | `10 gennaio 2026`, `january 10 2026` |
| weekday (in the workdate's week) | `monday`, `lunedì` |
| ISO date | `2026-01-10` |
| numeric date in the locale order | `10/1/26` (it), `4/28/08` (en), `28/4/08` (en_GB), `100126` |

Articles (`la settimana scorsa`, `il mese scorso`) are ignored. Any other
unknown word is an error.

## Month Rules

- A month without year is the workdate's year.
- `<month> scorso` / `last <month>`: the latest such month, the workdate's month included.
- `<month> prossimo` / `next <month>`: the first such month from the workdate's month.

With workdate April 2026: `aprile scorso` → April 2026, `marzo scorso` → March
2026, `maggio scorso` → May 2025, `marzo prossimo` → March 2027.

In a range, a month without year shifts against the other bound, as in the
legacy: `from december to march 2025` → 2024-12-01 .. 2025-03-31;
`dicembre;marzo` → 2026-12-01 .. 2027-03-31.

## Two-Digit Years

Two-digit years fall in a 100-year window around the workdate:
`workdate.year + pivot_year - 100` .. `workdate.year + pivot_year - 1`.

```python
parse_period("26", wd, "it")                # 2026
parse_period("26", wd, "it", pivot_year=0)  # 1926
```

## Languages

Italian and English ship in `genro_toolbox/dates/locales/`. A language is one
JSON file with these keys:

- `months`, `weekdays`, `quarters`: name → number (Monday = 0);
- `keywords`: key → list of phrases (`today`, `last_week`, `from`, `to`,
  `articles`, `no_period`, ...);
- `date_order`: `"default"` plus region overrides, e.g.
  `{"default": "MDY", "GB": "DMY"}`.

English keywords are accepted in every language. To add a language, copy
`it.json`, translate it, and pass its folder:

```python
parse_period("aujourd'hui", wd, "fr", locale_dir="my_locales/")
```

A missing file or key raises `PeriodLocaleError`, which is not a
`PeriodError`.

## Differences from GenroPy decodeDatePeriod

- A month without year on the end side is the workdate's year (legacy moved it to the past).
- `<month> scorso/prossimo` work (legacy ignored the word).
- Quarters accept `q`/`t` forms with a year (legacy failed).
- `tra`/`fra`, `10 gennaio 2026` and `january 10, 2026` are accepted.
- Commas no longer separate bounds (`2024,2025` is an error).
- One `pivot_year` window on the workdate for all two-digit years.
- Keywords match whole words; times (`oggi alle 10:00`) are rejected.
- Only shipped or provided languages are supported.
