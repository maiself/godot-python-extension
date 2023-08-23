import enum

import godot


@godot.register_extension_class
class Example(godot.Node, expose_all_methods = True):
	test_properties = godot.property_group()

	property_from_list: godot.Vector3 = godot.property(default = godot.Vector3(1, 2, 3))

	custom_signal = godot.signal()


	test_group = godot.property_group(prefix='group_')
	test_subgroup = godot.property_subgroup(prefix='group_subgroup_')


	@godot.property(usage = godot.PROPERTY_USAGE_DEFAULT | godot.PROPERTY_USAGE_READ_ONLY)
	def group_subgroup_custom_position(self) -> godot.Vector2:
		return self._pos

	@group_subgroup_custom_position.setter
	def group_subgroup_custom_position(self, pos: godot.Vector2):
		self._pos = pos


	@godot.expose
	class Constants(enum.IntEnum):
		FIRST = 0
		ANSWER_TO_EVERYTHING = 42

	CONSTANT_WITHOUT_ENUM = godot.constant(314)

	@godot.expose
	class Flags(enum.IntFlag):
		FLAG_ONE = 1
		FLAG_TWO = 2


	def __init__(self):
		self._pos = godot.Vector2(0, 0)


	def emit_custom_signal(self, name: str, value: int):
		self.custom_signal.emit(name, value)

	@classmethod
	def test_static(cls, a: int, b: int) -> int:
		return a + b

	@staticmethod
	def test_static2():
		pass


	def simple_func(self):
		self.custom_signal.emit('simple_func', 3)

	def simple_const_func(self):
		self.custom_signal.emit('simple_const_func', 4)

	def test_string_ops(self) -> str:
		s = godot.String('A')
		s += 'B'
		s += 'C'
		s += chr(0x010E)
		s = s + 'E'
		return s

	def test_str_utility(self) -> str:
		return godot.str('Hello, ', 'World', '! The answer is ', 42)

	def test_bitfield(self, flag: Example.Flags) -> Example.Flags:
		return flag


	def return_something(self, base: str) -> str:
		return base + '42'

	def return_something_const(self) -> godot.Viewport:
		return self.get_viewport() if self.is_inside_tree() else None


	def get_v4(self) -> godot.Vector4:
		return godot.Vector4(1.2, 3.4, 5.6, 7.8)

	def test_node_argument(self, node: Example) -> Example:
		return node


	def varargs_func(self, *args):
		return len(args)

	def varargs_func_v2(self, *args) -> godot.Variant:
		return len(args)

	def varargs_func_nv(self, *args) -> int:
		return len(args) + 42

	def varargs_func_void(self, *args) -> None:
		self.custom_signal.emit('varargs_func_void', len(args) + 1)


	def def_args(self, a: int = 100, b: int = 200) -> int:
		return a + b


	def _input(self, event: godot.InputEvent):
		if isinstance(event, godot.InputEventKey):
			self.custom_signal.emit('_input: ' + event.as_text_key_label(), event.unicode) # XXX: key_label???


