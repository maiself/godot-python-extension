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

		self._add_api_json()

	def _add_api_json(self):
		import sys
		import pathlib
		import tempfile
		import subprocess
		import gzip

		with tempfile.TemporaryDirectory() as temp_dir:
			subprocess.run([sys.executable, '--quiet', '--headless', '--dump-extension-api'],
				cwd = temp_dir,
				check = True,
			)

			data = (pathlib.Path(temp_dir) / 'extension_api.json').read_bytes()

		data = gzip.compress(data, mtime=0)

		self.add_file('res://.python/extension_api.json.gz', data, False)

	def _export_file(self, path: str, type_: str, features: list[str]):
		pass



export_plugin = PythonExportPlugin()

plugin = godot.EditorPlugin()
plugin.add_export_plugin(export_plugin)

