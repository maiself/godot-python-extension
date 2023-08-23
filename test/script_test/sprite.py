import godot

from godot.variant_types import *
from godot.global_enums import *

from godot import Input, InputEventKey


@godot.expose_script_class(as_global=True)
class TestSprite(godot.Node2D, expose_all_methods=True):
	'''Simple class to test Python script support.

	Implements a simple movable sprite.'''

	## The speed of the sprite when moving
	speed: float = godot.property(default = 250.0)

	def _process(self, delta: float):
		'''Move sprite based of speed and arrow key input.'''

		speed_modifier = (2.0 if Input.is_key_pressed(KEY_SHIFT) else 1.0)

		self.global_position += Vector2(
				Input.get_axis('ui_left', 'ui_right'),
				Input.get_axis('ui_up', 'ui_down')
			) * self.speed * speed_modifier * delta

	def _input(self, event):
		self.check_input(event)

	@godot.method
	def check_input(self, event: godot.InputEvent):
		'''Check input event for escape key and quit after a half second when pressed.'''

		match event:
			case InputEventKey(pressed = True, keycode = godot.KEY_ESCAPE):
				self.get_tree().create_timer(0.5).timeout.connect(lambda: self.get_tree().quit())

			# XXX
			case InputEventKey(pressed = True, keycode = godot.KEY_F5):
				print('reloading')
				import sys
				import importlib
				importlib.reload(sys.modules[__name__])
				importlib.reload(sys.modules['godot._python_extension.python_script'])

	def test_array(self, array: Array[TestSprite]):
		'''Test array argument.'''
		pass

