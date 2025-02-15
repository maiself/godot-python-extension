# godot-python-extension

This project provides [**Python**](https://www.python.org/) language bindings for the [**Godot**](https://godotengine.org/) game engine.

The bindings are implemented as a [GDExtension](https://godotengine.org/article/introducing-gd-extensions) that exposes Godot's APIs and enables extension classes and scripts to be written in Python.

Source code for the project can be found [here](https://github.com/maiself/godot-python-extension).

```{admonition} Documentation status

Full documentation is still in the process of being written. Please check back if anything is missing. You can also summit an [issue](https://github.com/maiself/godot-python-extension/issues) or [pull request](https://github.com/maiself/godot-python-extension/pulls) to help out in completing the documentation.
```

```{admonition} Project status
:class: warning

This repository is a work in progress and should be considered experimental. It's not yet production ready.

＊ *Please use version control with any project.*

Issues can be reported [here](https://github.com/maiself/godot-python-extension/issues). Suggestions on improvement are also welcomed.
```

## Example

```python
import godot
from godot import Vector2, Input

@godot.expose_script_class
class PythonSprite(godot.Sprite2D, expose_all_methods=True):
	'''A simple script to demonstrate Python support.'''

	message: str = godot.property(default = 'hello world! 🐍')
	speed: float = godot.property(default = 250.0)

	def _ready(self):
		print(self.message)

		self.texture = godot.load('res://icon.png')

	def _process(self, delta: float):
		self.global_position += Vector2(
				Input.get_axis('ui_left', 'ui_right'),
				Input.get_axis('ui_up', 'ui_down')
			) * self.speed * delta
```

## License

This project released under the MIT license, see the [license.md](https://github.com/maiself/godot-python-extension/blob/master/license.md) file.


## Contents

```{toctree}
:caption: Using the extension
:maxdepth: 3

usage/installation
usage/platforms
usage/type-conversions
reference/index
```

```{toctree}
:caption: Development

development/building
development/without-building
development/architecture
```

