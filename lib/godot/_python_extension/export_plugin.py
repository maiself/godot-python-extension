import pathlib
import re
import shutil

import godot

from godot._internal.extension_classes import *

from . import utils


_platforms = (
	'linux',
	'macos',
	'windows',
	'android',
	'ios',
	'web'
)

_architectures = [
	'universal',
	'x86_32',
	'x86_64',
	'arm32',
	'arm64',
	'rv64',
	'ppc32',
	'ppc64',
	'wasm32'
]


def _get_platform_from_features(features: list[str]) -> str:
	platforms = [feature for feature in features if feature in _platforms]
	if len(platforms) != 1:
		raise RuntimeError(f'unable to determine platform from features')
	return platforms[0]


def _get_arch_from_features(features: list[str]) -> str:
	archs = [feature for feature in features if feature in _architectures]
	if len(archs) != 1:
		raise RuntimeError(f'unable to determine architecture from features')
	return archs[0]


def _get_current_gdextension_path() -> pathlib.Path:
	for ext_path in godot.GDExtensionManager.get_loaded_extensions():
		if pathlib.Path(ext_path).name == 'python.gdextension':
			path = pathlib.Path(ext_path.removeprefix('res://'))
			if path.exists():
				return path

	raise RuntimeError('unable to locate python gdextension path')


def _get_target_platform_lib(platform, arch) -> pathlib.Path:
	gdextension_path = _get_current_gdextension_path()

	for line in gdextension_path.read_text().splitlines():
		if match_ := re.fullmatch(rf'{platform}\.{arch}\s*=\s*"(?P<path>.+)"', line):
			path = match_.group('path')

			if path.startswith('res://'):
				path = path.removeprefix('res://')
			else:
				path = gdextension_path.parent / path

			if path.exists():
				return path

	raise RuntimeError('unable to target platform lib path')


@register_extension_class
@utils.log_method_calls
class PythonExportPlugin(godot.EditorExportPlugin):
	def _get_name(self) -> str:
		return type(self).__name__

	def _export_begin(self, features: list[str], is_debug: bool, export_path: str, flags: int):
		platform = _get_platform_from_features(features)
		arch = _get_arch_from_features(features)

		platform_lib = _get_target_platform_lib(platform, arch)
		platform_dir = platform_lib.parent
		platform_so_suffix = '.so' if platform != 'windows' else '.dll'

		shared_objects = set()
		files = set()

		for path in platform_dir.glob('**/*'):
			if not path.is_file():
				continue
			if platform_so_suffix in path.suffixes and 'lib-dynload' not in path.parts:
				shared_objects.add(path)
			else:
				files.add(path)

		for shared_object in shared_objects:
			if shared_object == platform_lib:
				continue
			self.add_shared_object(str(shared_object), [], '')

		target_dir = pathlib.Path(export_path).parent / 'lib' / f'{platform}-{arch}'

		for file in files:
			dir_ = target_dir / file.parent.relative_to(platform_dir)
			dir_.mkdir(parents=True, exist_ok=True)
			shutil.copy2(file, dir_)

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

