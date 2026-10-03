# API Reference

Complete API documentation for Genro-Toolbox.

## extract_kwargs

```{eval-rst}
.. autofunction:: genro_toolbox.extract_kwargs
```

### Function Signature

```python
def extract_kwargs(
    _adapter: Optional[str] = None,
    _dictkwargs: Optional[Dict[str, Any]] = None,
    **extraction_specs: Any
) -> Callable[[F], F]
```

### Parameters

**_adapter** : `Optional[str]`
: Name of a method on `self` that will be called to pre-process `kwargs` before extraction.
  The adapter method receives the `kwargs` dict and can modify it in-place.

**_dictkwargs** : `Optional[Dict[str, Any]]`
: Optional dictionary of extraction specifications. When provided, this is used instead of `**extraction_specs`.
  Useful for dynamic extraction specifications.

**extraction_specs** : `Any`
: Keyword arguments where keys are prefix names and values specify extraction behavior:
  - `True`: Extract parameters with this prefix and remove them from source (`pop=True`)
  - `dict`: Custom extraction options (`pop`, `slice_prefix`)

### Returns

**Callable[[F], F]**
: Decorated function that performs kwargs extraction

### Examples

See [extract_kwargs Guide](../user-guide/extract-kwargs.md) for detailed examples.

## metadata

```{eval-rst}
.. autofunction:: genro_toolbox.metadata
```

### Function Signature

```python
def metadata(*, prefix: str | None = None, **attributes: Any) -> Callable[[T], T]
```

### Parameters

**prefix** : `str | None`
: Keyword-only. When given, each attribute name becomes `<prefix>_<key>`. Default: `None`.

**attributes** : `Any`
: Keyword arguments written onto the target with `setattr`.

### Returns

**Callable[[T], T]**
: A decorator that sets the attributes and returns the target itself (no wrapper).

### Raises

Nothing of its own. `setattr` errors on the target propagate (e.g. on an object with `__slots__`).

### Examples

```python
from genro_toolbox import metadata

@metadata(prefix="rpc", public=True)
def handler():
    pass

handler.rpc_public  # True
```

See [metadata Guide](../user-guide/metadata.md) for detailed examples.

## safe_is_instance

```{eval-rst}
.. autofunction:: genro_toolbox.safe_is_instance
```

### Function Signature

```python
def safe_is_instance(obj: Any, class_name: str) -> bool
```

### Parameters

**obj** : `Any`
: Object to check

**class_name** : `str`
: Fully qualified class name (e.g., "builtins.int", "package.module.ClassName")

### Returns

**bool**
: True if obj is an instance of the class, False otherwise

### Examples

See [safe_is_instance Guide](../user-guide/safe-is-instance.md) for detailed examples.

## tags_match

```{eval-rst}
.. autofunction:: genro_toolbox.tags_match
```

### Function Signature

```python
def tags_match(
    rule: str,
    values: set[str],
    *,
    max_length: int = 200,
    max_depth: int = 6,
) -> bool
```

### Parameters

**rule** : `str`
: Boolean expression string (e.g., `"admin&!internal"`).

**values** : `set[str]`
: Set of tag strings to match against.

**max_length** : `int`
: Maximum allowed length for the rule string. Default: 200.

**max_depth** : `int`
: Maximum nesting depth for parentheses. Default: 6.

### Returns

**bool**
: True if the expression matches the given values.

### Raises

**RuleError**
: If the rule is invalid or exceeds limits.

### Operators

| Symbol | Keyword | Meaning |
|--------|---------|---------|
| `,` or `\|` | `or` | OR (either matches) |
| `&` | `and` | AND (both must match) |
| `!` | `not` | NOT (must not match) |
| `()` | - | Grouping |

### Grammar

```text
expr     := or_expr
or_expr  := and_expr (('|' | ',' | 'or') and_expr)*
and_expr := not_expr (('&' | 'and') not_expr)*
not_expr := ('!' | 'not') not_expr | primary
primary  := '(' expr ')' | TAG
TAG      := [a-zA-Z_][a-zA-Z0-9_]* (excluding keywords)
```

### Examples

See [tags_match Guide](../user-guide/tags-match.md) for detailed examples.

## RuleError

```{eval-rst}
.. autoclass:: genro_toolbox.RuleError
```

Exception raised when a tag expression is invalid.

Inherits from `ValueError`.

## get_uuid

```{eval-rst}
.. autofunction:: genro_toolbox.get_uuid
```

### Function Signature

```python
def get_uuid() -> str
```

### Returns

**str**
: 22-character sortable unique identifier.

### Format

The ID consists of:
- `Z`: Version marker (distinguishes from legacy UUIDs, sorts after them)
- 9 characters: microseconds since 2025-01-01 UTC (base62 encoded)
- 12 characters: cryptographically secure random (base62 encoded)

### Properties

- Lexicographically sortable by creation time (UTC)
- URL-safe (alphanumeric only)
- 22 characters (compatible with legacy Genro ID columns)
- Timestamp valid for ~440 years from 2025
- Collision probability ~10^-19 for same microsecond

### Examples

```python
from genro_toolbox import get_uuid

uid = get_uuid()  # e.g., "Z00005KmLxHj7F9aGbCd3e"
len(uid)          # 22
uid[0]            # 'Z'
uid.isalnum()     # True

# IDs are sortable by time
ids = [get_uuid() for _ in range(3)]
sorted(ids) == ids  # True
```

## smartasync

```{eval-rst}
.. autofunction:: genro_toolbox.smartasync
```

### Function Signature

```python
def smartasync(method: Callable) -> Callable
```

### Parameters

**method** : `Callable`
: Method or function to decorate (async or sync).

### Returns

**Callable**
: Wrapped function that works in both sync and async contexts.

### How It Works

Automatically detects the execution context and adapts:

| Context | Method | Behavior |
|---------|--------|----------|
| Sync | Async | `asyncio.run()` |
| Sync | Sync | Direct call |
| Async | Async | Return coroutine (for await) |
| Async | Sync | `asyncio.to_thread()` |

### Features

- Auto-detection of sync/async context using `asyncio.get_running_loop()`
- Asymmetric caching: caches True (async), always checks False (sync)
- Works with both class methods and standalone functions
- Compatible with `__slots__` classes

### Examples

```python
from genro_toolbox import smartasync

class DataManager:
    @smartasync
    async def fetch_data(self, url: str):
        async with httpx.AsyncClient() as client:
            return await client.get(url).json()

manager = DataManager()

# Sync context - no await needed
data = manager.fetch_data("https://api.example.com")

# Async context - use await
async def main():
    data = await manager.fetch_data("https://api.example.com")
```

### Cache Reset

For testing, clear the per-thread event loops:

```python
from genro_toolbox import reset_smartasync_cache

reset_smartasync_cache()
```

## smartsplit

```{eval-rst}
.. autofunction:: genro_toolbox.smartsplit
```

### Function Signature

```python
def smartsplit(path: str, separator: str) -> list[str]
```

### Parameters

**path** : `str`
: The string to split.

**separator** : `str`
: The separator substring.

### Returns

**list[str]**
: List of substrings with whitespace stripped. Escaped separators (prefixed with `\`) are preserved.

### Examples

```python
from genro_toolbox import smartsplit

smartsplit("a.b.c", ".")          # ['a', 'b', 'c']
smartsplit(r"a\.b.c", ".")        # ['a\\.b', 'c']
smartsplit("one , two , three", ",")  # ['one', 'two', 'three']
```

## smarttimer

```{eval-rst}
.. automodule:: genro_toolbox.smarttimer
   :members: set_timeout, set_interval, cancel_timer
```

### set_timeout

```python
def set_timeout(delay: float, callback: Callable, *args, **kwargs) -> str
```

Schedule a one-shot callback after `delay` seconds. Returns a timer ID for cancellation.

**Parameters**:
- `delay`: Seconds to wait before executing callback
- `callback`: Function to call (sync or async)
- `*args, **kwargs`: Arguments forwarded to callback

**Returns**: `str` — Timer ID

### set_interval

```python
def set_interval(delay: float, callback: Callable, *args,
                 initial_delay: float | None = None, **kwargs) -> str
```

Schedule a repeating callback every `delay` seconds. Returns a timer ID for cancellation.

**Parameters**:
- `delay`: Seconds between each callback execution
- `callback`: Function to call (sync or async)
- `initial_delay`: Delay before first execution (defaults to `delay`)
- `*args, **kwargs`: Arguments forwarded to callback

**Returns**: `str` — Timer ID

### cancel_timer

```python
def cancel_timer(timer_id: str) -> bool
```

Cancel a timer by its ID.

**Parameters**:
- `timer_id`: The ID returned by `set_timeout` or `set_interval`

**Returns**: `True` if the timer was found and cancelled, `False` otherwise

### Context Detection

| Context | Callback | Strategy |
|---------|----------|----------|
| Sync | Sync | threading.Timer, direct call |
| Sync | Async | threading.Timer, temp event loop |
| Async | Async | asyncio task, await |
| Async | Sync | asyncio task, to_thread |

### Examples

```python
from genro_toolbox import set_timeout, set_interval, cancel_timer

# One-shot
tid = set_timeout(2.0, print, "Hello!")

# Repeating
tid = set_interval(1.0, print, "tick")
cancel_timer(tid)

# Async callback
async def notify(msg):
    await send_notification(msg)

set_timeout(5.0, notify, "done")
```

---

## smartretry

```{eval-rst}
.. autofunction:: genro_toolbox.smartretry
```

### Function Signature

```python
def smartretry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    on: tuple[type[BaseException], ...] = (Exception,),
) -> Callable
```

### Parameters

**max_attempts** : `int`
: Maximum number of attempts, the first call included. Default: 3.

**delay** : `float`
: Seconds to wait before the first retry. Default: 1.0.

**backoff** : `float`
: Multiplier applied to the wait after each retry. Default: 2.0.

**jitter** : `bool`
: When `True`, each wait is multiplied by a random factor in [1.0, 1.1). Default: `True`.

**on** : `tuple[type[BaseException], ...]`
: Exception types that trigger a retry. Other exceptions propagate at once. Default: `(Exception,)`.

### Returns

**Callable**
: A decorator. It returns an async wrapper for a coroutine function, a sync wrapper otherwise.

### Raises

**TypeError**
: If used without parentheses (`@smartretry` instead of `@smartretry()`).

The decorated function raises the exception of its last attempt when all attempts fail.

### Examples

```python
from genro_toolbox import smartretry

@smartretry(max_attempts=3, delay=0.1, on=(ConnectionError,))
def ping():
    return "pong"

ping()  # 'pong'
```

See [smartretry Guide](../user-guide/smartretry.md) for detailed examples.

## retry_call

```{eval-rst}
.. autofunction:: genro_toolbox.retry_call
```

### Function Signature

```python
def retry_call(
    func: Callable,
    args: tuple = (),
    kwargs: dict[str, Any] | None = None,
    *,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    on: tuple[type[BaseException], ...] = (Exception,),
    policy: dict[str, Any] | None = None,
) -> Any
```

### Parameters

**func** : `Callable`
: The function to call, sync or async.

**args** : `tuple`
: Positional arguments for `func`. Default: `()`.

**kwargs** : `dict[str, Any] | None`
: Keyword arguments for `func`. Default: `None` (no keyword arguments).

**max_attempts**, **delay**, **backoff**, **jitter**, **on**
: Same meaning as in [smartretry](#smartretry).

**policy** : `dict[str, Any] | None`
: A dict with any of the keys `max_attempts`, `delay`, `backoff`, `jitter`, `on`.
  Its keys override the keyword arguments. Typically a value of `RETRY_PRESETS`.

### Returns

**Any**
: The result of `func`. For an async `func`, a coroutine to await.

### Raises

The exception of the last attempt when all attempts fail.

### Examples

```python
from genro_toolbox import retry_call, RETRY_PRESETS

def add(a, b):
    return a + b

retry_call(add, (2, 3))  # 5
retry_call(add, (2, 3), policy=RETRY_PRESETS["network"])  # 5
```

## RETRY_PRESETS

`dict[str, dict[str, Any]]` with three predefined policies for `retry_call(policy=...)`
or `smartretry(**preset)`.

| Preset | `max_attempts` | `delay` | `backoff` | `jitter` | `on` |
|---|---|---|---|---|---|
| `network` | 3 | 1.0 | 2.0 | True | `ConnectionError`, `TimeoutError`, `OSError` |
| `aggressive` | 5 | 0.5 | 2.0 | True | `Exception` |
| `gentle` | 2 | 2.0 | 1.5 | False | `ConnectionError`, `TimeoutError` |

## sign

```{eval-rst}
.. autofunction:: genro_toolbox.sign
```

### Function Signature

```python
def sign(payload: str, key: str, expires_in: int | None = None) -> str
```

### Parameters

**payload** : `str`
: The string to protect. Any content is allowed.

**key** : `str`
: Secret key. Keep it server-side.

**expires_in** : `int | None`
: Lifetime in seconds. `None` means no expiry. Default: `None`.

### Returns

**str**
: The token `<payload>.<expiry>.<signature>`, three base64url fields. The payload is encoded, not encrypted.

### Raises

**ValueError**
: If `key` is empty, or `expires_in` is zero or negative.

### Examples

```python
from genro_toolbox import sign

sign("hello", key="secret")  # 'aGVsbG8..fWq4jxqaMCKOVQynnV5s3vNU93bfSRtZgxQdJ6kugHo'
```

See [Signing Guide](../user-guide/signing.md) for detailed examples.

## verify

```{eval-rst}
.. autofunction:: genro_toolbox.verify
```

### Function Signature

```python
def verify(token: str, key: str) -> str
```

### Parameters

**token** : `str`
: A token produced by `sign`.

**key** : `str`
: The same secret key used to sign.

### Returns

**str**
: The original payload, unchanged.

### Raises

**ValueError**
: If `key` is empty.

**SignatureExpired**
: The signature is valid but the token has expired.

**SignatureError**
: The token is malformed, or the signature does not match.

### Examples

```python
from genro_toolbox import sign, verify, SignatureError

token = sign("/srv/data", key="secret", expires_in=300)
verify(token, key="secret")  # '/srv/data'

try:
    verify(token, key="wrong")
except SignatureError:
    rejected = True

rejected  # True
```

## SignatureError

```{eval-rst}
.. autoclass:: genro_toolbox.SignatureError
```

Raised by `verify` when the token is malformed or its signature does not match.

Inherits from `Exception`.

## SignatureExpired

```{eval-rst}
.. autoclass:: genro_toolbox.SignatureExpired
```

Raised by `verify` when the signature is valid but the token's expiry has passed.

Inherits from `SignatureError`.

---

## dictExtract

Utility function for extracting dict items by key prefix. Used internally by `extract_kwargs`.

```python
def dictExtract(
    source_dict: dict,
    prefix: str,
    pop: bool = False,
    slice_prefix: bool = True,
) -> dict
```

Returns a dict of items with keys starting with prefix.

---

## dates.parse_period

Parse a natural-language date period. Exported from `genro_toolbox.dates` only.

### Function Signature

```python
def parse_period(
    text: str,
    workdate: datetime.date,
    locale: str,
    pivot_year: int = 20,
    locale_dir: Path | str | None = None,
) -> DatePeriod
```

### Parameters

- **text**: the period, e.g. `"mese scorso"`, `"today;today+7"`, `"from Q1 to Q2"`.
- **workdate**: the date relative expressions refer to.
- **locale**: `it`, `en`, or with region (`en_GB`, `it-IT`); the region selects the numeric date order.
- **pivot_year**: two-digit years fall in `workdate.year + pivot_year - 100` .. `workdate.year + pivot_year - 1`.
- **locale_dir**: folder with `<language>.json` files; default is the shipped `dates/locales/`.

### Returns

`DatePeriod(start, end)`, a `NamedTuple` of `datetime.date | None`. `None` is an open bound; both `None` means no period.

### Raises

- **PeriodError** (`ValueError`): the text is not recognized; attributes `value`, `locale`.
- **PeriodLocaleError**: the language file is missing or lacks a key. Not a `PeriodError`.

---

## Type Definitions

```python
F = TypeVar('F', bound=Callable[..., Any])
```

Type variable for decorated function preservation.

---

## See Also

- [User Guide](../user-guide/extract-kwargs.md) - Complete feature documentation
- [Examples](../examples/index.md) - Real-world usage examples
- [Best Practices](../user-guide/best-practices.md) - Production patterns
