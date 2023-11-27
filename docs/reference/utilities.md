# Utilities

Extra utility functions added to the `godot` module for use from Python. These utilities may or may not be the same as those available in GDScript.

```{function} load(res_path) -> godot.Resource
Load a resource.
```


````{function} preload(res_path) -> godot.Resource
Get a preloaded a resource.
```{caution}
Preloading from a Python script isn't actually implemented yet.
```
````


````{function} call_deferred(func, *args, **kwargs)
Make a deferred call to `func(*args, **kwargs)`.

Equivalent to `godot.Callable(functools.partial(func, *args, **kwargs)).call_deferred()`
````

