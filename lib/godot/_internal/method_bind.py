import textwrap
import itertools
import functools
import collections.abc
import copy
import contextlib

import _gdextension as gde

import godot

from . import utils
from .utils import doc_utils

from .utils import apply_attrs

from .api_info import api, get_via_path, pretty_string

#from .type_info import TypeInfo


import keyword


# set to `True` to only warn and then continue if a method fails to bind
# set to `False` to fully raise the exception and then quit if a method fails to bind
_method_bind_fail_warn_and_continue = True


if _method_bind_fail_warn_and_continue:
	_configured_warn_and_continue_or_raise = utils.print_exceptions_and_continue
else:
	@contextlib.contextmanager
	def _configured_warn_and_continue_or_raise():
		yield



def keyword_sanitize_identifier(ident: str) -> str:
	return ident + '_' if keyword.iskeyword(ident) else ident


def reformat_type_str(type_str: str) -> str:
	return utils.type_name_from_prop_info(utils.parse_type_str_prop_info(type_str))
	#if type_str == type_info.name:
	#	return type_str
	if type_str == 'String': return 'str'
	if type_str not in ['int', 'bool', 'float', 'str']:
		return repr(type_str)
	return type_str


class classproperty:
	def __init__(self, fget=None, fset=None, fdel=None, doc=None):
		self.fget = fget
		self.fset = fset
		self.fdel = fdel
		if doc is None and fget is not None:
			doc = fget.__doc__
		self.__doc__ = doc

	def __get__(self, instance, ownerclass):
		return self.fget(ownerclass)


class ArgumentInfo:
	def __init__(self, api_argument_info):
		self.arg_info = api_argument_info

		self.name = keyword_sanitize_identifier(self.arg_info.name)
		self.type = utils.type_name_from_prop_info(utils.parse_type_str_prop_info((self.arg_info.type)))
		self.type_no_implicit: str = utils.type_name_from_prop_info(utils.parse_type_str_prop_info(self.arg_info.type, implicit_cast=False))

		self.default_value = utils.parse_value_str_to_str(self.arg_info.get('default_value', utils.unspecified), type_=self.arg_info.type)

	@property
	def doc(self) -> str:
		return ' = '.join([
			': '.join([f'{self.name}', *[f'{self.type}'] * (self.type is not utils.unspecified)]),
			*[f'{self.default_value}'] * (self.default_value is not utils.unspecified),
		])

	@property
	def match_pattern(self) -> str:
		return utils.variant_type_implicitly_castable_from_match_pattern(self.type_no_implicit)

	@classmethod
	def _create_from_name_only(cls, name):
		info = ArgumentInfo.__new__(cls)
		info.arg_info = None
		info.name = name
		info.type = utils.unspecified
		info.default_value = utils.unspecified
		return info

	@classproperty
	def self_argument(cls):
		return cls._create_from_name_only('self')

	@classproperty
	def args_argument(cls):
		return cls._create_from_name_only('*args')

	def cast(self, arg_name: str) -> str:
		if not utils.variant_type_implicit_cast_needs_convert(self.type_no_implicit):
			return arg_name

		return f'{self.type_no_implicit}({arg_name})'


@utils.with_context
def bind_method(cls, type_info, method_info, with_docs=True):
	is_utility = (type_info is None) # XXX

	#is_variant_type = not issubclass(cls, gde.Object)
	is_variant_type = not is_utility and (utils.variant_type_name_to_enum(type_info.name, None)
		not in (None, godot.Variant.Type.TYPE_OBJECT))

	if is_utility:
		get_method = gde.variant_get_ptr_utility_function
	else:
		get_method = gde.variant_get_ptr_builtin_method if is_variant_type else gde.classdb_get_method_bind

	if is_variant_type or is_utility:
		implicit_cast = True

		if not is_utility and type_info.name in ['String', 'StringName']:
			if method_info.get('return_type') in ['String', 'StringName']:
				implicit_cast = False

		return_value_info = utils.parse_type_str_prop_info(method_info.get('return_type'),
			implicit_cast=implicit_cast)

	else:
		if method_info.get('return_value'):
			return_value_info = utils.parse_type_str_prop_info(method_info.get('return_value').type)

		else:
			return_value_info = apply_attrs(gde.GDExtensionPropertyInfo(),
				type = gde.GDEXTENSION_VARIANT_TYPE_NIL,
				class_name = '',
			) # XXX optional? #  if method_info.get('return_type') else None,

	class_method_info = apply_attrs(gde.GDExtensionClassMethodInfo(),
			name = method_info.name,
			method_flags = utils.get_method_flags(method_info),
			arguments_info = [
				utils.parse_type_str_prop_info(arg_info.type)
				#apply_attrs(copy.copy(utils.parse_type_str_prop_info(arg_info.type)),
				#	name = arg_info.name
				#)
				for arg_info in method_info.get('arguments', [])
			],
			return_value_info = return_value_info,
		)

	method = None

	if 'hash' in method_info:
		if is_utility:
			method = get_method(
				class_method_info,
				method_info.hash
			)
		else:
			method = get_method(
				TypeInfo.from_api_info_type_string(type_info.name).variant_type if is_variant_type else type_info.name,
				class_method_info,
				method_info.hash
			)

	else:
		# XXX: virtual method?
		#print(f'\033[93;3m{type_info.name}.{method_info.name} has no hash\033[0m')
		method = lambda *args, **kwargs: None # XXX return default value

	if not method:
		with _configured_warn_and_continue_or_raise():
			raise AttributeError(
				f'''invalid {
					'utility function' if is_utility
					else 'variant method' if is_variant_type
					else 'class method'
				}: {
					method_info.name if is_utility
					else '.'.join((type_info.name, method_info.name))
				}'''
			)

	# we now have `class_method_info: gde.GDExtensionClassMethodInfo` and `method` callable

	if is_utility:
		method_impl_name = f'_{method_info.name}_impl'
	else:
		method_impl_name = f'_{type_info.name}_{method_info.name}_impl'

	arg_infos = [ArgumentInfo(arg_info) for arg_info in method_info.get('arguments', [])]

	if with_docs or any(arg_info.default_value is not utils.unspecified for arg_info in arg_infos):
		if not method_info.get('is_static') and not is_utility:
			arg_infos.insert(0, ArgumentInfo.self_argument)

		if method_info.get('is_vararg'): # XXX
			arg_infos.append(ArgumentInfo.args_argument)

		arg_names = [arg_info.name for arg_info in arg_infos]
		arg_docs = [arg_info.doc for arg_info in arg_infos]

		ret_type_name = utils.type_name_from_prop_info(return_value_info)
		ret_doc = f' -> {ret_type_name}' if ret_type_name else ''

		def method_not_implemented(func):
			func._not_implemented = True # XXX
			return func

		decorators = []

		if 'hash' not in method_info: # XXX
			decorators.append('@method_not_implemented')

		if method_info.get('is_static'):
			decorators.append('@staticmethod')

		method_code = textwrap.dedent(f'''
				def {method_info.name}({', '.join(arg_docs)}){ret_doc}:
					return {method_impl_name}({', '.join(arg_names)})
			''').lstrip()

		method_code = '\n'.join([*decorators, method_code, ''])

		namespace = dict(
			godot = godot,
			method_not_implemented = method_not_implemented,
			**{
				method_impl_name: method
			}
		)

		if is_utility:
			full_method_name = f'{method_info.name}'
		else:
			full_method_name = f'{type_info.name}.{method_info.name}'

		with utils.exception_note(
			lambda: f'While binding method \'{full_method_name}\' with code:\n' + method_code
		):
			exec(method_code, namespace)

		method = namespace.get(method_info.name)

		if is_utility:
			method.__module__ = 'godot'
			method.__name__ = method_info.name
			method.__qualname__ = method_info.name

		else:
			method.__module__ = cls.__module__
			method.__name__ = method_info.name
			method.__qualname__ = f'{cls.__qualname__}.{method_info.name}'

			#method.__annotations__ = {'name': str}
			#method.__doc__ = f'godot {type_info.name} method'
			#method.__text_signature__ = f'''{method_info.name}({', '.join(arg_docs)}){ret_doc}'''
			#method.__signature__ = None

		if docs := method_info.get('documentation'):
			method.__doc__ = doc_utils.reformat_doc_bbcode(docs)

	setattr(cls, method_info.name, method)

	if is_utility:
		utils.set_method_info(f'godot', method_info.name, class_method_info)
	else:
		utils.set_method_info(f'godot.{type_info.name}', method_info.name, class_method_info)


@utils.with_context
def bind_variant_constructors(cls, type_info):
	global TypeInfo
	from .type_info import TypeInfo
	#print(f'constructors for {cls.__name__}:', *type_info.constructors, sep='\n\t')

	constructors = []
	constructor_cases = []
	case_doc_patterns = []

	def constructor_name(index) -> str:
		return f'_{type_info.name}_constructor_{index}'

	for constructor_info in type_info.constructors:
		assert(constructor_info.index == len(constructors))

		constructors.append(gde.variant_get_ptr_constructor(
			TypeInfo.from_api_info_type_string(type_info.name).variant_type,
			apply_attrs(gde.GDExtensionClassMethodInfo(),
				method_flags = utils.get_method_flags(constructor_info),
				arguments_info = [
					utils.parse_type_str_prop_info(arg_info.type)
					#apply_attrs(copy.copy(utils.parse_type_str_prop_info(arg_info.type)),
					#	name = arg_info.name,
					#)
					for arg_info in constructor_info.get('arguments', [])
				],
			),
			constructor_info.index
		))

		arg_casts = []

		arg_infos = [ArgumentInfo(arg_info) for arg_info in constructor_info.get('arguments', [])]

		case_match_pattern = f'''({
				', '.join(arg_info.match_pattern for arg_info in arg_infos)
			}{', ' if len(arg_infos) == 1 else ''})'''

		cast_arg_casts = ', '.join(arg
			for arg in ['self'] + [arg_infos[i].cast(f'args[{i}]') for i in range(len(arg_infos))])

		constructor_cases.append(textwrap.dedent(f'''
				case {case_match_pattern}:
					{constructor_name(constructor_info.index)}({cast_arg_casts})
			''').strip())

		case_doc_patterns.append(f'''({', '.join(arg_info.type for arg_info in arg_infos)})''') # XXX: builtin?

		if constructors[-1] is None:
			with _configured_warn_and_continue_or_raise():
				raise AttributeError(
					f'''invalid variant constructor: {type_info.name}{
						case_doc_patterns[-1].replace('godot.', '')} (index {constructor_info.index})'''
				)

	namespace = {
		constructor_name(index): constructor for index, constructor in enumerate(constructors)
	}

	if cls.__name__ in ['String', 'StringName']:
		#print(f'\033[91;1;2mskipping constructors for {cls.__name__}\033[0m')
		return # XXX

		#namespace['__builtin_init__'] = cls.__init__

		#constructor_cases.append(textwrap.dedent(f'''
		#		case _:
		#			__builtin_init__(self, *args)
		#	''').strip())

	else:
		error_msg = textwrap.dedent(f'''
			no matching constructor for {cls.__qualname__}
			called with:
			  {{args!r}}
			expected one of:
			  {"""
			  """.join(case_doc_patterns)}
		''')

		constructor_cases.append(textwrap.dedent(f'''
			case _:
				msg = textwrap.dedent(f"""{"""
					""".join(error_msg.splitlines())}
				""").strip()

				raise TypeError(msg)
			''').strip())

	constructor_code = textwrap.dedent(f'''
		# constructor for {cls.__name__}

		import collections.abc # XXX
		import enum # XXX
		import typing # XXX

		import textwrap # XXX

		import godot

		def __init__(self, *args):
			match args:
				{"""
				""".join(itertools.chain(*(case.splitlines() for case in constructor_cases)))}
	''')


	with utils.exception_note(lambda: f'Constructor code:\n\n{constructor_code}'):
		exec(constructor_code, namespace)

	method = namespace.get('__init__')

	method.__module__ = cls.__module__
	method.__name__ = '__init__'
	method.__qualname__ = f'{cls.__qualname__}.__init__'

	#method.__annotations__ = {'name': str}
	#method.__doc__ = f'godot {type_info.name} method'
	#method.__text_signature__ = f'''{method_info.name}({', '.join(arg_docs)}){ret_doc}'''
	#method.__signature__ = None

	#print(constructor_code)

	setattr(cls, '__init__', method)




_op_mapping = {}
_op_mapping_inv = {}

def _init_op_mapping():
	if _op_mapping:
		return

	_op_mapping.update(
		__eq__ = ('==', godot.Variant.Operator.OP_EQUAL),
		__nq__ = ('!=', godot.Variant.Operator.OP_NOT_EQUAL),
		__lt__ = ('<', godot.Variant.Operator.OP_LESS),
		__le__ = ('<=', godot.Variant.Operator.OP_LESS_EQUAL),
		__gt__ = ('>', godot.Variant.Operator.OP_GREATER),
		__ge__ = ('>=', godot.Variant.Operator.OP_GREATER_EQUAL),

		__add__ = ('+', godot.Variant.Operator.OP_ADD),
		__sub__ = ('-', godot.Variant.Operator.OP_SUBTRACT),
		__mul__ = ('*', godot.Variant.Operator.OP_MULTIPLY),
		__truediv__ = ('/', godot.Variant.Operator.OP_DIVIDE),

		__neg__ = ('unary-', godot.Variant.Operator.OP_NEGATE), # unary
		__pos__ = ('unary+', godot.Variant.Operator.OP_POSITIVE), # unary

		__mod__ = ('%', godot.Variant.Operator.OP_MODULE),
		__pow__ = ('**', godot.Variant.Operator.OP_POWER),
		__lshift__ = ('<<', godot.Variant.Operator.OP_SHIFT_LEFT),
		__rshift__ = ('>>', godot.Variant.Operator.OP_SHIFT_RIGHT),
		__and__ = ('&', godot.Variant.Operator.OP_BIT_AND),
		__or__ = ('|', godot.Variant.Operator.OP_BIT_OR),
		__xor__ = ('^', godot.Variant.Operator.OP_BIT_XOR),

		__inv__ = ('~', godot.Variant.Operator.OP_BIT_NEGATE), # unary # XXX
		#____ = ('and', godot.Variant.Operator.OP_AND),
		#____ = ('or', godot.Variant.Operator.OP_OR),
		#____ = ('xor', godot.Variant.Operator.OP_XOR),
		__not__ = ('not', godot.Variant.Operator.OP_NOT), # unary
		__contains__ = ('in', godot.Variant.Operator.OP_IN), # reversed
	)

	_op_mapping_inv.update({
		op: (method, enum) for method, (op, enum) in _op_mapping.items()
	})


def _bind_op(cls, type_info, op_info, method_name, op_enum, reverse=False):
	reversed_args = (method_name in ('__contains__', )) or reverse
	is_unary = method_name in ('__neg__', '__pos__', '__inv__', '__not__')

	if is_unary:
		op_eval = gde.variant_get_ptr_operator_evaluator(
				op_enum,
				TypeInfo.from_api_info_type_string(type_info.name).variant_type,
				godot.Variant.Type.TYPE_NIL,
				TypeInfo.from_api_info_type_string(op_info.return_type).variant_type,
			)

		if not op_eval:
			with _configured_warn_and_continue_or_raise():
				raise AttributeError(
					f'''invalid operator evaluator: {type_info.name}.{method_name}() -> {op_info.return_type}'''
				)

		op = lambda self: op_eval(self)

		utils.swap_members(cls, method_name, op)
		return

	op_eval = gde.variant_get_ptr_operator_evaluator(
			op_enum,
			TypeInfo.from_api_info_type_string(type_info.name).variant_type,
			TypeInfo.from_api_info_type_string(op_info.right_type).variant_type,
			TypeInfo.from_api_info_type_string(op_info.return_type).variant_type,
		)

	left_type = TypeInfo.from_api_info_type_string(type_info.name).type_object
	right_type = TypeInfo.from_api_info_type_string(op_info.right_type).type_object

	if reversed_args:
		left_type, right_type = right_type, left_type

	if not op_eval:
		with _configured_warn_and_continue_or_raise():
			raise AttributeError(
				f'''invalid operator evaluator: {left_type.__name__}.{method_name}({right_type.__name__}) -> {op_info.return_type}'''
			)

	def register(method_name, op):
		op.__name__ = method_name
		op.__qualname__ = f'{left_type.__name__}.{op.__name__}'
		op.__module__ = 'godot'

		if (not hasattr(left_type, method_name)
			or not hasattr(getattr(left_type, method_name), 'register')
		):
			default_op = functools.singledispatchmethod(lambda self, other: NotImplemented)
			utils.swap_members(left_type, method_name, default_op)

			if hasattr(op, '_is_non_const_method'):
				default_op._is_non_const_method = op._is_non_const_method # XXX

		getattr(left_type, method_name).register(right_type, op)

		#print(cls.__name__, method_name, left_type.__name__, right_type.__name__)

		if right_type in (godot.String, godot.StringName):
			getattr(left_type, method_name).register(str, op)

		elif right_type is godot.Array:
			getattr(left_type, method_name).register(collections.abc.Sequence, op)

		elif right_type is godot.Dictionary:
			getattr(left_type, method_name).register(collections.abc.Mapping, op)

		elif right_type is godot.Callable:
			getattr(left_type, method_name).register(collections.abc.Callable, op)

		elif right_type is godot.Variant:
			getattr(left_type, method_name).register(object, op) # XXX: ?

		# else # XXX: ?



	if not reversed_args:
		op = lambda self, other: op_eval(self, other)
	else:
		op = lambda self, other: op_eval(other, self)

	register(method_name, op)

	if reverse:
		return

	return_type = TypeInfo.from_api_info_type_string(op_info.return_type).type_object

	if return_type is left_type:
		method_name = method_name.replace('__', '__i', 1)

		_iop_type = left_type

		def iop(self, other):
			_iop_type.__init__(self, op_eval(self, other)) # XXX: __init__
			return self

		iop._is_non_const_method = True # XXX

		register(method_name, iop)




@utils.with_context
def bind_variant_operators(cls, type_info):
	_init_op_mapping()

	if indexing_return_type := type_info.get('indexing_return_type'):
		if type_info.get('is_keyed'):
			getter = gde.variant_get_ptr_keyed_getter(
				TypeInfo.from_api_info_type_string(type_info.name).variant_type,
				godot.Variant.Type.TYPE_NIL,
				TypeInfo.from_api_info_type_string(indexing_return_type).variant_type
			)

			setter = gde.variant_get_ptr_keyed_setter(
				TypeInfo.from_api_info_type_string(type_info.name).variant_type,
				godot.Variant.Type.TYPE_NIL,
				TypeInfo.from_api_info_type_string(indexing_return_type).variant_type
			)

			__getitem__ = getter
			__setitem__ = setter

		else:
			getter = gde.variant_get_ptr_indexed_getter(
				TypeInfo.from_api_info_type_string(type_info.name).variant_type,
				TypeInfo.from_api_info_type_string(indexing_return_type).variant_type)

			setter = gde.variant_get_ptr_indexed_setter(
				TypeInfo.from_api_info_type_string(type_info.name).variant_type,
				TypeInfo.from_api_info_type_string(indexing_return_type).variant_type)

			if type_info.methods.get('size'):
				def __getitem__(self, index):
					if index < 0:
						index = self.size() - index
						if index < 0:
							raise IndexError
					if index >= self.size():
						raise IndexError
					return getter(self, index)

				def __setitem__(self, index, value):
					if index < 0:
						index = self.size() - index
						if index < 0:
							raise IndexError
					if index >= self.size():
						raise IndexError
					setter(self, index, value)

			else:
				__getitem__ = getter
				__setitem__ = setter

		if not getter:
			with _configured_warn_and_continue_or_raise():
				raise AttributeError(
					f'''invalid keyed getter: {type_info.name}[Variant] -> {indexing_return_type}'''
					if type_info.get('is_keyed') else
					f'''invalid indexed getter: {type_info.name}[int] -> {indexing_return_type}'''
				)

		if not setter:
			with _configured_warn_and_continue_or_raise():
				raise AttributeError(
					f'''invalid keyed setter: {type_info.name}[Variant] = {indexing_return_type}'''
					if type_info.get('is_keyed') else
					f'''invalid indexed setter: {type_info.name}[int] = {indexing_return_type}'''
				)

		if indexing_return_type in ['String', 'StringName']:
			__getitem__inner = __getitem__
			__getitem__ = lambda self, key: str(__getitem__inner(self, key)) # XXX

		utils.swap_members(cls, '__getitem__', __getitem__)
		utils.swap_members(cls, '__setitem__', __setitem__)

		if hasattr(cls, 'size'):
			utils.swap_members(cls, '__len__', cls.size)

	#if type_info.name == 'PackedStringArray':
	#	print(pretty_string(type_info))



	for op_info in type_info.get('operators', []):
		if op_info.name in ('and', 'or', 'xor'):
			continue

		method_name, op_enum = _op_mapping_inv[op_info.name]

		with utils.exception_note(lambda: f'While binding operator {cls.__name__}.{method_name}'):
			_bind_op(cls, type_info, op_info, method_name, op_enum)



	reverse_ops = []

	for type_ in (api.builtin_classes.int, api.builtin_classes.float):
		for op in type_.operators:
			if op.get('right_type') in (None, 'bool', 'int', 'float', 'Variant'):
				continue

			if op.return_type in ('bool', ):
				continue

			reverse_ops.append((type_, op))


	for op_type, op_info in reverse_ops:
		if op_info.right_type == type_info.name:
			method_name, op_enum = _op_mapping_inv[op_info.name]
			method_name = method_name.replace('__', '__r', 1)

			#print(type_info.name, op_type.name, method_name)

			_bind_op(cls, op_type, op_info, method_name, op_enum, reverse=True)


