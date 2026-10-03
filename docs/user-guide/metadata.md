# metadata — stamp attributes on functions and classes

Decorator that stamps keyword arguments as attributes on a function or a class.

## Overview

`metadata(**attributes)` writes each keyword argument onto the decorated
object with `setattr`. With `prefix`, the attribute name becomes
`<prefix>_<key>`.

**Key Features**:

- Works on functions, methods and classes
- Returns the target itself: no wrapper, the function or class is unchanged
- Optional `prefix` to group related attributes under one namespace
- Attributes set on a class are visible on its instances and subclasses

## Basic Usage

```python
from genro_toolbox import metadata

@metadata(mixin_order=10)
class Core:
    pass

Core.mixin_order  # 10

@metadata(timeout=30, retries=2)
def handler():
    return "done"

handler.timeout  # 30
handler.retries  # 2
handler()  # 'done'
```

## Prefix

`prefix` is keyword-only. Each attribute name becomes `<prefix>_<key>`:

```python
from genro_toolbox import metadata

@metadata(prefix="rpc", public=True, tags="admin")
def handler():
    pass

handler.rpc_public  # True
handler.rpc_tags  # 'admin'
hasattr(handler, "public")  # False
```

## Identity

The decorator returns the same object it receives. A decorated class stays
instantiable, and the attributes are visible on its instances and subclasses
because they are class attributes.

```python
from genro_toolbox import metadata

def original():
    pass

metadata(owner="core")(original) is original  # True

@metadata(prefix="plugin", name="audit")
class AuditPlugin:
    pass

class StrictAuditPlugin(AuditPlugin):
    pass

AuditPlugin().plugin_name  # 'audit'
StrictAuditPlugin.plugin_name  # 'audit'
```

## Stacking

Several `metadata` decorators can be stacked. The decorator closest to the
target runs first, so on the same name the outer one wins.

```python
from genro_toolbox import metadata

@metadata(prefix="rpc", public=True)
@metadata(prefix="rpc", public=False, tags="user")
def handler():
    pass

handler.rpc_public  # True
handler.rpc_tags  # 'user'
```

## Real-World Example

### Collecting Marked Methods

Mark methods with an attribute, then find them by inspecting the class:

```python
from genro_toolbox import metadata

class Service:
    @metadata(prefix="rpc", public=True)
    def status(self):
        return "up"

    @metadata(prefix="rpc", public=False)
    def reset(self):
        return "reset"

    def helper(self):
        return "internal"

public_methods = sorted(
    name
    for name, member in vars(Service).items()
    if getattr(member, "rpc_public", False)
)

public_methods  # ['status']
```

## API Reference

```python
def metadata(*, prefix: str | None = None, **attributes: Any) -> Callable[[T], T]:
    """A decorator that stamps keyword arguments as attributes on the target.

    Args:
        prefix: Optional prefix prepended to each attribute name as ``<prefix>_<key>``.
        **attributes: Keyword arguments to stamp as attributes on the target.

    Returns:
        The decorated object itself, with the attributes set.
    """
```

## See Also

- [extract_kwargs Guide](extract-kwargs.md) - The other decorator in `genro_toolbox.decorators`
- [API Reference](../api/reference.md) - Complete API documentation
