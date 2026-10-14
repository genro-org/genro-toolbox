# genro-toolbox - LLM Quick Reference

Zero-dependency Python utilities for the Genro Kyō ecosystem.

## Installation

```bash
pip install genro-toolbox
```

## Core API

```python
from genro_toolbox import (
    extract_kwargs,         # Decorator: group kwargs by prefix
    safe_is_instance,       # isinstance() without import
    dictExtract,            # Extract dict subset by prefix
    NamedList,              # Mutable values with a shared name-to-position index
    tags_match,             # Boolean expression matcher for tags
)
```

## Quick Examples

### NamedList (0.18.0+)

```python
row = NamedList({"code": 0, "total": 1}, ["ABC", 10])
row["total"] = 20
assert row[1] == 20
assert tuple(row) == ("ABC", 20)
assert dict(row) == {"code": "ABC", "total": 20}
```

Construction validates unique integer positions `0 .. len(index)-1` and an
equal number of values, raising `ValueError` for inconsistent input.
`values=None` initializes all fields to `None`; the index is shared by reference.
Later index growth can leave sibling rows shorter, with implicit `None` fields.
See [API details](API-DETAILS.md#namedlist) for legacy limitations.

### extract_kwargs

```python
@extract_kwargs(logging=True, cache=True)
def func(name, logging_kwargs=None, cache_kwargs=None, **kwargs):
    return logging_kwargs, cache_kwargs

func("x", logging_level="INFO", cache_ttl=300, other=1)
# logging_kwargs = {"level": "INFO"}
# cache_kwargs = {"ttl": 300}
# kwargs = {"other": 1}
```

### safe_is_instance

```python
safe_is_instance(42, "builtins.int")           # True
safe_is_instance(obj, "mymodule.MyClass")      # True (includes subclasses)
```
