import sys
import os
import importlib.abc
import importlib.util
import re
import pathlib

import __future__

import godot

from . import utils
from . import python_script


module_search_path_setting = 'python/config/module_search_path'

if godot.ProjectSettings.has_setting(module_search_path_setting):
	sys.path.remove('res://')

	sys.path[:0] = list(
		str(x) for x in godot.ProjectSettings.get_setting(module_search_path_setting, ['res://']))


class _Cache:
	def __init__(self):
		self.clear()

	def clear(self):
		self._module_name_to_paths: dict[str, list[str]] = {}
		self._module_path_to_names: dict[str, list[str]] = {}

	@property
	def search_path(self):
		return [path for path in sys.path if path.startswith('res://')]

	@classmethod
	def _get_modules_under_path(cls, path: str):
		if path != 'res://':
			path = path.removesuffix('/')

		dirs = godot.DirAccess.get_directories_at(path)
		files = godot.DirAccess.get_files_at(path)

		if path.endswith('//'):
			path = path.removesuffix('/')

		for file in files:
			if file.endswith('.py'):
				yield '/'.join((path, file))

		for dir_ in dirs:
			yield from cls._get_modules_under_path('/'.join((path, dir_)))

	def _get_modules(self):
		for path in self.search_path:
			if not path.endswith('/'):
				path += '/'

			for file in self._get_modules_under_path(path):
				name = file.removeprefix(path).removesuffix('.py').replace('/', '.').removesuffix('.__init__')

				yield (file, name)

	def _get_modules_and_packages(self):
		modules = list(self._get_modules())

		names = set(name for path, name in modules)

		for module in modules:
			path, name = module

			path_parts = path.split('/')[:-1]
			name_parts = name.split('.')[:-1]

			while name_parts:
				pkg = '.'.join(name_parts)

				if pkg in names:
					break

				yield ('/'.join(path_parts) + '/', pkg)

				path_parts.pop()
				name_parts.pop()

			yield module

	def _update(self):
		if self._module_path_to_names:
			return

		for path, name in self._get_modules_and_packages():
			names = self._module_path_to_names.setdefault(path, [])

			if name not in names:
				names.append(name)

			names[:] = sorted(names, key = lambda name: (name.count('.'), names.index(name)))

			self._module_name_to_paths.setdefault(name, []).append(path)

	def get_module_path_from_name(self, name: str) -> str | None:
		self._update()

		paths = self._module_name_to_paths.get(name)

		if not paths:
			return None

		return paths[0]

	def get_module_name_from_path(self, path: str) -> str | None:
		self._update()

		names = self._module_path_to_names.get(path)

		if not names:
			return None

		return names[0]


_cache = _Cache()


#@utils.log_method_calls
class GodotFileSystemModuleImporter(importlib.abc.MetaPathFinder, importlib.abc.ExecutionLoader):
	compile_flags = __future__.annotations.compiler_flag

	@classmethod
	def _get_filename(cls, fullname: str) -> str | None:
		if fullname.startswith('godot.'):
			return None

		return _cache.get_module_path_from_name(fullname)

	@classmethod
	def get_filename(cls, fullname: str) -> str:
		if filename := cls._get_filename(fullname):
			return filename

		raise ImportError

	@utils.with_context
	def get_source(self, fullname):
		if (filename := self._get_filename(fullname)) is None:
			raise ImportError

		with utils.print_exceptions_and_continue():
		#try:
			with utils.exception_note(lambda: f'While getting source for: {fullname!r}'):
				if godot.ResourceLoader.exists(filename, python_script.PythonScript.__name__):
					script_resource = godot.ResourceLoader.load(filename,
						python_script.PythonScript.__name__,
						godot.ResourceLoader.CacheMode.CACHE_MODE_IGNORE) # XXX: ignore?

					return script_resource._get_source_code()

		#except Exception:
		#	pass # XXX

		raise ImportError

	@staticmethod
	def source_to_code(data, path='<string>'):
		return compile(data,
			filename = path,
			mode = 'exec',
			flags = __class__.compile_flags,
			dont_inherit = True,
			optimize = -1) # XXX

	def is_package(self, fullname):
		if (filename := self._get_filename(fullname)) is None:
			raise ImportError

		return (
			filename.endswith('/')
			or filename.endswith('/__init__.py')
			or filename.endswith('/__init__.pyc')
		)

	def find_spec(self, fullname, path, target=None):
		if (filename := self._get_filename(fullname)) is None:
			return None

		is_package = self.is_package(fullname)
		loader = self if not filename.endswith('/') else None
		origin = filename

		return importlib.util.spec_from_loader(fullname,
			loader = loader, origin = origin, is_package = is_package)

	def invalidate_caches(self):
		_cache.clear()


GodotFileSystemModuleImporter = GodotFileSystemModuleImporter()


def install():
	sys.meta_path.insert(0, GodotFileSystemModuleImporter)


def get_module_path_from_name(module_name: str) -> str | None:
	return _cache.get_module_path_from_name(module_name)

def get_module_name_from_path(module_path: str) -> str | None:
	return _cache.get_module_name_from_path(module_path)


