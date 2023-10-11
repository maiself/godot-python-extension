import godot

from godot.variant_types import *

from .sprite import TestSprite


@godot.expose_script_class(as_global=True)
class TestSpawner(godot.Node, expose_all_methods=True):
	'''Node that spawns a number of sprites.'''

	## The number of objects to spawn
	spawn_count: int = godot.property(default = 10)

	_spawn_color = godot.property_group(prefix='spawn_color_')

	## The color of the spawned objects
	spawn_color: Color = godot.property(default = godot.Color.WHITE)

	## The amount of randomness in hue of the spawned objects
	spawn_color_hue_randomness: float = godot.property(default = 0.0)

	def _ready(self):
		for i in range(self.spawn_count):
			node = TestSprite()

			node.texture = godot.load('res://icon.png')

			node.modulate = self.spawn_color
			node.modulate.h += godot.randf_range(-0.5, 0.5) * self.spawn_color_hue_randomness

			node.global_position = Vector2(godot.randf_range(0.0, 1.0), godot.randf_range(0.0, 1.0)) \
				* Vector2(self.get_tree().root.size)

			node.speed = godot.randf_range(50.0, 150.0)
			node._input_rotation = godot.randf_range(0.0, 360.0)

			self.add_child(node)

