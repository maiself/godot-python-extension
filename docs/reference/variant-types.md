# Variant types

All variant types have an overloaded `__init__` method, see Godot's variant type documentation for details on variant constructors. Differences are noted here. All types are also given `__str__`, `__repr__`, `__copy__`, `__deepcopy__`, and `copy` methods.


````{class} Array[T]
Typed `Array` with element type `T`. If no type is given the `Array` is untyped.

```{note}
Python doesn't enforce types, but Godot does.
```
````


````{class} Dictionary
```{method} __init__(**kwargs)
Create a `Dictionary` from keys and values from `kwargs`.
```

```{method} __init__(mapping)
:no-index:
Create a `Dictionary` as a copy of a `mapping` object.

```

```{method} items()
Return a sequence of `(key, value)` pairs.
```
````



````{class} Callable
```{method} __call__(*args)
Alias for `godot.Callable.call()`
```

```{method} get_custom()
Return the original Python callable if available.
```
````
