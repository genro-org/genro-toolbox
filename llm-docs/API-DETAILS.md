# genro-toolbox API Reference

## NamedList

```python
from genro_toolbox import NamedList

row = NamedList(index={"code": 0, "total": 1}, values=["ABC", 10])
```

Available since 0.18.0. A `list` subclass with a shared name-to-position index,
without SQL or external dependencies.

- `row[name]` / `row[position]`: read or assign; a new name adds a field.
- Iteration/unpacking yield values; `dict(row)` explicitly converts by name.
- Constructor positions must be unique plain integers `0 .. len(index)-1`;
  supplied values must have exactly the same length. Violations raise `ValueError`.
- `values=None` creates one `None` per column; iterable values are copied once.
- `keys()` / `items()` follow position order; `iteritems()` follows index insertion order.
- `values()` returns a tuple padded with `None`; `get(key, default)` handles absent keys.
- `update(mapping)`, `extractItems(columns)`, `extractValues(columns)` and `has_key(key)`
  preserve their legacy behavior. Falsy extraction columns mean all columns.
- The index is retained by reference. Later growth leaves unmodified sibling rows
  physically short: named reads return `None`, but `items()` and `repr()` can fail.
- Deepcopy of an entire result preserves sharing within the copy and isolates it
  from the original; slicing and `copy()` return plain lists.
- Structural mutations do not reindex. `pop` is deprecated. Failed positional
  writes can pad short rows; slice errors can be masked. Updates are nontransactional.

See the [full guide](../docs/user-guide/named-list.md) for the tested contract.

## extract_kwargs

```python
def extract_kwargs(
    _adapter: str | None = None,
    _dictkwargs: dict[str, Any] | None = None,
    **extraction_specs: Any
) -> Callable[[F], F]: ...
```

**Parameters**:
- `_adapter`: Method name on `self` to preprocess kwargs
- `_dictkwargs`: Dict alternative to `**extraction_specs`
- `**extraction_specs`: Prefix specifications
  - `prefix=True`: Extract and pop (default)
  - `prefix={'pop': False}`: Extract but keep in kwargs
  - `prefix={'slice_prefix': False}`: Keep prefix in keys

**Behavior**:
- Creates `{prefix}_kwargs` dict parameter
- Reserved word `class` → `_class`
- Works with methods (self) and functions
- Always returns `{}`, never `None`

**Example specs**:
```python
@extract_kwargs(logging=True, cache={'pop': False})
def func(self, logging_kwargs=None, cache_kwargs=None, **kwargs): ...
```

---

## safe_is_instance

```python
def safe_is_instance(obj: Any, class_full_name: str) -> bool: ...
```

**Parameters**:
- `obj`: Object to check
- `class_full_name`: Full path `"module.ClassName"`

**Behavior**:
- Checks MRO (includes subclasses)
- No import required
- Cached for performance
- Returns `False` for non-existent classes

**Examples**:
```python
safe_is_instance(42, "builtins.int")        # True
safe_is_instance([], "builtins.list")       # True
safe_is_instance(myobj, "pkg.BaseClass")    # True if subclass
```

---

## tags_match

```python
def tags_match(rule: str, values: set[str]) -> bool: ...
```

Match boolean expressions against a set of tags.

**Operators**:
- OR: `,`, `|`, `or`
- AND: `&`, `and`
- NOT: `!`, `not`
- Parentheses for grouping

**Examples**:
```python
tags_match("admin", {"admin", "user"})       # True
tags_match("admin,public", {"public"})       # True (OR)
tags_match("admin&internal", {"admin"})      # False (AND)
tags_match("!admin", {"public"})             # True (NOT)
tags_match("(admin|public)&!internal", {"admin"})  # True
```

---

## Helper Functions

### dictExtract

```python
def dictExtract(
    source_dict: dict,
    prefix: str,
    pop: bool = False,
    slice_prefix: bool = True,
) -> dict: ...
```
