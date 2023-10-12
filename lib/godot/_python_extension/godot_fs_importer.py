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



def _glob_godot_path(path: str):
	dirs = godot.DirAccess.get_directories_at(path)
	files = godot.DirAccess.get_files_at(path)

	if path.endswith('//'):
		path = path.removesuffix('/')

	for file in files:
		if file.endswith('.py'):
			yield '/'.join((path, file))

	for dir_ in dirs:
		yield from _glob_godot_path('/'.join((path, dir_)))



#@utils.log_method_calls
class GodotFileSystemModuleImporter(importlib.abc.MetaPathFinder, importlib.abc.ExecutionLoader):
	compile_flags = __future__.annotations.compiler_flag

	_known_fullnames = {}

	@classmethod
	def _get_filename(cls, fullname: str) -> str | None:
		if fullname.startswith('godot.'):
			return None

		if not cls._known_fullnames:
			files = []

			for path in (path for path in sys.path if path.startswith('res://')):
				files.extend(_glob_godot_path(path))

			for file in files:
				name = utils.godot_path_to_python_module_name(file)

				if name.endswith('.__init__'):
					name = name.removesuffix('.__init__')

				parts = name.split('.')[:-1]
				while parts:
					pkg = '.'.join(parts)

					if pkg not in cls._known_fullnames:
						cls._known_fullnames[pkg] = \
							utils.python_module_name_to_godot_path(pkg).removesuffix('.py') + '/'

					else:
						break

					parts.pop()

				cls._known_fullnames[name] = file

		return cls._known_fullnames.get(fullname)

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
		__class__._known_fullnames.clear()


GodotFileSystemModuleImporter = GodotFileSystemModuleImporter()


def install():
	sys.meta_path.insert(0, GodotFileSystemModuleImporter)


