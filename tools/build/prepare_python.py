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
	source_url: str
	so_suffixes: list[str]
	ext_suffixes: list[str]
	so_path: str
	python_lib_dir: str
	python_bin_paths: list[str]
	python_ext_dir: str
	executable: str

	@property
	def name(self):
		return f'{self.platform}-{self.arch}'


platform_configs = {}

def add_platform_config(*args, **kwargs):
	config = PlatformConfig(*args, **kwargs)
	key = (config.platform, config.arch)
	platform_configs[key] = config


add_platform_config(
	platform = 'linux',
	arch = 'x86_64',
	source_url = 'https://github.com/indygreg/python-build-standalone/releases/download/'
		'20231002/cpython-3.12.0+20231002-x86_64-unknown-linux-gnu-install_only.tar.gz',
	so_suffixes = ['.so'],
	ext_suffixes = ['.so'],
	so_path = 'lib/libpython3.12.so.1.0',
	python_lib_dir = 'lib/python3.12',
	python_bin_paths = ['bin'],
	python_ext_dir = 'lib/python3.12/lib-dynload',
	executable = 'bin/python3.12',
)

add_platform_config(
	platform = 'windows',
	arch = 'x86_64',
	source_url = 'https://github.com/indygreg/python-build-standalone/releases/download/'
		'20231002/cpython-3.12.0+20231002-x86_64-pc-windows-msvc-shared-install_only.tar.gz',
	so_suffixes = ['.dll'],
	ext_suffixes = ['.dll', '.pyd'],
	so_path = 'python312.dll',
	python_lib_dir = 'Lib',
	python_bin_paths = ['python.exe', 'pythonw.exe'],
	python_ext_dir = 'DLLs',
	executable = 'python.exe',
)

add_platform_config(
	platform = 'macos',
	arch = 'x86_64',
	source_url = 'https://github.com/indygreg/python-build-standalone/releases/download/'
		'20231002/cpython-3.12.0+20231002-x86_64-apple-darwin-install_only.tar.gz',
	so_suffixes = ['.so', '.dylib'],
	ext_suffixes = ['.so'],
	so_path = 'lib/libpython3.12.dylib',
	python_lib_dir = 'lib/python3.12',
	python_bin_paths = ['bin'],
	python_ext_dir = 'lib/python3.12/lib-dynload',
	executable = 'bin/python3.12',
)

add_platform_config(
	platform = 'macos',
	arch = 'arm64',
	source_url = 'https://github.com/indygreg/python-build-standalone/releases/download/'
		'20231002/cpython-3.12.0+20231002-aarch64-apple-darwin-install_only.tar.gz',
	so_suffixes = ['.so', '.dylib'],
	ext_suffixes = ['.so'],
	so_path = 'lib/libpython3.12.dylib',
	python_lib_dir = 'lib/python3.12',
	python_bin_paths = ['bin'],
	python_ext_dir = 'lib/python3.12/lib-dynload',
	executable = 'bin/python3.12',
)


def fetch_python_for_platform(platform: str, arch: str, dest_dir: pathlib.Path):
	config = platform_configs[(platform, arch)]

	print(f'fetching python for {config.name}')
	print(f'  {config.source_url}')

	with urllib.request.urlopen(config.source_url) as response:
		with (dest_dir / pathlib.Path(config.source_url).name).open('wb') as dest:
			shutil.copyfileobj(response, dest)


def prepare_for_platform(platform: str, arch: str,
		src_dir: pathlib.Path, dest_dir: pathlib.Path) -> pathlib.Path:
	config = platform_configs[(platform, arch)]

	print(f'preparing for {config.name}')

	shutil.unpack_archive(src_dir / pathlib.Path(config.source_url).name, extract_dir = src_dir)

	src_python = src_dir / 'python'
	src_lib_path = src_python / config.so_path
	lib_filename = pathlib.Path(config.so_path).name

	if platform == 'macos':
		# Rename the library id (which we depend on) to be in @rpath.
		# (it defaults to /install/lib/)
		subprocess.run(['install_name_tool', '-id', f'@rpath/python/lib/{lib_filename}', src_lib_path], check=True)


	dest_dir_python = dest_dir / 'python'
	dest_dir_python_lib = dest_dir_python / 'lib'
	dest_dir_python_lib.mkdir(parents=True, exist_ok=True)

	shutil.copy2(src_lib_path, dest_dir_python_lib)
	if platform == 'macos':
		subprocess.run(['strip', '-x', dest_dir_python_lib / lib_filename], check=True)
	else:
		subprocess.run(['strip', '-s', dest_dir_python_lib / lib_filename], check=True)

	for bin_path in config.python_bin_paths:
		src_path: pathlib.Path = src_python / bin_path

		if src_path.is_file():
			shutil.copy2(src_path, dest_dir_python / bin_path)
		elif src_path.is_dir():
			shutil.copytree(src_path, dest_dir_python / bin_path, dirs_exist_ok=True)
		else:
			raise RuntimeError(f"Cannot find file: {src_path}")

		if bin_path == 'bin':
			# Ignore the bin path in Godot.
			(dest_dir_python / bin_path / '.gdignore').touch()

	if (src_python / config.python_ext_dir).exists():
		dest_ext_dir = dest_dir_python_lib / 'python3.12' / 'lib-dynload'
		dest_ext_dir.mkdir(parents=True, exist_ok=True)

		for path in (src_python / config.python_ext_dir).iterdir():
			if any(suffix in path.suffixes for suffix in config.ext_suffixes):
				shutil.copy2(path, dest_ext_dir)

	shutil.make_archive(dest_dir / 'python312', 'zip', root_dir=src_python / config.python_lib_dir, base_dir='')


def get_python_for_platform(platform: str, arch: str, src_dir: pathlib.Path) -> pathlib.Path:
	config = platform_configs[(platform, arch)]

	src = src_dir / 'python'

	return src / config.executable



def main():
	for platform in platform_configs:
		prepare_for_platform(*platform)


if __name__ == '__main__':
	main()

