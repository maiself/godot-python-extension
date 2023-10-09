import atexit

import godot

from . import python_interpreter

from . import python_language
from . import python_script
from . import script_resource_format

from . import godot_fs_importer

from . import cli


# create instances

script_language = python_language.PythonLanguage()
script_loader = script_resource_format.PythonScriptLoader()
script_saver = script_resource_format.PythonScriptSaver()

godot.Engine.register_script_language(script_language)
godot.ResourceLoader.add_resource_format_loader(script_loader)
godot.ResourceSaver.add_resource_format_saver(script_saver)


godot_fs_importer.install()


cli.main()


def _install_icons():
	# XXX: probably not the best way to do things, but works for now

	if not godot.Engine.is_editor_hint():
		return

	import importlib.resources
	package = importlib.resources.files(__package__)

	svg = (package / 'icons' / 'python-script.svg').read_text()

	img = godot.Image()
	img.load_svg_from_string(svg, godot.EditorInterface.get_editor_scale())

	texture = godot.ImageTexture.create_from_image(img)

	godot.EditorInterface.get_editor_theme().set_icon('PythonScript', 'EditorIcons', texture)


godot.Callable(_install_icons).call_deferred()


@atexit.register
def _cleanup():
	global script_language
	global script_loader
	global script_saver

	godot.ResourceSaver.remove_resource_format_saver(script_saver)
	godot.ResourceLoader.remove_resource_format_loader(script_loader)
	godot.Engine.unregister_script_language(script_language)

	python_language.PythonLanguage.get().free()

	del script_language
	del script_loader
	del script_saver


