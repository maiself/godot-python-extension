import sys
import importlib
import functools

import godot

from .. import utils


if not godot.Engine.is_editor_hint():
	raise ImportError(
		f'cannot import module {__name__!r} when not running from editor')


def _continue_after_fail(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		with utils.print_exceptions_and_continue():
			return func(*args, **kwargs)
		return Exception
	return wrapper


_commands = []

def _command(func):
	key = f'python_extension/{func.__name__.removeprefix("_")}'
	label = func.__doc__.splitlines()[0].strip()
	_commands.append((key, label, func))
	return func


@_continue_after_fail
def _install_commands():
	command_palette = godot.EditorInterface.get_command_palette()

	for key, label, func in _commands:
		command_palette.add_command(label, key, func)


@_continue_after_fail
def _uninstall_commands():
	command_palette = godot.EditorInterface.get_command_palette()

	for key, label, func in _commands:
		command_palette.remove_command(key)


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


@_command
def _reload_python_extension_modules():
	'''Reload Python Extension Modules'''

	# TODO: test and enable reload for more modules
	reloadable_modules = [
		'godot._python_extension.python_language',
		#'godot._python_extension.python_script',
		'godot._python_extension.editor',
	]

	print('\n\033[91;1m', 'reloading python extension modules...', '\033[0m', sep='')

	for module_name in reloadable_modules:
		if module := sys.modules.get(module_name):
			print('\033[91;3m', f'  {module_name}', '\033[0m', sep='')
			importlib.reload(module)

	print('\033[91;1m', f'finished reloading', '\033[0m\n', sep='')


def _init():
	_init_settings()
	_install_icons()
	_install_commands()

	_register_export_plugin()


def _reload():
	_uninstall_commands()
	_install_commands()


try:
	if not _is_first_module_init:
		_reload()

except NameError:
	_is_first_module_init = False

	godot.Callable(_init).call_deferred() # XXX: singletons aren't ready immediately


