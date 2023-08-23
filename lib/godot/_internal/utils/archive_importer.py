import sys
import io
import pathlib
import importlib.abc
import tarfile
import zipfile
import marshal


# NOTE: This file intentionally avoids importing from any other local modules.
# It is copied directly into the the extension shared library and used to load
# everything else from the embedded module archive. As such nothing else is
# available to use here.


# XXX: split class?
class ArchiveTraversable(importlib.resources.abc.Traversable, importlib.resources.abc.ResourceReader):
	def __init__(self, archive, path):
		self._archive = archive
		self._path = path

	def __repr__(self):
		return f'<{type(self).__name__} {getattr(self, "_path", None)!r}>'

	# importlib.resources.abc.Traversable

	@property
	def name(self):
		if self._path.endswith('/'):
			return self._path.rsplit('/', 2)[-2]
		return self._path.rsplit('/', 1)[-1]

	@property
	def _valid(self):
		return self._path in self._archive._archive_names

	def iterdir(self):
		return (type(self)(self._archive, path)
			for path in self._archive._archive_names if path.startswith(self._path))

	def is_dir(self):
		return self._path == '' or self._path.endswith('/')

	def is_file(self):
		return not self.is_dir()

	def joinpath(self, child):
		if self._path == '':
			path = child
		else:
			path = self._path + child

		if path not in self._archive._archive_names and path+'/' in self._archive._archive_names:
			path += '/'

		return type(self)(self._archive, path)

	def open(self, mode='r'):
		return io.BytesIO(self._archive.get_data(self._path))

	# importlib.resources.abc.ResourceReader

	def open_resource(self, name):
		return self.joinpath(name).open()

	def resource_path(self, name):
		child = self.joinpath(name)
		if not child._valid:
			raise FileNotFoundError
		return child._path

	def is_resource(self, name):
		child = self.joinpath(name)
		if not child._valid:
			raise FileNotFoundError
		return not child._path.endswith('/')

	def contents(self):
		return (child.name for child in self.iterdir())


class ArchiveImporter(importlib.abc.MetaPathFinder, importlib.abc.FileLoader,
		importlib.resources.abc.TraversableResources):
	def __init__(self, archive: tarfile.TarFile | zipfile.ZipFile | bytes | str | pathlib.Path, *,
			name: str | None = None, compile_flags = 0):
		self._archive = archive
		self._name = name
		self._compile_flags = compile_flags

		if self._name is None and isinstance(self._archive, (str, pathlib.Path)):
			self._name = str(self._archive)

		archive_names = self._prepare_archive()
		self._archive_names = archive_names

		self._fullnames = {}

		for file in archive_names:
			if '.' not in file:
				continue

			path, ext = file.rsplit('.', 1)

			if ext not in ('py', 'pyc'):
				continue

			name = path.replace('/', '.')

			if name.endswith('.__init__'):
				name = name.removesuffix('.__init__')

			if self._fullnames.get(name, '').endswith('.pyc'):
				continue

			parts = name.split('.')[:-1]

			while parts:
				pkg = '.'.join(parts)

				if pkg in self._fullnames:
					break

				self._fullnames[pkg] = pkg.replace('.', '/') + '/'

				parts.pop()

			self._fullnames[name] = file

	def __repr__(self):
		try:
			if self._name is not None:
				return f'<{type(self).__qualname__} object name={self._name!r}>'
			return f'<{type(self).__qualname__} object archive={self._archive!r}>'

		except Exception:
			return super().__repr__()


	def _prepare_archive(self) -> list[str]:
		match self._archive:
			case tarfile.TarFile():
				self._extract = self._archive.extractfile
				return self._archive.getnames()

			case zipfile.ZipFile():
				self._extract = self._archive.open
				return self._archive.namelist()

			case bytes():
				self._archive = io.BytesIO(self._archive)
				return self._prepare_archive()

			case str() | pathlib.Path():
				with open(path, 'rb') as file:
					self._archive = file.read()
				return self._prepare_archive()

			case io.BytesIO():
				magic = self._archive.read(4)
				self._archive.seek(0)

				if magic == b'PK\x03\x04':
					self._archive = zipfile.ZipFile(self._archive)
				else:
					self._archive = tarfile.open(fileobj=self._archive)

				return self._prepare_archive()

			case _:
				raise TypeError(
					f'archive must be an instance of tarfile.TarFile, zipfile.ZipFile, '
					f'bytes, str or path.Pathlib, received ')#{self._archive!r}')

	def get_resource_reader(self, fullname):
		if not self.is_package(fullname):
			return None

		filename = self.get_filename(fullname)
		if not filename.endswith('/'):
			filename = filename.rsplit('/', 1)[0] + '/'

		return ArchiveTraversable(self, filename)

	def files(self):
		return ArchiveTraversable(self, '')

	def _get_filename(self, fullname: str) -> str | None:
		return self._fullnames.get(fullname)

	def get_filename(self, fullname: str) -> str:
		if filename := self._get_filename(fullname):
			return filename

		raise ImportError

	def get_data(self, filename):
		with self._extract(filename) as file:
			return file.read()

	def get_code(self, fullname):
		if (filename := self._get_filename(fullname)) is None:
			raise ImportError

		data = self.get_data(filename)

		if filename.endswith('.pyc'):
			return marshal.loads(data[16:])

		return self.source_to_code(data, filename)

	def get_source(self, fullname):
		if (filename := self._get_filename(fullname)) is None:
			raise ImportError

		if filename.endswith('.pyc'):
			filename = filename.removesuffix('c')

		return self.get_data(filename).decode()

	def source_to_code(self, data, path='<string>'):
		return compile(data,
			filename = path,
			mode = 'exec',
			flags = self._compile_flags,
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


