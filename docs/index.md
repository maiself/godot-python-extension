# godot-python-extension

This project provides [**Python**](https://www.python.org/) language bindings for the [**Godot**](https://godotengine.org/) game engine.

The bindings are implemented as a [GDExtension](https://godotengine.org/article/introducing-gd-extensions) that exposes Godot's APIs and enables extension classes and scripts to be written in Python.

Source code can be found [here](https://github.com/maiself/godot-python-extension).

Full documentation is currently in the process of being written.


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

To be added.

```{toctree}
```

