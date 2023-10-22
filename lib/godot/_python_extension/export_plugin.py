import godot

from godot._internal.extension_classes import *

from . import utils


@register_extension_class
@utils.log_method_calls
class PythonExportPlugin(godot.EditorExportPlugin):
	def _get_name(self) -> str:
		return type(self).__name__

	def _export_begin(self, features: list[str], is_debug: bool, path: str, flags: int):
		if 'linux' in features:
			self.add_shared_object('bin/libpython3.12.so.1.0', [], '') # TODO: use correct library path

		#self.add_file(path, godot.FileAccess.get_file_as_bytes(path), False)

	def _export_file(self, path: str, type_: str, features: list[str]):
		pass



export_plugin = PythonExportPlugin()

plugin = godot.EditorPlugin()
plugin.add_export_plugin(export_plugin)

