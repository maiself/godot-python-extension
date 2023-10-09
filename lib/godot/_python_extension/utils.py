import types
import re
import inspect
import functools
import textwrap

from godot._internal.utils import * # XXX



def godot_path_to_python_module_name(path: str) -> str:
	return path.removeprefix('res://').removesuffix('.py').replace('/', '.') # XXX

def python_module_name_to_godot_path(mod_name: str) -> str:
	return mod_name.replace('.', '/').join(('res://', '.py')) # XXX


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

			if isinstance(cls, type) and isinstance(args[0], cls):
				self_arg = f'\033[34m{fa(args[0])}\033[35m'
				a = (self_arg, *(fa(arg) for arg in args[1:]))
			else:
				a = (fa(arg) for arg in args)

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


def format_func(doc, for_template = False):
	try:
		try:
			m = types.SimpleNamespace(**re.fullmatch(
				r'(?P<name>[\w.:<>]+)\((?P<args>[^\)]*?)\) -> (?P<ret>[\w.:<>]+)\s*',
				doc).groupdict())
		except AttributeError:
			return ''

		name = m.name
		args = [types.SimpleNamespace(**re.fullmatch(r'\s*((?P<name>\w+):\s*)?(?P<type>[\w.:<>]+)\s*', arg).groupdict()) for arg in m.args.split(',')]
		ret = m.ret

		def f(s):
			s = re.sub(r'TypedArray<([\w.:]+)>', r'Array[\1]', s.replace('::', '.'))

			#if True:
			#	s = s.replace('godot.', '')

			d = {
				'capsule': 'object',
				'Dictionary': 'dict',
				'StringName': 'str',
				'String': 'str',
				'Array': 'list',
			}

			d2 = [
				'Variant',
				'Object',
				'Error',
				'Script',
			]

			for a, b in d.items():
				if s.startswith(a):
					s = s.replace(a, b)
				elif s.startswith('godot.'+a):
					s = s.replace('godot.'+a, b)

				if s in d2:
					s = 'godot.'+s

			if '[' in s:
				a_, b_ = s.split('[')
				b_ = b_.removesuffix(']')

				for a, b in d.items():
					if b_.startswith(a):
						b_ = b_.replace(a, b)
					elif b_.startswith('godot.'+a):
						b_ = b_.replace('godot.'+a, b)

					if b_ in d2:
						b_ = 'godot.'+s

				s = f'{a_}[{b_}]'

			s = s.replace('PackedStringArray', 'list[str]')

			#if True:
			#	s = s.replace('godot.', '')

			return s

		args_ = [f'{arg.name}: {f(arg.type)}' for arg in args]
		ret = f(ret)

		if not for_template:
			prefix = args[0].name + '.'
			args_ = args_[1:]

			return f'{prefix}{name}({", ".join(args_)}) -> {ret}'


		return f'''
	def {name}({", ".join(("self", *args_[1:]))}) -> {ret}:
		raise NotImplementedError
'''

	except Exception:
		print(doc)
		raise


def dont_log_calls(f):
	f._dont_log_calls = True
	return f


def log_method_calls(cls):
	for name, obj in vars(cls).items():
		if not isinstance(obj, (types.FunctionType, types.MethodType, classmethod, staticmethod, godot.exposition.method)):
			continue

		if getattr(obj, '_dont_log_calls', False):
			continue

		#continue # XXX

		#try:
		#	obj._format = format_func(getattr(cls.__mro__[1], name).__doc__)
		#except Exception:
		#	continue
		#print(cls.__name__+'.'+name, obj._format)
		#print(cls.__name__+'.'+name, getattr(cls.__mro__[1], name).__doc__)
		#print(getattr(cls.__mro__[1], name))

		with exception_note(f'while decorating {obj} for logging'):
			if hasattr(obj, '__wrapped__'):
				try:
					functools.update_wrapper(obj, log_calls(obj.__wrapped__, cls))
				except AttributeError:
					obj = type(obj)(log_calls(obj.__wrapped__, cls))
				#obj.__wrapped__ = log_calls(obj.__wrapped__, cls)

			else:
				setattr(cls, name, log_calls(obj, cls))

	return cls


