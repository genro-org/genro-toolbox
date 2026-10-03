# FAQ

## General

### What is genro-toolbox?

Genro-toolbox is a lightweight, zero-dependency Python library providing essential utilities for the Genro Kyō ecosystem. It serves as the foundation for common patterns used across genro-asgi, genro-routes, genro-api, and other Genro projects.

### Why use genro-toolbox instead of writing my own utilities?

1. **Tested** - 88 tests covering all functionality
2. **Zero dependencies** - Only Python standard library
3. **Type-safe** - Full type hints
4. **Consistent** - Same patterns across all Genro projects

### What Python versions are supported?

Python 3.10 and later. We use modern type hints (`|` union syntax, `dict[str, Any]`).

## extract_kwargs

### Why does extract_kwargs always return a dict, never None?

This is by design for consistency. Even when no kwargs match the prefix, you get an empty dict `{}`. This means you can always safely do `logging_kwargs.get("level")` without checking for None first.

### What happens to the reserved word "class"?

Python's `class` keyword is automatically renamed to `_class`:

```python
@extract_kwargs(html=True)
def func(html_kwargs=None, **kwargs):
    return html_kwargs

func(html_class="container")  # Returns {"_class": "container"}
```

### Can I use extract_kwargs on functions (not just methods)?

Yes. The decorator detects whether the first argument is `self` (a method) or not (a function). Both work correctly.

### What's the difference between pop=True and pop=False?

- `pop=True` (default): Extracted kwargs are removed from the original kwargs
- `pop=False`: Extracted kwargs remain in the original kwargs too

```python
@extract_kwargs(logging={'pop': False})
def func(logging_kwargs=None, **kwargs):
    # logging_kwargs = {"level": "INFO"}
    # kwargs = {"logging_level": "INFO", "other": "value"}  # Still contains logging_level
```

## safe_is_instance

### Why not just use isinstance()?

`isinstance()` requires importing the class. `safe_is_instance()` works with the fully qualified class name as a string, avoiding import cycles and allowing type checks without runtime dependencies.

### Does safe_is_instance work with subclasses?

Yes. It checks the entire MRO (Method Resolution Order), so:

```python
class Parent: pass
class Child(Parent): pass

obj = Child()
safe_is_instance(obj, "module.Parent")  # True
safe_is_instance(obj, "module.Child")   # True
```

### Is safe_is_instance cached?

Yes. The MRO lookup is cached using `@lru_cache` for performance. Multiple calls with the same class are fast.

## Troubleshooting

### I get "ModuleNotFoundError: No module named 'genro_toolbox'"

Make sure you've installed the package:

```bash
pip install genro-toolbox
```

### Type hints aren't working in my IDE

Ensure you're using Python 3.10+ and your IDE supports modern type hints. The library uses `dict[str, Any]` syntax (not `Dict[str, Any]`).
