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
    tags_match,             # Boolean expression matcher for tags
)
```

## Quick Examples

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
