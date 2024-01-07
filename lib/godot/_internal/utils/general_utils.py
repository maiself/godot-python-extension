import sys
import builtins
import importlib
import importlib.machinery
import contextlib
import functools
import textwrap
import time
import traceback
import atexit
import collections.abc
import itertools


unspecified = type('unspecified', (type, ), dict(__repr__ = lambda self: 'unspecified'))('unspecified', (), {})


def fullname(obj: object) -> str:
	'''Return the full name of a named object including its module and qualname.'''
	return '.'.join((
		*(obj.__module__, ) * (obj.__module__ not in (None, 'builtins')),
		(obj.__qualname__ if hasattr(obj, '__qualname__') else obj.__name__)
	))


_resolved_name_cache = {} # XXX: may hold old values

class _resolve_name_error:
	def __init__(self, name: str, exception: Exception):
		self.name = name
		self.exception = exception




import inspect

def get_args_dict(level: int = 0) -> dict:
	frame = inspect.currentframe().f_back
	for i in range(-level):
		frame = frame.f_back
	info = inspect.getargvalues(frame)
	assert info.varargs is None
	return {**{arg: info.locals[arg] for arg in info.args}, **info.locals[info.keywords]}


def _get_caller_filename(level: int = 0) -> str:
	assert(level <= 0)

	try:
		frame = inspect.currentframe().f_back
		for i in range(-level):
			frame = frame.f_back

		return inspect.getframeinfo(frame).filename

	except Exception:
		return ''


def update_globals(*args, level: int = 0, **kwargs):
	assert(level <= 0)

	frame = inspect.currentframe().f_back
	for i in range(-level):
		frame = frame.f_back

	frame.f_globals.update(*args, **kwargs)




import types
import re
import inspect
import functools
import textwrap



def log_calls(func, cls=None):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		#try:

			def fa(arg):
				if m := re.fullmatch(r'<[\w.]*?([\w]+) object at 0x[a-f0-9]+>', f'{arg!r}'):
					if type(arg).__module__ == 'godot':
						return f'<godot.{type(arg).__qualname__} object>'
					return f'<{type(arg).__qualname__} object>'
					return f'<{m.group(1)}>'
				return f'{arg!r}'

			prefix = cls.__name__ + '.' if cls else ''
			#if isinstance(args[0], cls):
			#	prefix = fa(args[0]) + '.'

			a = (fa(arg) for arg in (args[1:] if cls and isinstance(args[0], cls) else args))
			kw = (f'{name} = {fa(val)}' for name, val in kwargs.items())
			a = (*a, *kw)

			#print(func._format)

			f = f'{prefix}{func.__name__}({", ".join(a)})'
			f = textwrap.fill(f, 120,
					initial_indent = ' '*0,
					subsequent_indent = ' '*4,
					replace_whitespace = False,
					max_lines = 2,
				)

			print(f'\033[35;1m{f}\033[0;35;2m -> ...\033[0m')

			try:
				res = func(*args, **kwargs)
			except BaseException as exc:
				exc.__traceback__ = exc.__traceback__.tb_next
				raise

			r = f'{fa(res)}'
			r = textwrap.fill(r, 120,
					initial_indent = ' '*len(f.splitlines()[-1]),
					subsequent_indent = ' '*8,
					replace_whitespace = False,
					max_lines = 2,
				)
			r = r[len(f.splitlines()[-1]):]

			print(f'\033[35;2m{f} -> \033[0;35;1m{r}\033[0m') # XXX: exc

			return res
		#except Exception as e:
		#	print(e) # XXX: why is this needed?
		#finally:
		#	pass

	return wrapper



@atexit.register
def _clear_resolved_name_cache():
	_resolved_name_cache.clear()


#@log_calls
def resolve_name(name, *, context=None, use_cache=True) -> object: # XXX: assess use_cache default
	'''Return an object from its fullname by importing its containing module and following the attribute chain.'''

	#print(f'resolve_name({name!r})', _get_caller_filename(-2))

	if context:
		use_cache = False

	if use_cache:
		if obj := _resolved_name_cache.get(name): # XXX
			if isinstance(obj, _resolve_name_error):
				raise obj.exception from None

			return obj

	try:
		if '[' in name and name.endswith(']'):
			type_name, params = name[:-1].split('[', 1)
			obj = resolve_name(type_name, context=context, use_cache=use_cache)[*(
					resolve_name(param.strip(), context=context, use_cache=use_cache) for param in params.split(',')
				)]

			if use_cache:
				_resolved_name_cache[f'{type_name}[{params}]'] = obj # XXX

			return obj

		parts = name.split('.')

		if context:
			try:
				obj = context
				for part in parts:
					obj = getattr(obj, part)

			except AttributeError as error:
				if error.obj is not obj or error.name != part:
					raise

				try:
					obj = builtins
					for part in parts:
						obj = getattr(obj, part)

				except AttributeError as inner_error:
					if inner_error.obj is not obj or inner_error.name != part:
						raise

					raise error from None

		else:
			def try_import(name):
				try:
					return importlib.import_module(name)
				except ModuleNotFoundError:
					return None

			for i in range(len(parts), 0, -1):
				if mod := try_import('.'.join(parts[:i])):
					break

			if mod:
				obj = mod
				parts = parts[i:]
			else:
				obj = builtins

			for part in parts:
				obj = getattr(obj, part)

		if use_cache:
			_resolved_name_cache[name] = obj # XXX

		return obj

	except Exception as exc:
		if use_cache and name not in _resolved_name_cache:
			_resolved_name_cache[name] = _resolve_name_error(name, exc) # XXX

		exc.add_note(f'  While trying to resolve name {name!r}')
		raise


def apply_attrs(obj, **attrs):
	'''Apply attrs to obj. Return obj.'''
	for name, value in attrs.items():
		setattr(obj, name, value)
	return obj


def set_attr_if_unspecified(obj, name: str, **kwargs):
	if len(kwargs) != 1 or next(iter(kwargs.keys())) not in ('from_object', 'from_value'):
		raise TypeError(f'either \'from_object\' or \'from_value\' must be provided')

	key, value = kwargs.popitem()

	if getattr(obj, name, unspecified) is not unspecified:
		return

	if key == 'from_object' and value is not unspecified:
		value = getattr(value, name)

	setattr(obj, name, value)


def print_doc(obj):
	'''Print documentation for obj.'''
	import pydoc
	print(pydoc.render_doc(obj))


@contextlib.contextmanager
def print_exceptions_and_continue(except_then=None):
	'''Context manager that catches and prints any exceptions and allows execution to continue.'''
	try:
		yield
		return

	except Exception as exc:
		exc.__traceback__ = exc.__traceback__.tb_next
		print(''.join(format_exception(exc, sgr=(_sgr.bright_yellow, ))).removesuffix('\n'), file=sys.stderr)

	if except_then:
		except_then()


@contextlib.contextmanager
def print_exceptions_and_reraise():
	'''Context manager that catches and prints any exceptions and then reraises them.'''
	try:
		yield
		return

	except Exception as exc:
		exc.__traceback__ = exc.__traceback__.tb_next
		print(''.join(format_exception(exc, sgr=(_sgr.bright_red, ))).removesuffix('\n'), file=sys.stderr)

		raise


@contextlib.contextmanager
def timer(name: str):
	'''Context manager tracks and prints the time taken.'''
	start_time = time.time()
	yield
	end_time = time.time()
	#print(f'{name} time: {(end_time - start_time) * 1000:.2f} ms') # XXX


@contextlib.contextmanager
def exception_note(note, *args, **kwargs):
	'''Context manager that adds a note to any exception raised.

	`note` may be any object convertable to a string or a callable.
	If a callable args and kwargs are forwarded and an object
	convertable to a string should be returned.
	'''

	try:
		yield

	except BaseException as exc:
		exc.__traceback__ = exc.__traceback__.tb_next

		if callable(note):
			note = note(*args, **kwargs)

		exc.add_note(f'\n{note}'.replace('\t', ' '*4))

		raise


def with_context(func):
	'''Decorator that adds a note with call info to any exception raised.'''

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		def make_note():
			lines = []

			for arg in args:
				lines.append(f'{arg!r},')

			for name, value in kwargs.items():
				lines.append(f'{name}: {value!r},')

			lines = [
				textwrap.fill(line, 120,
					initial_indent = ' '*8,
					subsequent_indent = ' '*12,
					replace_whitespace = False,
					max_lines = 5,
				)
				for line in lines
			]

			lines = [f'In call:\n{" "*4}{fullname(func)}(', *lines, f'{" "*4})']

			note = '\n'.join(lines)

			return note

		with exception_note(make_note):
			try:
				return func(*args, **kwargs)
			except BaseException as exc:
				exc.__traceback__ = exc.__traceback__.tb_next
				raise

	return wrapper


def class_set_attr(class_or_namespace: type | types.SimpleNamespace, name: str, value: object):
	setattr(class_or_namespace, name, value)
	if isinstance(class_or_namespace, type) and hasattr(value, '__set_name__'):
		value.__set_name__(class_or_namespace, name)


def swap_members(cls, attr_name=unspecified, with_obj=unspecified):
	if attr_name is unspecified:
		# swap all members of `cls` with `base`
		base = cls.__base__

		for attr_name, value in cls.__dict__.items():
			if attr_name in ('__module__', '__qualname__', '__name__', '__dict__'):
				continue

			if attr_name == '__doc__' and value is None:
				continue

			class_set_attr(cls, attr_name, getattr(base, attr_name, None))
			class_set_attr(base, attr_name, value)

		return cls

	else:
		# swap member `attr_name` with `with_obj`
		orig = getattr(cls, attr_name, None)

		def swap(with_obj):
			try:
				with_obj.__name__ = attr_name
			except AttributeError:
				pass

			class_set_attr(cls, attr_name, with_obj)

			return orig

		if with_obj is not unspecified:
			return swap(with_obj)

		return swap



_importlib_filenames = [
	f'<frozen {k}>' if v.__loader__ is importlib.machinery.FrozenImporter else getattr(v, '__file__', '?')
	for k, v in sys.modules.items() if k.split('.')[0] == 'importlib'
]

_godot_fs_importer_filename = None


def filter_import_tracebacks(exc):
	global _godot_fs_importer_filename

	# lazy init of _godot_fs_importer_filename

	if not _godot_fs_importer_filename:
		try:
			from godot._python_extension import godot_fs_importer
			_godot_fs_importer_filename = godot_fs_importer.__file__

		except Exception:
			pass

	# gather tracebacks into a list

	tracebacks = [exc.__traceback__]

	while tracebacks[-1].tb_next:
		tracebacks.append(tracebacks[-1].tb_next)

	# functions for finding a traceback in the list

	def find_matching_tb(pred, *, start = 0, end = None) -> tuple[int, types.TracebackType | None]:
		for i, tb in enumerate(tracebacks[start:end]):
			if pred(tb):
				return i+start, tb

		return -1, None

	def is_importlib(tb: types.TracebackType) -> bool:
		return tb.tb_frame.f_code.co_filename in _importlib_filenames

	def is_import_terminal(tb: types.TracebackType) -> bool:
		return (
			(is_importlib(tb) and tb.tb_frame.f_code.co_qualname == '_call_with_frames_removed')
			or (tb.tb_frame.f_code.co_filename == _godot_fs_importer_filename
				and tb.tb_frame.f_code.co_qualname == 'GodotFileSystemModuleImporter.source_to_code'
			)
		)

	# remove spans of import tracebacks

	while True:
		start, tb = find_matching_tb(is_importlib)

		if not tb:
			break

		end, tb = find_matching_tb(is_import_terminal, start = start+1)

		if not tb:
			break

		del tracebacks[start:end+1]

	# update tb_next of remaining tracebacks

	tb_next = None
	for tb in reversed(tracebacks):
		tb.tb_next = tb_next
		tb_next = tb

	exc.__traceback__ = tb_next


def format_exception(exc, *, sgr=()):
	filter_import_tracebacks(exc)
	return list(ColoredTracebackException(type(exc), exc, exc.__traceback__, compact=True, sgr=sgr).format())


_sgr = types.SimpleNamespace(
	bright_red = 91,
	bright_yellow = 93,
	bold = 1,
	dim = 2,
)

_unit_sep = '\037'

class ColoredTracebackException(traceback.TracebackException):
	def __init__(self, *args, sgr=(), **kwargs):
		self._sgr = sgr if sgr else (_sgr.bright_red, )
		super().__init__(*args, **kwargs)

	@staticmethod
	def _make_params_line(text: str, *params: tuple[int]) -> str:
		if text.startswith(_unit_sep):
			return text
		return f'{_unit_sep}{_unit_sep.join(f"{param}" for param in params)}{_unit_sep}{text}'

	def format(self, *args, **kwargs):
		lines = super().format(*args, **kwargs)

		if self.exceptions is None and not self.stack:
			# add back the header even if theres not really a traceback
			lines = itertools.chain(['Traceback (most recent call last):\n'], lines)

		def formatted_lines():
			nonlocal lines

			yield self._make_params_line(next(lines), _sgr.bold)

			if self.exc_type and issubclass(self.exc_type, SyntaxError):
				yield from (self._make_params_line(line, _sgr.bold, _sgr.dim) for line in lines)
				return

			lines = list(lines)
			last_file_line_index = -1

			for i, line in enumerate(lines):
				if re.match(r'^\s*File\s+', line):
					last_file_line_index = i

			for i, line in enumerate(lines):
				if i == last_file_line_index:
					yield self._make_params_line(line, _sgr.bold)
				else:
					yield self._make_params_line(line, _sgr.bold, _sgr.dim)

		for line in formatted_lines():
			params = list(self._sgr)
			prefix = ''
			suffix = ''

			if line.startswith(_unit_sep):
				_, *params_, line = line.split(_unit_sep)
				params += params_

			if params:
				prefix = f'\033[{";".join(f"{param}" for param in params)}m'
				suffix = f'\033[0m'

			yield f'{prefix}{line}{suffix}'

	def format_exception_only(self):
		lines = super().format_exception_only()

		if self.exc_type and issubclass(self.exc_type, SyntaxError):
			if (
				isinstance(self.__notes__, collections.abc.Sequence)
				and not isinstance(self.__notes__, (str, bytes))
			):
				note_lines = -sum(len(str(note).split('\n')) for note in self.__notes__)
			elif self.__notes__ is not None:
				note_lines = -1
			else:
				note_lines = None

			lines = list(lines)

			yield from (self._make_params_line(line, _sgr.bold) for line in lines[:note_lines])

			if note_lines is not None:
				yield from (self._make_params_line(line, _sgr.bold, _sgr.dim) for line in lines[note_lines:])

		else:
			yield self._make_params_line(next(lines), _sgr.bold)
			yield from (self._make_params_line(line, _sgr.bold, _sgr.dim) for line in lines)







class IntConstant(int):
	_constant_lookup_cache = {}

	def __set_name__(self, cls, name):
		self.name = name
		self.full_name = f'{cls.__module__}.{cls.__qualname__}.{name}'

	def __repr__(self):
		if hasattr(self, 'full_name'):
			return f'<{self.full_name}: {super().__repr__()}>'
		else:
			return super().__repr__()

	@classmethod
	def lookup(cls, in_class: type, value: int, *, prefix: str = ''):
		cache = cls._constant_lookup_cache

		for class_ in in_class.mro():
			if class_ not in cache:
				cache[class_] = {}

				for key, val in class_.__dict__.items():
					if isinstance(val, cls):
						if int(val) not in cache[class_]:
							cache[class_][int(val)] = []
						cache[class_][int(val)].append(val)

				if not cache[class_]:
					cache[class_] = None

			if class_constants := cache.get(class_, None):
				if constants_with_value := class_constants.get(value, None):
					if len(constants_with_value) == 1:
						return constants_with_value[0]

					elif prefix:
						for constant in constants_with_value:
							if constant.name.startswith(prefix):
								return constant

		return value


