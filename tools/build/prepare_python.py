#!/usr/bin/env python3

import pathlib
import contextlib
import subprocess
import shutil
import dataclasses
import urllib.request


@dataclasses.dataclass
class PlatformConfig:
	platform: str
	arch: str
	python_version_major: str
	python_version_minor: str
	python_version_patch: str
	build: str
	source_url: str
	so_suffixes: list[str]
	ext_suffixes: list[str]
	so_path: str
	python_lib_dir: str
	python_ext_dir: str
	executable: str

	@property
	def name(self):
		return f'{self.platform}-{self.arch}-py{self.python_version_patch}-ig{self.build}'


def configure(platform: str, arch: str, python_version: str, build: str):
	python_version_major = python_version.split(".")[0]
	python_version_minor = ".".join(python_version.split(".")[:2])

	source_base_url = 'https://github.com/indygreg/python-build-standalone/releases/download/'

	shared_args = dict(
		platform = platform,
		arch = arch,
		python_version_major = python_version_major,
		python_version_minor = python_version_minor,
		python_version_patch = python_version,
		build = build,
	)

	arch_indygreg = {
		'x86_64': 'x86_64',
		'arm64': 'aarch64',
	}[arch]

	if platform == 'linux':
		return PlatformConfig(
			**shared_args,
			source_url = source_base_url +
				f'{build}/cpython-{python_version}+{build}-{arch_indygreg}-unknown-linux-gnu-install_only.tar.gz',
			so_suffixes = ['.so'],
			ext_suffixes = ['.so'],
			so_path = f'lib/libpython{python_version_minor}.so.1.0',
			python_lib_dir = f'lib/python{python_version_minor}',
			python_ext_dir = f'lib/python{python_version_minor}/lib-dynload',
			executable = f'bin/python{python_version_minor}',
		)

	if platform == 'windows':
		return PlatformConfig(
			**shared_args,
			source_url = source_base_url +
				f'{build}/cpython-{python_version}+{build}-{arch_indygreg}-pc-windows-msvc-shared-install_only.tar.gz',
			so_suffixes = ['.dll'],
			ext_suffixes = ['.dll', '.pyd'],
			so_path = f'python{python_version_minor.replace(".", "")}.dll',
			python_lib_dir = 'Lib',
			python_ext_dir = 'DLLs',
			executable = 'python.exe',
		)

	if platform == 'macos':
		return PlatformConfig(
			**shared_args,
			source_url = source_base_url +
				f'{build}/cpython-{python_version}+{build}-{arch_indygreg}-apple-darwin-install_only.tar.gz',
			so_suffixes = ['.so', '.dylib'],
			ext_suffixes = ['.so'],
			so_path = f'lib/libpython{python_version_minor}.dylib',
			python_lib_dir = f'lib/python{python_version_minor}',
			python_ext_dir = f'lib/python{python_version_minor}/lib-dynload',
			executable = f'bin/python{python_version_minor}',
		)

	raise ValueError("Unsupported platform.")


def fetch_python_for_config(config: PlatformConfig, target):
	print(f'fetching python for {config.name}')
	print(f'  {config.source_url}')

	target_path = pathlib.Path(target.path)
	with urllib.request.urlopen(config.source_url) as response:
		target_path.parent.mkdir(parents=True, exist_ok=True)
		with target_path.open('wb') as dest:
			shutil.copyfileobj(response, dest)


def prepare_for_platform(config: PlatformConfig, src_dir: pathlib.Path, dest_dir: pathlib.Path) -> pathlib.Path:
	print(f'preparing for {config.name}')

	shutil.unpack_archive(src_dir / pathlib.Path(config.source_url).name, extract_dir = src_dir)

	src = src_dir / 'python'
	src_lib_path = src / config.so_path
	lib_filename = pathlib.Path(config.so_path).name

	if config.platform == 'macos':
		# Rename the library id (which we depend on) to be in @rpath.
		# (it defaults to /install/lib/)
		subprocess.run(['install_name_tool', '-id', f'@rpath/{lib_filename}', src_lib_path], check=True)

	dest_dir.mkdir(parents=True, exist_ok=True)
	shutil.copy2(src_lib_path, dest_dir)

	if config.platform == 'macos':
		subprocess.run(['strip', '-x', dest_dir / lib_filename], check=True)
	else:
		subprocess.run(['strip', '-s', dest_dir / lib_filename], check=True)

	if (src / config.python_ext_dir).exists():
		dest_ext_dir = dest_dir / f'python{config.python_version_minor}' / 'lib-dynload'
		dest_ext_dir.mkdir(parents=True, exist_ok=True)

		for path in (src / config.python_ext_dir).iterdir():
			if any(suffix in path.suffixes for suffix in config.ext_suffixes):
				shutil.copy2(path, dest_ext_dir)

	shutil.make_archive(dest_dir / f'python{config.python_version_minor}-lib', 'zip', root_dir=src / config.python_lib_dir, base_dir='')


def get_python_for_platform(config: PlatformConfig, src_dir: pathlib.Path) -> pathlib.Path:
	return src_dir / 'python' / config.executable
