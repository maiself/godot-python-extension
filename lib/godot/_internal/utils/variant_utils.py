from __future__ import annotations

import itertools

from _godot_internal_core_utils import *
from .general_utils import *

import _gdextension as gde


import godot


_unspecified = object()

_variant_type_name_to_enum_value = {}
_variant_enum_value_to_type_name = {}

def _init_variant_enums():
	if _variant_type_name_to_enum_value:
		return

	enum_values = [godot.Variant.Type(value) for value in range(gde.GDEXTENSION_VARIANT_TYPE_VARIANT_MAX)]

	enum_values.remove(godot.Variant.Type.TYPE_OBJECT)

	for enum_value in enum_values:
		type_ = variant_type_from_enum(enum_value)
		name = type_.__name__

		_variant_type_name_to_enum_value[name] = enum_value
		_variant_enum_value_to_type_name[enum_value] = name

	_variant_type_name_to_enum_value['Object'] = godot.Variant.Type.TYPE_OBJECT
	_variant_enum_value_to_type_name[godot.Variant.Type.TYPE_OBJECT] = 'Object'


def variant_type_enum_to_name(type_enum: 'godot.Variant.Type') -> str:
	_init_variant_enums()
	return _variant_enum_value_to_type_name[godot.Variant.Type(type_enum)]



def variant_type_name_to_enum(type_name: str, default = _unspecified) -> 'godot.Variant.Type':
	_init_variant_enums()
	try:
		return _variant_type_name_to_enum_value[type_name]

	except KeyError:
		if default is _unspecified:
			raise

		return default


def variant_type_name_to_fullname(variant_type_name: str) -> str:
	if variant_type_name.islower():
		return variant_type_name

	return f'godot.{variant_type_name}'


def variant_type_enum_to_fullname(type_enum: 'godot.Variant.Type') -> str:
	_init_variant_enums()
	return variant_type_name_to_fullname(_variant_enum_value_to_type_name[godot.Variant.Type(type_enum)])




def full_type_description(obj_or_type: object | type) -> tuple:
	import _gdextension as gde
	import godot # XXX

	if obj_or_type is None:
		return (godot.Variant.Type.TYPE_NIL, '', None)
		#return (gde.GDEXTENSION_VARIANT_TYPE_NIL, '', None)

	obj = obj_or_type if not isinstance(obj_or_type, type) else None
	type_ = obj_or_type if isinstance(obj_or_type, type) else type(obj)

	variant_type = variant_enum_from_type_inferred(type_)

	if variant_type is None:
		raise TypeError(f'{type_!r} is not a valid variant type')

	if variant_type == godot.Variant.Type.TYPE_ARRAY:
		return (
			godot.Variant.Type.TYPE_ARRAY,
			type_._element_type.__name__ if type_._element_type else '', # XXX: wrong
			None
		)

	#if variant_type != gde.GDEXTENSION_VARIANT_TYPE_OBJECT:
	if variant_type != godot.Variant.Type.TYPE_OBJECT:
		return (godot.Variant.Type(variant_type), '', None)

	def _most_derived_non_script_base(cls: type) -> type: # XXX
		if not isinstance(cls, type) or not issubclass(cls, godot.Object):
			raise TypeError(f'')
		return getattr(cls, '_extension_class', None) or getattr(cls, '_godot_class', godot.Object)

	if obj:
		class_name = obj.get_class()
		script = obj.get_script()

	else:
		from godot._python_extension.python_script import PythonScript # XXX

		class_name = _most_derived_non_script_base(type_).__name__
		script = None

		if script_class := getattr(type_, '_script_class', None):
			for scr in PythonScript.get_all_scripts():
				if scr._class is script_class:
					script = scr
					break

	return (godot.Variant.Type(variant_type), class_name, script)





def get_method_flags(method_info) -> gde.GDExtensionClassMethodFlags:
	flags = 0

	if method_info.get('is_const'):
		flags |= gde.GDEXTENSION_METHOD_FLAG_CONST
	if method_info.get('is_static'):
		flags |= gde.GDEXTENSION_METHOD_FLAG_STATIC
	if method_info.get('is_vararg'):
		flags |= gde.GDEXTENSION_METHOD_FLAG_VARARG

	return gde.GDExtensionClassMethodFlags(flags)



_classes = set()

def _get_api_classes():
	if not _classes:
		from ..api_info import api

		for class_info in api.classes:
			_classes.add(class_info.name)

	return _classes


def parse_type_str_prop_info(type_str: str | None, *, implicit_cast: bool = True) -> gde.GDExtensionPropertyInfo:
	from ..type_info import TypeInfo

	if not type_str:
		return None

	info = TypeInfo.from_api_info_type_string(type_str)

	#print(type_str, repr(info))
	if implicit_cast:
		#print(info.property_info_with_implicit_cast)
		return info.property_info_with_implicit_cast # XXX

	#print(type_str, repr(info))
	return info.property_info


def type_name_from_prop_info(prop_info: gde.GDExtensionPropertyInfo | None) -> str | None:
	if prop_info is None:
		return None

	if prop_info.type == godot.Variant.Type.TYPE_OBJECT:
		if prop_info.python_type is not None:
			return prop_info.python_type
		#class_name = str(prop_info.class_name)
		#if class_name != '':
		#	return class_name

	if prop_info.hint == godot.PropertyHint.PROPERTY_HINT_INT_IS_POINTER:
		return 'object'

	return variant_type_enum_to_fullname(prop_info.type)


_method_infos = {} # XXX

def get_method_info(cls: type, method_name: str) -> gde.GDExtensionClassMethodInfo:
	method_info = None

	for c in cls.mro():
		val = getattr(c, method_name, None)
		if not val:
			continue

		#method_info = getattr(val, '_method_info', None) # XXX

		#if not method_info:
		method_info = _method_infos.get((fullname(c), method_name))

		if not method_info:
			continue

		break

	if not method_info:
		raise RuntimeError(
			f'failed to get method info for \'{fullname(cls)}.{method_name}\'')

	return method_info

def set_method_info(cls: type | str, method_name: str, method_info: gde.GDExtensionClassMethodInfo):
	class_name = fullname(cls) if isinstance(cls, type) else cls
	_method_infos[(class_name, method_name)] = method_info
	



_implicit_casts = {}
_implicit_cast_needs_convert = set()

def _init_implicit_casts():
	if _implicit_casts:
		return

	import enum, typing, collections.abc

	def fullnames(*args):
		return tuple(fullname(arg) for arg in args)

	_implicit_casts.update(
		int = fullnames(enum.Enum, typing.SupportsInt, typing.SupportsIndex),
		float = fullnames(int, typing.SupportsFloat),

		String = fullnames(str, godot.StringName),
		StringName = fullnames(str, godot.String),

		Array = fullnames(collections.abc.Sequence, ),
		Dictionary = fullnames(collections.abc.Mapping, ),

		Callable = fullnames(collections.abc.Callable, ),

		Variant = fullnames(object),

		# XXX: bytes / buffer
		# XXX: bool?
	)

	_implicit_cast_needs_convert.update(set(
		#'int',
		#'float',
		#'String', # XXX: not from string / string name ?
		#'StringName',
	))


def variant_type_get_type_names_implicitly_castable_from(variant_type: str | godot.Variant.Type) -> list[str]:
	_init_implicit_casts()

	if not isinstance(variant_type, str):
		variant_type = variant_type_enum_to_name(variant_type)
	else:
		variant_type = variant_type.removeprefix('godot.')

	return _implicit_casts.get(variant_type, ())


def variant_type_implicitly_castable_from_module_import_names() -> list[str]:
	return ['enum', 'typing', 'collections.abc', 'godot']

def variant_type_implicitly_castable_from_match_pattern(variant_type: str | godot.Variant.Type) -> str:
	if not isinstance(variant_type, str):
		variant_type = variant_type_enum_to_fullname(variant_type)

	if variant_type == 'godot.Variant':
		return 'object()'

	implicit = variant_type_get_type_names_implicitly_castable_from(variant_type)

	if implicit:
		return f'''({' | '.join(f'{type_}()' for type_ in (variant_type, *implicit))})'''

	return f'{variant_type}()'


def variant_type_implicit_cast_needs_convert(variant_type: str | godot.Variant.Type) -> bool:
	_init_implicit_casts()

	if not isinstance(variant_type, str):
		variant_type = variant_type_enum_to_name(variant_type)
	else:
		variant_type = variant_type.removeprefix('godot.')

	return (variant_type in _implicit_cast_needs_convert)




@with_context
def parse_value_str_to_str(value: str | unspecified, type_: str) -> str | unspecified:
	_init_parse_value_namespace()

	if value is unspecified:
		return value


	if value == 'false': return False
	if value == 'true': return True
	if value == 'null': return None

	res = unspecified

	#with print_exceptions_and_continue():

	try:
		res = eval(value, _parse_value_namespace) # XXX
		return value.replace(type(res).__name__, fullname(type(res)))

	except TypeError:
		from ..api_info import api
		var_type = _parse_value_namespace[type_]

		if type_ == 'Transform3D':
			itype = godot.Vector3
		else:
			itype = _parse_value_namespace[api.builtin_classes.get(type_).indexing_return_type]

		import re

		size = int(re.search(r'[0-9]+', itype.__name__).group(0))

		parsed_args = [x.strip() for x in re.fullmatch(r'.+?\((.*)\)', value).group(1).split(',')]
		it = iter(parsed_args)

		args = []

		while grouped_args := tuple(itertools.islice(it, size)):
			args.append(f'{fullname(itype)}({", ".join(grouped_args)})')

		return f'{fullname(var_type)}({", ".join(args)})'





	return


	val = parse_value_str_to_value(value, type_) # XXX

	if isinstance(val, (int, float, bool, str, type(None), list, tuple)):
		return repr(val)

	s = repr(val).removeprefix('<').removesuffix('>').strip() # XXX

	type_name, repr_ = s.split(' ', 1)
	if repr_[0] == '[' and repr_[-1] == ']':
		return f'{type_name}({repr_})'
	if repr_[0] == '(' and repr_[-1] == ')':
		return f'{type_name}{repr_}'

	return f'{repr_}' # XXX


	if value == 'false': return 'False'
	if value == 'true': return 'True'
	if value == 'null': return 'None'
	if '(' in value:
		return 'None'#return 'gde.'+n # XXX
	return value



_parse_value_namespace = {}

def _init_parse_value_namespace():
	if _parse_value_namespace:
		return

	enum_values = [godot.Variant.Type(value) for value in range(gde.GDEXTENSION_VARIANT_TYPE_VARIANT_MAX)]

	enum_values.remove(godot.Variant.Type.TYPE_OBJECT)

	for enum_value in enum_values:
		type_ = variant_type_from_enum(enum_value)
		name = type_.__name__

		if name.islower():
			continue

		_parse_value_namespace[name] = type_

	import math # XXX

	_parse_value_namespace.update(
		inf = math.inf
	)


@with_context
def parse_value_str_to_value(value: str | unspecified, type_: str) -> object | unspecified:
	_init_parse_value_namespace()

	if value is unspecified:
		return value

	if value == 'false': return False
	if value == 'true': return True
	if value == 'null': return None

	res = unspecified

	#with print_exceptions_and_continue():

	try:
		res = eval(value, _parse_value_namespace) # XXX

	except TypeError:
		from ..api_info import api
		var_type = _parse_value_namespace[type_]

		if type_ == 'Transform3D':
			itype = godot.Vector3
		else:
			itype = _parse_value_namespace[api.builtin_classes.get(type_).indexing_return_type]

		import re

		size = int(re.search(r'[0-9]+', itype.__name__).group(0))

		parsed_args = [float(x) for x in re.fullmatch(r'.+?\((.*)\)', value).group(1).split(',')]
		it = iter(parsed_args)

		args = []

		while grouped_args := tuple(itertools.islice(it, size)):
			args.append(itype(*grouped_args))

		res = var_type(*args)



	#if res is unspecified:
	#	res = eval(type_+'()', _parse_value_namespace)

	return res

	if '(' in value:
		return 'None'#return 'gde.'+n # XXX
	return value


