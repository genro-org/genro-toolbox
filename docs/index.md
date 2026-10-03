<div align="center">
  <img src="_static/logo.png" alt="Genro-Toolbox Logo" width="200"/>
</div>

# Genro-Toolbox

**Essential utilities for the Genro ecosystem (Genro Kyō)**

Genro-Toolbox is a lightweight, zero-dependency Python library providing core utilities for Genro Kyō (genro-asgi, genro-routes, genro-api, etc.). Think of it as the foundation from which Genro solutions are built.

## Features

- **`extract_kwargs`** - Decorator for extracting and grouping keyword arguments by prefix
- **`metadata`** - Decorator to stamp keyword arguments as attributes on functions or classes
- **`dictExtract`** - Extract dict items by key prefix
- **`smartsplit`** - Split strings honoring escaped separators
- **`tags_match`** - Boolean expression matcher for tag-based filtering
- **`get_uuid`** - Sortable 22-char unique identifiers for distributed systems
- **`smartasync`** - Unified sync/async API decorator with automatic context detection
- **`smarttimer`** - Non-blocking timers (set_timeout/set_interval) for async code
- **`safe_is_instance`** - Type checking without imports
- **`smartretry`** - Retry decorator with exponential backoff for sync and async functions
- **`sign` / `verify`** - HMAC-signed payloads with optional expiry
- **`dates.parse_period`** - Natural-language date periods to a start/end pair, multilingual
- **Zero dependencies** - Pure Python standard library only
- **Full type hints** - Complete typing support
- **Python 3.11+** - Modern Python

## Quick Example

```python
from genro_toolbox import extract_kwargs

@extract_kwargs(logging=True, cache=True)
def setup_service(name, logging_kwargs=None, cache_kwargs=None, **kwargs):
    print(f"Logging config: {logging_kwargs}")
    print(f"Cache config: {cache_kwargs}")

# All these styles work:
setup_service(
    name="api",
    logging_level="INFO",      # → logging_kwargs={'level': 'INFO'}
    cache_ttl=300,             # → cache_kwargs={'ttl': 300}
)

setup_service(
    name="api",
    logging={'level': 'INFO'},  # Dict style
    cache=True                  # Boolean activation
)
```

```{toctree}
:maxdepth: 2
:caption: Getting Started
:hidden:

self
user-guide/installation
user-guide/quickstart
```

```{toctree}
:maxdepth: 2
:caption: Functions and Arguments
:hidden:

user-guide/extract-kwargs
user-guide/metadata
user-guide/safe-is-instance
```

```{toctree}
:maxdepth: 2
:caption: Async and Timing
:hidden:

user-guide/smartasync
user-guide/smarttimer
user-guide/smartretry
```

```{toctree}
:maxdepth: 2
:caption: Data and Parsing
:hidden:

user-guide/tags-match
user-guide/dates
```

```{toctree}
:maxdepth: 2
:caption: Security
:hidden:

user-guide/signing
```

```{toctree}
:maxdepth: 2
:caption: Guides and Reference
:hidden:

user-guide/best-practices
examples/index
api/reference
faq
```

```{toctree}
:maxdepth: 2
:caption: Project
:hidden:

appendix/architecture
appendix/contributing
```

## Part of Genro Kyō

Genro-Toolbox is part of [Genro Kyō](https://github.com/softwell/meta-genro-modules).

## License

Apache License 2.0 - Copyright © 2025 Softwell Srl
