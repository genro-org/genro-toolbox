# smartretry — retry with exponential backoff

Retry a function with exponential backoff, for sync and async code.

## Overview

`smartretry` is a decorator: the call is repeated when it raises one of the
listed exceptions, waiting longer before each new attempt. `retry_call` does
the same for a single call, with the configuration chosen at runtime.
`RETRY_PRESETS` holds three ready-made configurations.

**Key Features**:

- Exponential backoff: the delay is multiplied by `backoff` after each retry
- Optional jitter: 0-10% random extra on each delay
- Retry only on the exception types you choose
- Sync or async detected at decoration time
- When all attempts fail, the last exception is raised

## Basic Usage

```python
from genro_toolbox import smartretry

calls = 0

@smartretry(max_attempts=3, delay=0.1)
def fetch():
    global calls
    calls += 1
    if calls < 3:
        raise ConnectionError("server unavailable")
    return "ok"

fetch()  # 'ok'
calls  # 3
```

The parentheses are required, even with no arguments:

```python
from genro_toolbox import smartretry

@smartretry()
def ping():
    return "pong"

ping()  # 'pong'

# @smartretry without parentheses raises:
# TypeError: smartretry requires arguments: use @smartretry() not @smartretry
```

The decorated function keeps its name and docstring (`functools.wraps`).

## Choosing the Exceptions

`on` is a tuple of exception types. Only those are retried; any other
exception propagates at once. The default is `(Exception,)`.

```python
from genro_toolbox import smartretry

attempts = 0

@smartretry(max_attempts=5, delay=0.1, on=(ConnectionError, TimeoutError))
def parse():
    global attempts
    attempts += 1
    raise ValueError("bad input")

try:
    parse()
except ValueError:
    pass

attempts  # 1
```

## When All Attempts Fail

The exception of the last attempt is raised.

```python
from genro_toolbox import smartretry

attempts = 0

@smartretry(max_attempts=2, delay=0.1)
def always_fails():
    global attempts
    attempts += 1
    raise TimeoutError(f"attempt {attempts}")

try:
    always_fails()
except TimeoutError as e:
    message = str(e)

message  # 'attempt 2'
```

## Backoff and Jitter

The wait before retry `n` (counting from 0) is `delay * backoff ** n`. There
is no wait after the last attempt, so `max_attempts` attempts wait
`max_attempts - 1` times.

| Settings | Waits |
|---|---|
| `max_attempts=3, delay=1.0, backoff=2.0` (defaults) | 1.0, 2.0 |
| `max_attempts=4, delay=1.0, backoff=2.0` | 1.0, 2.0, 4.0 |
| `max_attempts=3, delay=0.5, backoff=1.0` | 0.5, 0.5 |

With `jitter=True` (the default) each wait is multiplied by a random factor
between 1.0 and 1.1. Several clients retrying the same server then do not all
retry at the same instant. Use `jitter=False` for exact waits.

## Async Functions

A coroutine function gets an async wrapper that waits with `asyncio.sleep`, so
the event loop is not blocked.

```python
import asyncio
from genro_toolbox import smartretry

calls = 0

@smartretry(max_attempts=3, delay=0.1)
async def fetch_async():
    global calls
    calls += 1
    if calls < 2:
        raise ConnectionError("server unavailable")
    return "ok"

asyncio.run(fetch_async())  # 'ok'
```

## retry_call: Configuration at Runtime

`retry_call` applies the retry to one call. Positional arguments go in `args`
(a tuple), keyword arguments in `kwargs` (a dict).

```python
from genro_toolbox import retry_call

calls = 0

def divide(a, b, scale=1):
    global calls
    calls += 1
    if calls < 2:
        raise ConnectionError("server unavailable")
    return a / b * scale

retry_call(divide, (10, 4), {"scale": 2}, max_attempts=3, delay=0.1)  # 5.0
```

With an async function, `retry_call` returns a coroutine to await:

```python
import asyncio
from genro_toolbox import retry_call

async def double(x):
    return x * 2

async def main():
    return await retry_call(double, (21,))

asyncio.run(main())  # 42
```

## Presets

`RETRY_PRESETS` maps a name to a configuration dict.

| Preset | `max_attempts` | `delay` | `backoff` | `jitter` | `on` |
|---|---|---|---|---|---|
| `network` | 3 | 1.0 | 2.0 | True | `ConnectionError`, `TimeoutError`, `OSError` |
| `aggressive` | 5 | 0.5 | 2.0 | True | `Exception` |
| `gentle` | 2 | 2.0 | 1.5 | False | `ConnectionError`, `TimeoutError` |

Pass a preset to `retry_call` as `policy`:

```python
from genro_toolbox import retry_call, RETRY_PRESETS

def read_status():
    return "up"

retry_call(read_status, policy=RETRY_PRESETS["network"])  # 'up'
```

Keys present in `policy` override the keyword arguments, including keywords
passed explicitly. Missing keys keep the keyword values.

```python
from genro_toolbox import retry_call, RETRY_PRESETS

attempts = 0

def unreachable():
    global attempts
    attempts += 1
    raise ConnectionError("down")

try:
    retry_call(unreachable, max_attempts=10, policy={"max_attempts": 2, "delay": 0.1})
except ConnectionError:
    pass

attempts  # 2

# A preset with one value changed
fast_network = {**RETRY_PRESETS["network"], "delay": 0.1}
fast_network["max_attempts"]  # 3
```

A preset dict also works with the decorator, by unpacking it:

```python
from genro_toolbox import smartretry, RETRY_PRESETS

@smartretry(**RETRY_PRESETS["gentle"])
def load_config():
    return {"debug": False}

load_config()  # {'debug': False}
```

## API Reference

```python
def smartretry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    on: tuple[type[BaseException], ...] = (Exception,),
) -> Callable: ...

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
) -> Any: ...

RETRY_PRESETS: dict[str, dict[str, Any]]
```

## See Also

- [smarttimer Guide](smarttimer.md) - Non-blocking timers
- [smartasync Guide](smartasync.md) - Unified sync/async API
- [API Reference](../api/reference.md) - Complete API documentation
