import godot


def _install_icons():
	# XXX: probably not the best way to do things, but works for now

	import importlib.resources
	package = importlib.resources.files(__package__)

	svg = (package / 'icons' / 'python-script.svg').read_text()

	img = godot.Image()
	img.load_svg_from_string(svg, godot.EditorInterface.get_editor_scale())

	texture = godot.ImageTexture.create_from_image(img)

	godot.EditorInterface.get_editor_theme().set_icon('PythonScript', 'EditorIcons', texture)


def _register_export_plugin():
	from . import export_plugin


def init_extension():
	godot.Callable(_install_icons).call_deferred()
	godot.Callable(_register_export_plugin).call_deferred()



