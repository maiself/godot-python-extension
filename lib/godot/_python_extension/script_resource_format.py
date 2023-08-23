import pathlib

import godot

from godot._internal.extension_classes import *

from . import utils

from .python_script import PythonScript
from .python_language import PythonLanguage


@register_extension_class
@bind_all_methods
#@utils.log_method_calls
class PythonScriptLoader(godot.ResourceFormatLoader):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def _get_recognized_extensions(self) -> list[str]:
		return ['py']

	def _recognize_path(self, path: str, type_: str) -> bool:
		return path.endswith('.py')

	def _handles_type(self, type_: str) -> bool:
		return type_ in ('PythonScript')

	def _get_resource_type(self, path: str) -> str:
		if path.endswith('.py'):
			return 'PythonScript'
		return ''

	#def _get_resource_script_class(self, path: str) -> str:
	#	return ''

	#def _get_resource_uid(self, path: str) -> int:
	#	return -1

	def _get_dependencies(self, path: str, add_types: bool) -> list[str]:
		return []

	def _rename_dependencies(self, path: str, renames: dict) -> godot.Error:
		raise NotImplementedError

	def _exists(self, path: str) -> bool:
		return godot.FileAccess.file_exists(path) # XXX
		#return pathlib.Path(path.removeprefix('res://')).exists()

	def _get_classes_used(self, path: str) -> list[str]:
		raise NotImplementedError

	def _load(self, path: str, original_path: str, use_sub_threads: bool, cache_mode: int) -> godot.Variant:
		script_resource = PythonScript(path=original_path) # XXX
		script_resource._set_source_code(godot.FileAccess.get_file_as_string(path))
		return script_resource


@register_extension_class
@bind_all_methods
#@utils.log_method_calls
class PythonScriptSaver(godot.ResourceFormatSaver):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def _save(self, resource: godot.Resource, path: str, flags: int) -> godot.Error:
		if not isinstance(resource, PythonScript):
			raise ValueError(f'cannot save resource {resource!r} as {PythonScript.__name__!r}')

		source = resource._source#_code # XXX

		#pathlib.Path(path.removeprefix('res://')).write_text(source)
		godot.FileAccess.open(path, godot.FileAccess.ModeFlags.WRITE).store_string(source)

		#if godot.ScriptServer.is_reload_scripts_on_save_enabled(): # XXX: not exposed
		PythonLanguage.get()._reload_tool_script(resource, True)

		return godot.Error.OK

	def _set_uid(self, path: str, uid: int) -> godot.Error:
		return godot.Error.OK#raise NotImplementedError

	def _recognize(self, resource: godot.Resource) -> bool:
		return isinstance(resource, PythonScript)

	def _get_recognized_extensions(self, resource: godot.Resource) -> list[str]:
		if isinstance(resource, PythonScript):
			return ['py']
		return []

	def _recognize_path(self, resource: godot.Resource, path: str) -> bool:
		return isinstance(resource, PythonScript) and path.endswith('.py')



