# Exposition

## Methods

````{function} method(func)
Expose a method to Godot. Use as a decorator.

Example:
```
class MethodExample(godot.RefCounted):
	@godot.method
	def callable_from_godot(self):
		print('you called?')
```
````

```{function} classmethod(func)
Expose a class method to Godot as a static method. Use as a decorator.
```

```{function} staticmethod(func)
Expose a static method to Godot. Use as a decorator.
```

```{function} expose_all_methods(cls)
Expose all methods of `cls` to Godot. Use as a class decorator.

Methods with dunder names (those beginning and ending with double underscore, i.e. `__init__`, `__add__`, etc.) are not exposed by this function. Methods beginning with a single underscore will be exposed.
```


## Properties

````{function} property(*args, default = unspecified, default_factory = unspecified, type: godot.Variant.Type = unspecified, name: str = unspecified, class_name: str = unspecified, hint: godot.PropertyHint = unspecified, hint_string: str = unspecified, usage: godot.PropertyUsageFlags = unspecified, **kwargs)

Expose a property to Godot. This function behaves much like the `builtins.property()` type with a few Godot specific additions.

The default value for the property can be specified with:

- `default`: The default value for the property.
- `default_factory`: A factory function that will be called to create the default value for each instance. Use this instead of `default` for types like `list` or `Vector2` which otherwise would have a single reference to the same shared object for each instance.

The following six parameters are passed to Godot as a `PropertyInfo` dictionary:

`type`, `name`, `class_name`, `hint`, `hint_string`, `usage`

See Godot's documentation for their meanings[^godot-properties]. If left unspecified they will be derived from the property's type annotation.

`args` and `kwargs` are forwarded to Python's `builtins.property()`. Valid arguments include `fget`, `fset`, `fdel` and `doc`, all of which are optional. See Python's documentation for full details.

If `args` is a single `builtins.property()` instance a copy of that property descriptor will be made and updated with all other arguments.

Examples:

1.	As a descriptor with type annotation
	```
	speed: float = godot.property(default = 250.0, doc = "The character's speed")
	```

2.	As a decorator for getters and setters
	```
	@godot.property
	def speed(self) -> float:
		'''The character's speed'''
		return self._speed

	@speed.setter
	def speed(self, value: float):
		self._speed = value
	```

3.	Specifying a range using Godot's property hints
	```
	count: int = godot.property(hint = godot.PropertyHint.PROPERTY_HINT_RANGE,
		hint_string = '0,10,1,or_greater')
	```

4.	Passing hints to the decorator of a getter
	```
	@godot.property(hint = godot.PropertyHint.PROPERTY_HINT_RANGE,
		hint_string = '0.0,500.0,0.1,or_greater')
	def speed(self) -> float:
		'''The character's speed'''
		return self._speed
````

````{function} property_group(name: str = unspecified, *, prefix: str = unspecified)
Begin a property group. Properties that follow will be placed under this group until the next group is defined.

If `name` is unspecified the group's name will be taken from the name the group is assigned to within the class.

If `prefix` is specified properties starting with that prefix will be grouped and displayed in the inspector showing only the part of their name that follows the prefix.

See Godot`s [EditorInspector](https://docs.godotengine.org/en/stable/classes/class_editorinspector.html) documentation for details on property groups.

```{note}
Each group must be assigned with a unique identifier, otherwise a previously defined group of the same name will be overridden.
```

Example:
```
class ClassWithProperties(godot.RefCounted):
	group_name = godot.property_group()
	prop_in_group: int: godot.property()

	group_with_prefix = godot.property_group(prefix='group_with_prefix_')
	group_with_prefix_prop: int: godot.property()
```
````

```{function} property_subgroup(name: str = unspecified, *, prefix: str = unspecified)
Begin a property subgroup. See {func}`property_group`.
```


## Signals

````{function} signal()
Define a signal for the class.

```{note}
`godot.signal()` and `godot.Signal` differ. Lowercase `signal()` described here defines a signal on a class, while uppercase `Signal` is the variant type used for instances.
```

Example:
```
class SignalExample(godot.RefCounted):
	example_signal = godot.signal()

	def _ready(self):
		self.example_signal.emit()
```
````


## Constants

````{function} constant(value: int)
Define an integer constant for the class.

Example:
```
class ConstantExample(godot.RefCounted):
	CONSTANT = godot.constant(42)

	def _ready(self):
		print(f'the answer to everything is {self.CONSTANT}')
```
````


## Enums

````{function} expose(enum)
Expose an enumeration to Godot. See Python's `enum` documentation for how to define enumerations.

Example:
```
import enum

class EnumExample(godot.RefCounted):
	@godot.expose
	class Constants(enum.IntEnum):
		FIRST = 0
		ANSWER_TO_EVERYTHING = 42

	@godot.expose
	class Flags(enum.IntFlag):
		FLAG_A = 1
		FLAG_B = 2
		FLAG_C = 4
```
````


## Class registration

````{function} expose_script_class(cls: type | None = None, name: str | None = None, as_global: bool = False, icon: str | None = None, tool: bool = False)
Expose a script class to Godot.

Only one class per module can be exposed.

```{note}
Passing `expose_all_methods = True` to the class definition will cause {func}`expose_all_methods` to be called on the class. This detail may change in a later version, feedback on this is welcome.
```

Example:
```
@godot.expose_script_class
class PythonSprite(godot.Sprite2D, expose_all_methods=True):
	def _ready(self):
		print('hello! 🐍')

@godot.expose_script_class(as_global=True)
class GlobalPythonSprite(godot.Sprite2D, expose_all_methods=True):
	def _ready(self):
		print('hello world! 🐍')
```
````


[^godot-properties]: Godot's property hints are documented [here](https://docs.godotengine.org/en/stable/classes/class_@globalscope.html#enum-globalscope-propertyhint)


