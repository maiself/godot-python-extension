import sys
import pathlib
import importlib

try:
	import _gdextension as gde

except ModuleNotFoundError:
	gde = None

if not gde:
	try:
		from . import _gdextension as gde
	except Exception as _exc:
		raise ImportError(
			"the 'godot' module cannot be initialized, "
			"unable to import the required '_gdextension' module"
		) from _exc


from . import utils


def _init():
	_check_env()
	_try_restart_headless_if_cli()
	_load_api_data()

	from . import module_machinery
	module_machinery.initialize_module()

	sys.path.insert(0, 'res://') # XXX


def _check_env():
	if getattr(gde, '_is_stub', False):
		return

	#sys.path.remove('') # XXX: current directory shouldnt be in path, check interpreter initialization
	if any(path in sys.path for path in ('', '.', './')):
		raise RuntimeError(f'current directory found in sys.path')


def _try_restart_headless_if_cli():
	# XXX: is there a better way?
	# is there a better place to put this?

	try:
		if '--headless' not in sys.argv:
			import itertools
			pairwise_args = itertools.pairwise(itertools.chain(sys.argv, (None,)))

			args = []

			for arg, next_arg in pairwise_args:
				if arg == '--path':
					# skip passing along path as cwd will have already been changed to it
					next(pairwise_args)
					path = next_arg

				else:
					args.append(arg)

			for arg in args:
				if arg.startswith('--python'):
					# python cli option as specified, restart as headless
					import os
					os.execlp(args[0], args[0], '--quiet', '--headless', *args[1:])

	except Exception as exc:
		# if anything goes wrong then just continue
		pass


def _load_api_data():
	with utils.timer('api parse'):
		res_root = pathlib.Path().resolve()

		likely_running_from_editor = (res_root / 'project.godot').exists() and (res_root / '.godot').exists()

		if not likely_running_from_editor:
			import gzip

			# get api json from packed data
			data = utils.get_file_as_bytes('res://.python/extension_api.json.gz')
			if data:
				data = gzip.decompress(data)

		else:
			# try to get or update cached api json when running from editor
			python_dir = res_root / '.python'

			if not python_dir.exists():
				# create the python cache dir
				python_dir.mkdir()
				(python_dir / '.gdignore').touch()
				(python_dir / '.gitignore').write_text('*\n')

			api_json_path = python_dir / 'extension_api.json'

			api_json_mtime_ns = api_json_path.stat().st_mtime_ns if api_json_path.exists() else 0
			godot_binary_mtime_ns = pathlib.Path(sys.executable).stat().st_mtime_ns

			# check mtimes
			if api_json_mtime_ns // 1000**3 != godot_binary_mtime_ns // 1000**3:
				# cached api json either doens't exist or doesn't match the current godot binary
				import os
				import subprocess

				# generate api json in cache dir
				subprocess.run([sys.executable, '--quiet', '--headless', '--dump-extension-api-with-docs'],
					cwd = str(python_dir),
					check = True,
				)

				# set api json mtime to match the godot binary
				os.utime(api_json_path, ns=(godot_binary_mtime_ns, godot_binary_mtime_ns))

			# read the cached api json
			data = api_json_path.read_text()

		# load api from data
		from . import api_info
		api_info.load_api_data(data)


_init()


def initialize(level: gde.GDExtensionInitializationLevel):
	#print(f'\033[92;1;3minitializing level: {level}\033[0m')

	if level == gde.GDEXTENSION_INITIALIZATION_CORE:
		pass

	elif level == gde.GDEXTENSION_INITIALIZATION_SCENE:
		importlib.import_module('godot._python_extension')

		#from . import test # XXX

		for ext_path in pathlib.Path().glob('*.pyextension'):
			text = ext_path.read_text()
			if 'python_path' not in text and 'python_package' not in text:
				continue

			lines = text.splitlines()
			for line in lines:
				if line.startswith('python_path'):
					python_path = line.split('=')[1].strip()[1:-1]

				if line.startswith('python_package'):
					python_package = line.split('=')[1].strip()[1:-1]

					#print(f'importing {python_package}')

					with utils.exception_note(f'While importing extension package {python_package!r}'):
						importlib.import_module(python_package)


def deinitialize(level: gde.GDExtensionInitializationLevel):
	#print(f'\033[92;1;3mdeinitializing level: {level}\033[0m')
	pass


