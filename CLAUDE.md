# Claude Code Instructions - Genro-Toolbox

## Project Context

**genro-toolbox** is a lightweight, zero-dependency Python library providing essential utilities for the Genro ecosystem (Genro Kyō).

Part of **genro-modules** (Apache 2.0 license).

## Repository Structure

```
genro-toolbox/
├── src/genro_toolbox/
│   ├── __init__.py      # Public API exports
│   ├── dates/           # parse_period (natural-language periods) + locales/*.json
│   ├── decorators.py    # extract_kwargs decorator
│   ├── dict_utils.py    # dictExtract
│   └── typeutils.py     # safe_is_instance
├── tests/
│   ├── test_decorators.py
│   ├── test_dict_utils.py
│   └── test_typeutils.py
├── js/                  # @genrojs/toolbox (npm) / @genro/toolbox (JSR)
│   ├── src/dates/       # parseDateExpression; locales.js is generated
│   ├── scripts/         # build-locales.js (JSON -> locales.js)
│   └── test/            # node --test; corpus read from tests/data/
├── package.json, jsr.json  # JS package metadata, same version as pyproject
├── pyproject.toml
├── LICENSE              # Apache 2.0
└── README.md
```

## Public API

```python
from genro_toolbox import (
    extract_kwargs,      # Decorator for kwargs extraction by prefix
    safe_is_instance,    # Type check without importing
)
```

## Development

### Running Tests

```bash
pytest tests/
pytest tests/ --cov=src/genro_toolbox --cov-report=term-missing
```

```bash
npm test                 # JavaScript tests, including the shared corpus
npm run build:locales    # after editing src/genro_toolbox/dates/locales/*.json
```

A release bumps the version in pyproject.toml, `__init__.py`, package.json and
jsr.json together; the `v*` tag publishes PyPI, npm and JSR.

### Code Style

- Python 3.11+
- Type hints required
- English for all code, comments, and commit messages

## Philosophy

> If you write a generic helper that could be useful elsewhere, put it in genro-toolbox.

This library is the **foundation** for utilities shared across:
- genro-asgi
- genro-routes
- genro-api
- Other Genro Kyō projects

## Key Design Principles

1. **Zero dependencies** - Only Python standard library
2. **Type-safe** - Full type hints
3. **Well-tested** - 100% test coverage goal
4. **Minimal** - Only essential utilities

## Git Commit Authorship

- **NEVER** include Claude as a co-author in commits
- **ALWAYS** remove the "Co-Authored-By: Claude" line

## Language Policy

- All code, comments, and commit messages in **English**
