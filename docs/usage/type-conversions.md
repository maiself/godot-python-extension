# Type conversions

% <!-- → ← ↔ ⇄ -->

Some variant types are automatically converted for ease of use.


## `String` and `StringName` ↔ `str`

- `godot.String` ↔ `str`
- `godot.StringName` ↔ `str`

`String` and `StringName` are automatically converted to and from `str` for return values and call augments. This means any Godot API documented as returning `String` will actually return a `str` to Python. If you need to work on a `String` specifically you will need to convert back.

```{important}
The exception to this implicit conversion are the methods of `String` and `StringName` themselves, which will return their own types without conversion.
```

Examples:

`godot.Node.get_name()` returns `StringName` in Godot, but is implicitly converted to `str` in Python.

```python
# `name` is a `str`
name = node.get_name()
```

Properties are implicitly converted to `str` as well.

```python
# `name` is a `str`
name = node.name
```

Attempting to call `godot.StringName`'s `to_snake_case()` will raise `AttributeError` as the return type of `get_name()` in the bindings is actually `str`.

```python
# AttributeError
#snake_case_name = node.get_name().to_snake_case()
```

Converting to `String` first will succeed. Note that `to_snake_case()` is a `String`/`StringName` method and so the return type is `String`, as implicit conversion is not applied to the methods of those types.

```python
# `snake_case_name` is a `String`
snake_case_name = godot.String(node.get_name()).to_snake_case()

# `snake_case_name` is a `str`
snake_case_name = str(godot.String(node.get_name()).to_snake_case())
```


## `list` and sequences → arrays

- `list` → `godot.Array`
- `list` → `godot.Array[…]`
- `list` → `godot.Packed…Array`

Lists and any sequence are implicitly converted from Python to Godot's array types where an API expects an array type.

This works for any of Godot's array types, including typed arrays and packed arrays, however if any element in the Python sequence cannot be converted to the element type of Godot array the result will be an error.

Godot's array types are never converted to `list` implicitly.


## `dict` and mappings → `Dictionary`

- `dict` → `godot.Dictionary`

Python's `dict` and mapping types will implicitly convert to `godot.Dictionary` when needed by the API.

If any key, value, or nested value cannot be converted the result will be an error.

`godot.Dictionary` is never converted to `dict` implicitly.



## Callables and methods ↔ `Callable`

- `callable` → `godot.Callable`

_To be written..._

```{caution}
Bound methods are currently referenced strongly, which can cause issues with objects not being collected properly. This behavior is likely to be changed soon.
```

