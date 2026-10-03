# sign / verify — HMAC-signed payloads

Sign a payload with HMAC-SHA256, with an optional expiry, and verify it later.

## Overview

`sign` and `verify` authenticate data that leaves the server and comes back:
a payload handed to a client, put in a URL or a cookie, then returned to be
acted upon. The key stays on the server. Sign on the way out, verify on the
way in.

- `sign(payload, key, expires_in=None)` returns a token string.
- `verify(token, key)` returns the original payload, or raises.
- `SignatureError`: the token is malformed, altered, or signed with another key.
- `SignatureExpired`: the signature is valid but the expiry has passed.
  It is a subclass of `SignatureError`.

Signing does not encrypt: the payload is only base64url-encoded, and anyone
holding the token can read it. Do not put secrets in the payload.

## Basic Usage

```python
from genro_toolbox import sign, verify

SECRET = "server-side-secret"

token = sign("/srv/data", key=SECRET)
verify(token, key=SECRET)  # '/srv/data'
```

The same payload and key always give the same token when there is no expiry:

```python
from genro_toolbox import sign

sign("hello", key="secret")  # 'aGVsbG8..fWq4jxqaMCKOVQynnV5s3vNU93bfSRtZgxQdJ6kugHo'
```

## Expiry

`expires_in` is a lifetime in seconds. Without it the token never expires.

```python
import time
from genro_toolbox import sign, verify, SignatureExpired

SECRET = "server-side-secret"

token = sign("download:report.pdf", key=SECRET, expires_in=1)
verify(token, key=SECRET)  # 'download:report.pdf'

time.sleep(1.1)

try:
    verify(token, key=SECRET)
except SignatureExpired as e:
    message = str(e)

message  # 'Token has expired.'
```

The expiry is inside the signed part of the token, so it cannot be removed
or extended without breaking the signature.

## Rejected Tokens

Catch `SignatureExpired` before `SignatureError`, since it is a subclass.

```python
from genro_toolbox import sign, verify, SignatureError, SignatureExpired

SECRET = "server-side-secret"

def read_token(token):
    try:
        return verify(token, key=SECRET)
    except SignatureExpired:
        return "expired"  # signature valid, the token is too old
    except SignatureError:
        return "rejected"  # forged, altered, or signed with another key

read_token(sign("ok", key=SECRET))  # 'ok'
read_token(sign("ok", key="another-key"))  # 'rejected'
read_token("not-a-token")  # 'rejected'
```

A token whose payload was changed is rejected:

```python
import base64
from genro_toolbox import sign, verify, SignatureError

SECRET = "server-side-secret"

token = sign("user", key=SECRET)
_, expiry, signature = token.split(".")
forged_payload = base64.urlsafe_b64encode(b"admin").rstrip(b"=").decode()
forged = f"{forged_payload}.{expiry}.{signature}"

try:
    verify(forged, key=SECRET)
except SignatureError as e:
    message = str(e)

message  # 'Signature does not match: the token was not produced with this key.'
```

## Token Format

A token is three base64url fields joined by `.`:

```text
<payload>.<expiry>.<signature>
```

- **payload**: the payload, UTF-8 encoded, then base64url without padding.
- **expiry**: a Unix timestamp, base64url-encoded; empty when the token does not expire.
- **signature**: HMAC-SHA256 of `<payload>.<expiry>`, base64url without padding.

The base64url alphabet (`A-Za-z0-9-_`) has no `.`, so the payload can contain
any character and comes back unchanged. The token is safe in URLs and cookies.

```python
from genro_toolbox import sign, verify

payload = '{"exclude": "*.tmp;*.bak", "city": "Città"}'
verify(sign(payload, key="k"), key="k") == payload  # True
```

The signature is compared with `hmac.compare_digest`, in constant time.

## Invalid Arguments

An empty key, or an `expires_in` that is zero or negative, raises
`ValueError`:

```python
from genro_toolbox import sign

try:
    sign("data", key="")
except ValueError as e:
    message = str(e)

message  # 'A non-empty key is required to sign a payload.'

try:
    sign("data", key="k", expires_in=0)
except ValueError as e:
    message = str(e)

message  # 'expires_in must be a positive number of seconds, got 0.'
```

`verify` with an empty key raises `ValueError` too.

## API Reference

```python
def sign(payload: str, key: str, expires_in: int | None = None) -> str: ...

def verify(token: str, key: str) -> str: ...

class SignatureError(Exception): ...

class SignatureExpired(SignatureError): ...
```

## See Also

- [API Reference](../api/reference.md) - Complete API documentation
