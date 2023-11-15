import functools

import godot

from . import utils


def _continue_after_fail(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		with utils.print_exceptions_and_continue():
			return func(*args, **kwargs)
		return Exception
	return wrapper


@_continue_after_fail
def _init_settings():
	module_search_path_setting = 'python/config/module_search_path'

	if not godot.ProjectSettings.has_setting(module_search_path_setting):
		godot.ProjectSettings.set_setting(module_search_path_setting, ['res://'])

	godot.ProjectSettings.set_initial_value(module_search_path_setting, ['res://'])
	godot.ProjectSettings.add_property_info(dict(
		name = module_search_path_setting,
		type = godot.TYPE_ARRAY,
		hint = godot.PROPERTY_HINT_TYPE_STRING,
		hint_string = f'{int(godot.TYPE_STRING)}/{int(godot.PROPERTY_HINT_DIR)}:',
	))
	godot.ProjectSettings.set_restart_if_changed(module_search_path_setting, True)


@_continue_after_fail
def _install_icons():
	# XXX: probably not the best way to do things, but works for now

	import importlib.resources
	package = importlib.resources.files(__package__)

	svg = (package / 'icons' / 'python-script.svg').read_text()

	img = godot.Image()
	img.load_svg_from_string(svg, godot.EditorInterface.get_editor_scale())

	texture = godot.ImageTexture.create_from_image(img)

	godot.EditorInterface.get_editor_theme().set_icon('PythonScript', 'EditorIcons', texture)


@_continue_after_fail
def _register_export_plugin():
	from . import export_plugin


def _deferred_init_extension():
	_init_settings()
	_install_icons()

	_register_export_plugin()


def init_extension():
	godot.Callable(_deferred_init_extension).call_deferred() # XXX: singletons aren't ready immediately


