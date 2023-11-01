import sys
import os
import pathlib
import types
import re
import itertools


from . import build_utils


def _stable_unique(list_: list) -> list:
	'''Return a copy of `list` containing only unique elements in their the original order.'''
	return list({k: None for k in list_}.keys())


def get_python_config_vars(env) -> types.SimpleNamespace:
	config_vars = types.SimpleNamespace()

	if not env.get('python_lib_dir'):
		# run the target python's sysconfig module to get config vars
		target_python = build_utils.get_executable_path('python', env)

		lines = build_utils.run_with_output(target_python, '-m', 'sysconfig').splitlines()

		sysconfig_vars = {
				match_['key']: match_['value']
				for line in lines
				if (match_ := re.search(r'''(?P<key>[\w]+)\s*=\s*["'](?P<value>.*)["']''', line))
			}

		# XXX: fixup when running thru wine
		if target_python.endswith('.exe') and sys.platform.startswith('linux'):
			for key, value in sysconfig_vars.items():
				if value.lower().startswith('z:'):
					value = value[2:]
					sysconfig_vars[key] = value

		# XXX: fixup when using a python-build-standalone build
		for key, value in sysconfig_vars.items():
			if value.startswith('/install'):
				value = value.removeprefix('/install').removeprefix('/')
				value = str(pathlib.Path(target_python).resolve().parent.parent / value)
				sysconfig_vars[key] = value

	else:
		# search the target python's lib or build dir for the `_sysconfigdata_*.py` file to get config vars
		search_path = env.get('python_lib_dir')

		# TODO: also search into the `python*.zip` if found

		sysconfigdata_files = [
				path
				for path in pathlib.Path(search_path).glob('**/*')
				if (match_ := re.fullmatch(r'_sysconfigdata_.*\.py', path.name))
			]

		if not sysconfigdata_files:
			print(f'no sysconfigdata files found in {search_path}')
			sys.exit(1)

		if len(sysconfigdata_files) > 1:
			print(f'found more than one sysconfigdata file in {search_path}:')
			for path in sysconfigdata_files:
				print(f'  {path}')
			sys.exit(1)

		# the `_sysconfigdata_*.py` file should contain a single `dict` named `build_time_vars`
		ns = {}
		exec(sysconfigdata_files[0].read_text(), ns, ns)

		sysconfig_vars = ns['build_time_vars']

	#for k, v in sysconfig_vars.items():
	#	print('  ', k, '=', repr(v))

	version = sysconfig_vars.get('VERSION')
	abiflags = sysconfig_vars.get('abiflags', sysconfig_vars.get('ABIFLAGS'))

	python_lib = f'python{version}{abiflags}'

	#if env['use_mingw']: # XXX: which condition to use?
	if env['platform'] == 'windows':
		python_lib += '.dll.a' # XXX: '.a' added to workaround weirdness with scons

	def normpath(path: str) -> str:
		# XXX: not so nice...
		if not path:
			return ''
		path = pathlib.Path(path.replace('\\', '/'))
		if not path.exists():
			path = str(path).lower()
		return path

	config_vars.include_flags = _stable_unique([
			f'-I{normpath(value)}'
			for name in ('INCLUDEPY', 'include', 'platinclude')
			if (value := sysconfig_vars.get(name))
		])

	config_vars.link_flags = _stable_unique([
			*[f'-L{normpath(sysconfig_vars.get("LIBDIR"))}'] * bool(sysconfig_vars.get("LIBDIR")),
			*itertools.chain(*(
				value.split()
				for name in ('LIBS', 'SYSLIBS')
				if (value := sysconfig_vars.get(name))
			)),
		])

	config_vars.link_libs = _stable_unique([
			*itertools.chain(*(
				(v.removeprefix('-l') for v in value.split())
				for name in ('LIBS', 'SYSLIBS')
				if (value := sysconfig_vars.get(name))
			)),
			python_lib,
		])

	config_vars.ldlibrary = sysconfig_vars.get('INSTSONAME')
	#config_vars.ldlibrary = sysconfig_vars.get('LDLIBRARY')

	if env['use_mingw']:
		# XXX: posix vs nt install scheme mismatch?
		config_vars.include_flags.insert(0,
			os.path.join(config_vars.include_flags[0], f'python{version}{abiflags}'))
		config_vars.include_flags = _stable_unique(config_vars.include_flags)

	#print(f'\n{config_vars}\n')

	return config_vars



