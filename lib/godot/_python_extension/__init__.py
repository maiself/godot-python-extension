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


