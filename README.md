<p align="center">
  <img src="docs/assets/logo.png" alt="Genro-Toolbox Logo" width="200">
</p>

<p align="center">
  <a href="https://badge.fury.io/py/genro-toolbox"><img src="https://badge.fury.io/py/genro-toolbox.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/genro-toolbox/"><img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python 3.11+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://github.com/genropy/genro-toolbox/actions/workflows/test.yml"><img src="https://github.com/genropy/genro-toolbox/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://codecov.io/gh/genropy/genro-toolbox"><img src="https://codecov.io/gh/genropy/genro-toolbox/graph/badge.svg" alt="codecov"></a>
  <a href="https://genro-toolbox.readthedocs.io/"><img src="https://readthedocs.org/projects/genro-toolbox/badge/?version=latest" alt="Documentation"></a>
  <a href="llm-docs/"><img src="https://img.shields.io/badge/LLM%20Docs-available-brightgreen" alt="LLM Docs"></a>
</p>

# Genro-Toolbox

> Essential utilities for the Genro ecosystem

Part of [Genro Kyō](https://github.com/genropy) ecosystem.

A lightweight, zero-dependency Python library providing core utilities that can be used across all Genro projects.

📚 **[Full Documentation](https://genro-toolbox.readthedocs.io/)**

## Installation

```bash
pip install genro-toolbox
```

## Features

- **extract_kwargs** - Decorator to group kwargs by prefix
- **metadata** - Decorator to stamp keyword arguments as attributes on functions or classes
- **dictExtract** - Extract dict items by key prefix
- **smartsplit** - Split strings honoring escaped separators
- **get_uuid** - Sortable 22-char unique identifiers for distributed systems
- **sign / verify** - HMAC-signed payloads with optional expiry, for data that leaves the server and comes back
- **smartasync** - Unified sync/async API with automatic context detection
- **safe_is_instance** - isinstance() without importing the class
- **tags_match** - Boolean expression matcher for tag-based filtering
- **dates.parse_period** - Natural-language date periods ("mese scorso", "from Q1 to Q2") to a start/end date pair, multilingual

## Examples

### extract_kwargs Decorator

```python
from genro_toolbox import extract_kwargs

@extract_kwargs(logging=True, cache=True)
def my_function(name, logging_kwargs=None, cache_kwargs=None, **kwargs):
    print(f"logging: {logging_kwargs}")
    print(f"cache: {cache_kwargs}")

my_function(
    "test",
    logging_level="INFO",
    logging_format="json",
    cache_ttl=300,
)
# logging: {'level': 'INFO', 'format': 'json'}
# cache: {'ttl': 300}
```

### metadata Decorator

Stamp keyword arguments as attributes on a function or class:

```python
from genro_toolbox import metadata

@metadata(mixin_order=10)
class Core:
    pass

Core.mixin_order        # 10

@metadata(prefix="rpc", public=True)
def handler():
    pass

handler.rpc_public      # True
```

### safe_is_instance

```python
from genro_toolbox import safe_is_instance

# Check type without importing
safe_is_instance(42, "builtins.int")              # True
safe_is_instance(my_obj, "mypackage.BaseClass")   # True (includes subclasses)
```

### tags_match

```python
from genro_toolbox import tags_match

# Simple tag check
tags_match("admin", {"admin", "user"})  # True

# OR (comma, pipe, or keyword)
tags_match("admin,public", {"public"})  # True
tags_match("admin or public", {"admin"})  # True

# AND (ampersand or keyword)
tags_match("admin&internal", {"admin", "internal"})  # True
tags_match("admin and internal", {"admin"})  # False

# NOT (exclamation or keyword)
tags_match("!admin", {"public"})  # True
tags_match("not admin", {"admin"})  # False

# Complex expressions
tags_match("(admin|public)&!internal", {"admin"})  # True
tags_match("(admin or public) and not internal", {"admin", "internal"})  # False
```

### get_uuid

```python
from genro_toolbox import get_uuid

# Generate sortable unique identifiers
uid = get_uuid()  # e.g., "Z00005KmLxHj7F9aGbCd3e"

len(uid)      # 22 characters
uid[0]        # 'Z' (version marker, sorts after legacy UUIDs)
uid.isalnum() # True (URL-safe)

# IDs are lexicographically sortable by creation time
ids = [get_uuid() for _ in range(3)]
sorted(ids) == ids  # True (already sorted)
```

### sign / verify

Authenticate data that leaves the server and comes back — a payload handed to a
client, put in a URL or a cookie, then returned to be acted upon. The key stays
server-side: sign on the way out, verify on the way in.

```python
from genro_toolbox import sign, verify, SignatureError, SignatureExpired

token = sign("/srv/data", key=SECRET, expires_in=300)
# 'L3Nydi9kYXRh.MTc4NTMyMzIyMQ.FmMftICRb9MQVrFUwoo9qPCg-R5SYVpKmXA2oXQdmLg'

verify(token, key=SECRET)   # '/srv/data'
```

Tampering and expiry are both rejected:

```python
try:
    path = verify(token_from_client, key=SECRET)
except SignatureExpired:
    ...   # signature was valid, the token is just too old
except SignatureError:
    ...   # forged, altered, or signed with another key
```

The token is three base64url fields joined by `.`, so the payload round-trips
byte for byte whatever it contains — separators, unicode, XML-unsafe characters:

```python
payload = '{"exclude": "*.tmp;*.bak"}'
verify(sign(payload, key=SECRET), key=SECRET) == payload  # True
```

The expiry sits inside the signed area, so it cannot be stripped or extended.
Omit `expires_in` for a token that never expires.

### smartasync

```python
from genro_toolbox import smartasync

class DataManager:
    @smartasync
    async def fetch_data(self, url: str):
        async with httpx.AsyncClient() as client:
            return await client.get(url).json()

manager = DataManager()

# Sync context - no await needed!
data = manager.fetch_data("https://api.example.com")

# Async context - use await
async def main():
    data = await manager.fetch_data("https://api.example.com")

# Also works with sync methods in async context (offloaded to thread)
class LegacyProcessor:
    @smartasync
    def cpu_intensive(self, data):
        return process(data)  # Blocking operation

async def main():
    proc = LegacyProcessor()
    result = await proc.cpu_intensive(data)  # Won't block event loop
```

### smartsplit

```python
from genro_toolbox import smartsplit

smartsplit("a.b.c", ".")          # ['a', 'b', 'c']
smartsplit(r"a\.b.c", ".")        # ['a\\.b', 'c']  (escaped separator preserved)
smartsplit("one , two , three", ",")  # ['one', 'two', 'three']  (strips whitespace)
```

### dictExtract

```python
from genro_toolbox import dictExtract

kwargs = {"logging_level": "INFO", "logging_format": "json", "cache_ttl": 300}
dictExtract(kwargs, "logging_")  # {'level': 'INFO', 'format': 'json'}
```

### dates.parse_period

Parses a period written in natural language into a start and an end date,
relative to a workdate. Either bound may be `None` (open period); both `None`
means no filter. Unrecognized text raises `PeriodError` (a `ValueError`)
carrying `value` and `locale`.

```python
from datetime import date
from genro_toolbox.dates import parse_period

wd = date(2026, 4, 15)
parse_period("mese scorso", wd, "it")          # 2026-03-01 .. 2026-03-31
parse_period("oggi-30;", wd, "it")             # 2026-03-16 .. None
parse_period("from january to march", wd, "en")
parse_period("ottobre scorso", wd, "it")       # 2025-10-01 .. 2025-10-31
parse_period("Q1 2024", wd, "en")              # 2024-01-01 .. 2024-03-31
parse_period("10/1/26", wd, "it")              # 2026-01-10 .. 2026-01-10
```

Supported forms: years, `today`/`oggi` with `+n`/`-n`, this/last/next week and
month, quarters, months with year or `last`/`next`, weekdays, ISO and locale
dates, ranges with `;` or `from ... to` / `dal ... al`. The full rules are in
the `genro_toolbox.dates.period_parser` module docstring. Two-digit years use a
window around the workdate set by `pivot_year` (default 20).

Languages live in JSON files (`genro_toolbox/dates/locales/it.json`,
`en.json`). To add one, write `<language>.json` with the same keys; pass
`locale_dir=` to load it from your own folder. A missing file or key raises
`PeriodLocaleError`.

## Philosophy

> If you write a generic helper that could be useful elsewhere, put it in genro-toolbox.

This library serves as the foundation for utilities shared across:

- genro-asgi
- genro-routes
- genro-api
- Other Genro Kyō projects

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

Copyright 2025 Softwell S.r.l.
