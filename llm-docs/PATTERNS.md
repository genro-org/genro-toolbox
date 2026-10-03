# genro-toolbox Usage Patterns

## extract_kwargs Patterns

### Basic prefix extraction

```python
# From test: test_decorators.py::TestExtractKwargsBasic::test_extract_with_prefix
@extract_kwargs(logging=True)
def func(self, name, logging_kwargs=None, **kwargs):
    return logging_kwargs

func(obj, "test", logging_level="INFO", logging_format="json", timeout=30)
# logging_kwargs = {"level": "INFO", "format": "json"}
# kwargs = {"timeout": 30}
```

### Multiple prefix groups

```python
# From test: test_decorators.py::TestExtractKwargsBasic::test_extract_multiple_prefixes
@extract_kwargs(logging=True, cache=True)
def func(self, logging_kwargs=None, cache_kwargs=None, **kwargs):
    pass

func(obj, logging_level="INFO", cache_ttl=300, cache_backend="redis")
# logging_kwargs = {"level": "INFO"}
# cache_kwargs = {"ttl": 300, "backend": "redis"}
```

### Keep extracted in kwargs (pop=False)

```python
# From test: test_decorators.py::TestExtractKwargsBasic::test_extract_with_pop_false
@extract_kwargs(logging={'pop': False})
def func(self, logging_kwargs=None, **kwargs):
    return logging_kwargs, kwargs

# logging_kwargs = {"level": "INFO"}
# kwargs = {"logging_level": "INFO", "timeout": 30}  # still contains prefixed
```

### Merge with explicit kwargs

```python
# From test: test_decorators.py::TestExtractKwargsBasic::test_merge_with_existing_kwargs
@extract_kwargs(logging=True)
def func(self, logging_kwargs=None, **kwargs):
    return logging_kwargs

func(obj, logging_kwargs={"existing": "value"}, logging_level="INFO")
# logging_kwargs = {"existing": "value", "level": "INFO"}
```

### Adapter preprocessing

```python
# From test: test_decorators.py::TestExtractKwargsAdapter::test_adapter_called
class MyClass:
    def preprocess(self, kwargs):
        kwargs['injected'] = True

    @extract_kwargs(_adapter='preprocess', logging=True)
    def method(self, logging_kwargs=None, **kwargs):
        return kwargs

obj.method(logging_level="INFO")
# kwargs contains {'injected': True}
```

---

## safe_is_instance Patterns

### Check built-in types

```python
# From test: test_typeutils.py::TestSafeIsInstance::test_builtin_types
safe_is_instance(42, "builtins.int")      # True
safe_is_instance("hello", "builtins.str") # True
safe_is_instance([1, 2], "builtins.list") # True
safe_is_instance({"a": 1}, "builtins.dict") # True
```

### Check with inheritance

```python
# From test: test_typeutils.py::TestSafeIsInstance::test_subclass_recognition
class Base: pass
class Derived(Base): pass

obj = Derived()
safe_is_instance(obj, "module.Derived")  # True
safe_is_instance(obj, "module.Base")     # True (subclass)
safe_is_instance(obj, "builtins.object") # True (all objects)
```

### Check custom class without importing

```python
# From test: test_typeutils.py::TestSafeIsInstance::test_basic_instance_check
safe_is_instance(obj, "mypackage.models.BaseNode")
# No import of mypackage required
# Checks full MRO
```

---
