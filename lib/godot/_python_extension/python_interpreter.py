from godot._internal.extension_classes import *

import godot


@bind_all_methods
@register_extension_class
class Python(godot.RefCounted):
	@classmethod
	def exec(cls, *args, **kwargs):
		print('\033[91;1mYAY!\033[0m', args, kwargs)
		exec(str(args[0]), {})

