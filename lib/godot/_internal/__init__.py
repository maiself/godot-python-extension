import sys
import pathlib
import importlib

import _gdextension as gde

from . import module_machinery
from . import utils


def _init():
	sys.path.remove('') # XXX: current directory shouldnt be in path, check interpreter initialization
	if any(path in sys.path for path in ('', '.', './')):
		raise RuntimeError(f'current directory found in sys.path')

	with utils.timer('api parse'):
		from . import api_info

	module_machinery.initialize_module()

	sys.path.insert(0, 'res://') # XXX


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


