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
	python_ext_dir = 'DLLs',
	executable = 'python.exe',
)


def fetch_python_for_platform(platform: str, arch: str):
	config = platform_configs[(platform, arch)]

	print(f'fetching python for {config.name}')
	print(f'  {config.source_url}')

	with urllib.request.urlopen(config.source_url) as response:
		with (pathlib.Path() / pathlib.Path(config.source_url).name).open('wb') as dest:
			shutil.copyfileobj(response, dest)


def prepare_for_platform(platform: str, arch: str, dest: pathlib.Path) -> pathlib.Path:
	config = platform_configs[(platform, arch)]

	print(f'preparing for {config.name}')

	shutil.unpack_archive(pathlib.Path(config.source_url).name)

	src = pathlib.Path().resolve() / 'python'

	dest.mkdir(parents=True, exist_ok=True)

	shutil.copy2(src / config.so_path, dest)
	subprocess.run(['strip', '-s', str(dest / pathlib.Path(config.so_path).name)], check=True)

	if (src / config.python_ext_dir).exists():
		dest_ext_dir = dest / 'python3.12' / 'lib-dynload'
		dest_ext_dir.mkdir(parents=True, exist_ok=True)

		for path in (src / config.python_ext_dir).iterdir():
			if any(suffix in path.suffixes for suffix in config.ext_suffixes):
				shutil.copy2(path, dest_ext_dir)

	with contextlib.chdir(src / config.python_lib_dir):
		subprocess.run(['zip', '-q', '-r', str(dest / 'python312.zip'),
			*(str(file) for file in pathlib.Path().iterdir())])


def get_python_for_platform(platform: str, arch: str) -> pathlib.Path:
	config = platform_configs[(platform, arch)]

	src = pathlib.Path().resolve() / 'python'

	return src / config.executable



def main():
	for platform in platform_configs:
		prepare_for_platform(*platform)


if __name__ == '__main__':
	main()

