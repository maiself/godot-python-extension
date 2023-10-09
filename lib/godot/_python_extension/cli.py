import sys
import signal
import time
import itertools
import types
import inspect
import textwrap

import godot

from . import utils


_python_commands = {}

def _python_command(func):
	name = func.__name__.strip('_')
	_python_commands[name] = func
	return func


def _install_signal_handlers():
	_last_sigint_time = 0

	def _sigint_handler(*args):
		nonlocal _last_sigint_time

		now = time.time()

		if now - _last_sigint_time < 0.5:
			print('\n\033[93;1mReceived SIGINT twice in a half second, quitting...\033[0m')

			godot.Callable(godot.Engine.get_main_loop().quit).call_deferred()

			_last_sigint_time = 0
			return

		_last_sigint_time = now

	signal.signal(signal.SIGINT, _sigint_handler)


@_python_command
def _version():
	'''Print the Python version used by the extension.'''

	print(f'Python {sys.version} on {sys.platform}')

	sys.exit()


@_python_command
def _usage():
	'''Print usage of the Python extension command line interface.'''

	for name, func in _python_commands.items():
		params = [param.name.upper() for param in inspect.signature(func).parameters.values()]
		print(f'{" "*2}--python-{name} {" ".join(params)}\n{" "*6}{func.__doc__}\n')

	sys.exit()


@_python_command
def _help(name):
	'''Open the interactive help for the object named NAME. (ex: godot.Node.get_children)'''

	if name is None:
		_usage()
		sys.exit()

	obj = utils.resolve_name(name)

	import pydoc
	pydoc.help(obj)

	sys.exit()


@_python_command
def _repl():
	'''Start Python's interactive interpreter from inside the engine.'''

	__main__ = {'godot': godot}
	sys.modules['__main__'] = __main__

	import code
	import readline
	import rlcompleter

	readline.parse_and_bind('tab: complete')
	readline.set_completer(rlcompleter.Completer(__main__).complete)

	banner = textwrap.dedent(f'''
		Python {sys.version} on {sys.platform}
		Type "help", "copyright", "credits" or "license" for more information.
		>>> import godot''').lstrip()
	code.interact(local=__main__, banner=banner, exitmsg='')

	sys.exit()


@_python_command
def _module(module_name):
	'''Search for and run the module named MODULE_NAME as `__main__`.'''
	raise NotImplementedError # TODO


@_python_command
def _command(command_code):
	'''Execute the statements given in COMMAND_CODE.'''
	raise NotImplementedError # TODO


@_python_command
def _script(script_path):
	'''Execute the script at located SCRIPT_PATH as `__main__`.'''
	raise NotImplementedError # TODO


def _parse_args() -> tuple[list, dict]:
	args = []
	kwargs = {}

	pairwise_args = itertools.pairwise(itertools.chain(godot.OS.get_cmdline_args(), (None,)))

	for arg, next_arg in pairwise_args:
		if arg.startswith('--'):
			if '=' in arg:
				key = arg.removeprefix('--').split('=', 1)[0]
				value = arg.split('=', 1)[-1]

			else:
				key = arg.removeprefix('--')
				value = None

				if next_arg is not None and not next_arg.startswith('-'):
					value = next_arg
					next(pairwise_args)

			kwargs[key] = value

		elif arg.startswith('-'):
			continue

		else:
			args.append(arg)

	return args, kwargs


def _try_run_python_command():
	args, kwargs = _parse_args()

	for key, value in kwargs.items():
		if key == 'python':
			key, value = f'python-{value}', None

		if not key.startswith('python-'):
			continue

		name = key.removeprefix('python-')

		if func := _python_commands.get(name):
			if inspect.signature(func).parameters:
				func(value)
			else:
				func()


def main():
	# XXX: ensure sys.argv is set elsewhere
	sys.argv[1:] = [str(arg) for arg in godot.OS.get_cmdline_user_args()]

	_try_run_python_command()

	_install_signal_handlers()


