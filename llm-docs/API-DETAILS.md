# genro-toolbox API Reference

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

### filtered_dict

```python
def filtered_dict(
    data: Mapping[str, Any] | None,
    filter_fn: Callable[[str, Any], bool] | None = None,
) -> dict[str, Any]: ...
```

### dictExtract

```python
def dictExtract(
    mydict: dict,
    prefix: str,
    pop: bool = False,
    slice_prefix: bool = True,
    is_list: bool = False,  # unused
) -> dict: ...
```
