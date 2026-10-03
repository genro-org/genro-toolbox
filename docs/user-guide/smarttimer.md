# smarttimer — non-blocking timers

The `smarttimer` module provides `setTimeout`/`setInterval` semantics (like JavaScript) for **async** Python code. Timers are `asyncio` tasks on the running event loop, so they must be created inside a running loop: called anywhere else, `set_timeout` and `set_interval` raise `RuntimeError`.

## Overview

```mermaid
flowchart TD
    A[set_timeout / set_interval] --> B{Running event loop?}
    B -->|No| E[RuntimeError]
    B -->|Yes| D[asyncio task on that loop]
    D --> F{Callback}
    F -->|async| G[awaited]
    F -->|sync| H[asyncio.to_thread]
```

## Installation

`smarttimer` is included in `genro-toolbox`:

```bash
pip install genro-toolbox
```

## API

### set_timeout

Schedule a one-shot callback after `delay` seconds:

```python
from genro_toolbox import set_timeout

timer_id = set_timeout(2.0, print, "Hello!")
# "Hello!" printed after 2 seconds
```

### set_interval

Schedule a repeating callback every `delay` seconds:

```python
from genro_toolbox import set_interval, cancel_timer

timer_id = set_interval(1.0, print, "tick")
# "tick" printed every second until cancelled
cancel_timer(timer_id)
```

Use `initial_delay` to control the delay before the first execution (defaults to `delay`):

```python
# Check immediately (after 1s), then every 30s
tid = set_interval(30.0, check_status, initial_delay=1)
```

### cancel_timer

Cancel a pending timer by its ID. Returns `True` if the timer was found and cancelled, `False` otherwise:

```python
from genro_toolbox import set_timeout, cancel_timer

timer_id = set_timeout(10.0, expensive_task)
cancel_timer(timer_id)  # True — cancelled before firing
cancel_timer(timer_id)  # False — already gone
```

## Callbacks

Timers always run on the event loop; the callback type decides how it is called:

| Callback | How it runs |
|----------|-------------|
| `async def` | awaited in the timer task |
| plain function | `asyncio.to_thread`, so it never blocks the loop |

Outside a running event loop both functions raise:

```python
set_timeout(1.0, print)
# RuntimeError: set_timeout/set_interval require a running async event loop. ...
```

## Real-World Examples

### Token refresh (inside an async server or worker)

Renew an auth token before it expires, without blocking request handling. `set_timeout` is called from a coroutine, so a loop is running; the async `_refresh` is awaited when the timer fires:

```python
from genro_toolbox import set_timeout, cancel_timer

class TokenManager:
    def __init__(self, auth_client):
        self.auth_client = auth_client
        self._refresh_timer = None

    async def on_token_received(self, token, expires_in):
        self.token = token
        # Schedule refresh 5 minutes before expiry
        if self._refresh_timer:
            cancel_timer(self._refresh_timer)
        self._refresh_timer = set_timeout(
            expires_in - 300, self._refresh
        )

    async def _refresh(self):
        new_token = await self.auth_client.refresh()
        await self.on_token_received(new_token, new_token.expires_in)
```

### Heartbeat / keepalive (ASGI server)

Send periodic pings on a WebSocket connection:

```python
from genro_toolbox import set_interval, cancel_timer

class WebSocketHandler:
    def __init__(self, ws):
        self.ws = ws
        self._heartbeat = None

    async def on_connect(self):
        self._heartbeat = set_interval(30.0, self.ws.send_json, {"type": "ping"})

    async def on_disconnect(self):
        if self._heartbeat:
            cancel_timer(self._heartbeat)
```

### Job polling (async worker)

Poll a job queue and stop when the job completes:

```python
from genro_toolbox import set_interval, cancel_timer

pollers = {}

async def check_job(job_id):
    status = await api.get_job_status(job_id)
    if status in ("completed", "failed"):
        cancel_timer(pollers.pop(job_id))
        await handle_result(job_id, status)

async def start_polling(job_id):
    pollers[job_id] = set_interval(5.0, check_job, job_id)
```

## Timer IDs

Each timer gets a unique 22-character ID (from `get_uuid`), suitable for logging and tracking:

```python
tid = set_timeout(5.0, callback)
print(tid)  # e.g., "Z00005KmLxHj7F9aGbCd3e"
```

## Lifetime

A timer lives as long as its event loop. When the loop stops (for example at the end of `asyncio.run()`), pending timers are cancelled with it. `cancel_timer` removes a timer before that; a finished one-shot timer removes itself.
