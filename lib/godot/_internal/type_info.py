from __future__ import annotations

import sys
import inspect
import enum
import dataclasses
import functools
import copy
import abc
import types
import typing
import builtins

from .utils.variant_utils import *
from .utils.general_utils import *

import _gdextension as gde

from . import utils

import godot

_classes = set()
_enums = set()


def _get_api_classes():
	if not _classes:
		from .api_info import api

		for class_info in api.classes:
			_classes.add(class_info.name)

	return _classes


def _get_api_enums():
	if not _enums:
		from .api_info import api

		for info in api.global_enums:
			_enums.add(info.name)

	return _enums



#@log_calls
def _resolved_annotation(annotation, *, context) -> type:
	if annotation is None:
		return None

	if annotation == inspect.Signature.empty:
		return unspecified

	if isinstance(annotation, str):
		if len(annotation) >= 3 and (annotation[0], annotation[-1]) in (("'", "'"), ('"', '"')):
			annotation = annotation[1:-1]

		return resolve_name(annotation, context=context)

	return annotation

	#try:
	#except AttributeError:
	#	return None # XXX


#@log_calls
def _get_resolved_annotation(cls, name) -> type:
	annotation = cls.__dict__.get('__annotations__', {}).get(name, None)

	if annotation is None and isinstance(getattr(cls, name), property):
		annotation = getattr(cls, name).fget.__annotations__.get('return', None)

	if annotation is None:
		return None

	if isinstance(annotation, type):
		return annotation

	module = sys.modules[cls.__module__]

	return resolve_name(annotation, context=module)


@functools.cache
def _get_type_object_by_registered_name(name: str) -> type: # XXX XXX
	if name in ('bool', 'int', 'float'):
		return getattr(builtins, name)

	if type_ := variant_type_name_to_enum(name, None):
		return getattr(godot, name)

	if name in _get_api_classes():
		return getattr(godot, name)

	if name in _get_api_enums():
		return getattr(godot, name)

	from . import exposition

	if name in exposition._exposed_classes:
		return exposition._exposed_classes[name].class_ # XXX

	# XXX script classes?

	if '.' in name and name.split('.')[0] in _get_api_classes(): # XXX
		return resolve_name(f'godot.{name}')

	if '.' in name and name.split('.')[0] in exposition._exposed_classes: # XXX
		return getattr(exposition._exposed_classes[name.split('.')[0]].class_, name.split('.')[1]) # XXX

	raise TypeError(f'unknown type {name!r}')





class TypeInfo(abc.ABC):
	__subclasses = []

	def __init_subclass__(cls, *,
			variant_type: godot.Variant.Type = unspecified,
			type_object: type = unspecified,
			**kwargs):
		super().__init_subclass__(**kwargs)

		TypeInfo.__subclasses.append(cls)

		if variant_type is not unspecified:
			#utils.class_set_attr(cls, 'variant_type', cls.variant_type.getter(lambda self: variant_type))
			utils.class_set_attr(cls, 'variant_type', variant_type)

		if type_object is not unspecified:
			utils.class_set_attr(cls, 'type_object', cls.type_object.getter(lambda self: type_object))

	@classmethod
	@functools.cache
	@abc.abstractmethod
	def from_type(cls, type_object: type) -> TypeInfo:
		if type_object is unspecified: # XXX
			type_object = godot.Variant

		elif type_object is None: # XXX
			type_object = types.NoneType

		for subclass in reversed(cls.__subclasses):
			try:
				return subclass.from_type(type_object)
			except TypeError:
				pass

		raise TypeError(f'unable to create {cls.__name__} from {type_object!r}')

	@classmethod
	@abc.abstractmethod
	def from_property_info(cls, prop_info: gde.GDExtensionPropertyInfo) -> TypeInfo:
		for subclass in reversed(cls.__subclasses):
			if (isinstance(subclass.variant_type, godot.Variant.Type)
					and subclass.variant_type != prop_info.type
			):
				continue

			try:
				return subclass.from_property_info(prop_info)
			except ValueError:
				pass

		raise ValueError(f'unable to create {cls.__name__} from property info {prop_info!r}')

	@classmethod
	@functools.cache
	@abc.abstractmethod
	def from_api_info_type_string(cls, type_str: str) -> TypeInfo:
		if type_str is None: # XXX
			return None

		for subclass in reversed(cls.__subclasses):
			try:
				return subclass.from_api_info_type_string(type_str)
			except ValueError:
				pass

		raise ValueError(f'unable to create {cls.__name__} from api type string {type_str!r}')

	@classmethod
	@functools.cache
	def from_annotation(cls, annotation, *, context) -> TypeInfo:
		return cls.from_type(_resolved_annotation(annotation, context=context))

	@classmethod
	def from_resolved_annotation(cls, cls_, annotation) -> TypeInfo: # XXX: ?
		return cls.from_type(_get_resolved_annotation(cls_, annotation))

	@abc.abstractmethod
	def __str__(self) -> str:
		pass

	def __repr__(self) -> str:
		return f'<{type(self).__name__} for {str(self)!r}>'

	@property
	@abc.abstractmethod
	def variant_type(self) -> godot.Variant.Type:
		pass

	@property
	@abc.abstractmethod
	def type_object(self) -> type:
		pass

	@property
	def implicit_cast_type_object(self) -> type | None:
		return None

	'''@property
	def implicit_cast_type_info(self) -> TypeInfo | None:
		if (type_object := self.implicit_cast_type_object) is not None:
			return TypeInfo.from_type(type_object)
		return None'''

	@functools.cached_property
	@abc.abstractmethod
	def property_info_dict(self) -> dict:
		return dict(
			type = self.variant_type,
			name = '',
			class_name = '',
			hint = godot.PropertyHint.PROPERTY_HINT_NONE,
			hint_string = '',
			usage = godot.PropertyUsageFlags.PROPERTY_USAGE_DEFAULT
		)

	@functools.cached_property
	def property_info(self) -> gde.GDExtensionPropertyInfo:
		return apply_attrs(gde.GDExtensionPropertyInfo.from_dict(self.property_info_dict),
			python_type = None, # XXX
		)

	@functools.cached_property
	def property_info_with_implicit_cast(self) -> gde.GDExtensionPropertyInfo:
		return apply_attrs(copy.copy(self.property_info),
			python_type = self.implicit_cast_type_object,
		)

	@functools.cached_property
	def doc_type_string(self) -> str:
		return str(self)


class VoidTypeInfo(TypeInfo, variant_type = godot.Variant.Type.TYPE_NIL, type_object = types.NoneType):
	def __str__(self) -> str:
		return 'void'

	@classmethod
	def from_type(cls, type_object: type) -> TypeInfo:
		if not issubclass(type_object, types.NoneType):
			raise TypeError

		return cls()

	@classmethod
	def from_property_info(cls, prop_info: gde.GDExtensionPropertyInfo) -> TypeInfo:
		if prop_info.type != cls.variant_type:
			raise ValueError

		return cls()

	@classmethod
	def from_api_info_type_string(cls, type_str: str) -> TypeInfo:
		if type_str != 'void':
			raise ValueError

		return cls()

	@functools.cached_property
	def property_info_dict(self) -> dict:
		return super().property_info_dict


class VariantTypeInfo(TypeInfo): # XXX: rename
	def __init__(self, *, variant_type: godot.Variant.Type):
		super().__init__()

		self._variant_type = variant_type

	def __str__(self) -> str:
		return variant_type_enum_to_name(self._variant_type)

	@classmethod
	@functools.cache
	def from_type(cls, type_object: type) -> TypeInfo:
		variant_type = variant_enum_from_type_inferred(type_object)

		if variant_type is None:
			raise TypeError(f'{type_object!r} is not a valid variant type')

		return cls(variant_type = variant_type)

	@classmethod
	def from_property_info(cls, prop_info: gde.GDExtensionPropertyInfo) -> TypeInfo:
		return cls(variant_type = prop_info.type)

	@classmethod
	@functools.cache
	def from_api_info_type_string(cls, type_str: str) -> TypeInfo:
		if type_ := variant_type_name_to_enum(type_str, None):
			return cls(variant_type = type_)

		raise ValueError(f'{type_str!r} is not a valid variant type')

	@functools.cached_property
	def variant_type(self) -> godot.Variant.Type:
		return self._variant_type

	@functools.cached_property
	def type_object(self) -> type:
		return variant_type_from_enum(self._variant_type)

	@functools.cached_property
	def implicit_cast_type_object(self) -> type | None:
		if self._variant_type in (godot.Variant.Type.TYPE_STRING, godot.Variant.Type.TYPE_STRING_NAME):
			return str

		return None

	@functools.cached_property
	def property_info_dict(self) -> dict:
		if self._variant_type == godot.Variant.Type.TYPE_NIL:
			return {**super().property_info_dict, **dict(
				usage = godot.PropertyUsageFlags.PROPERTY_USAGE_NIL_IS_VARIANT,
			)}
		else:
			return super().property_info_dict


class EnumTypeInfo(TypeInfo, variant_type = godot.Variant.Type.TYPE_INT):
	class_name: str

	def __init__(self, *, class_name: str):
		super().__init__()

		self.class_name = class_name

	def __str__(self) -> str:
		return self.class_name

	@classmethod
	@functools.cache
	def from_type(cls, type_object: type) -> TypeInfo:
		if not issubclass(type_object, enum.Enum):
			raise TypeError

		class_name = type_object.__qualname__ # XXX: use exposed name
		return cls(class_name = class_name)

	@classmethod
	def from_property_info(cls, prop_info: gde.GDExtensionPropertyInfo) -> TypeInfo:
		if (prop_info.type != cls.variant_type
			or not (prop_info.usage & godot.PropertyUsageFlags.PROPERTY_USAGE_CLASS_IS_ENUM)
		):
			raise ValueError

		return cls(class_name = prop_info.class_name)

	@classmethod
	@functools.cache
	def from_api_info_type_string(cls, type_str: str) -> TypeInfo:
		if not type_str.startswith('enum::'):
			raise ValueError

		return cls(class_name = type_str.removeprefix('enum::'))

	@functools.cached_property
	def type_object(self) -> type:
		return _get_type_object_by_registered_name(self.class_name)

	@functools.cached_property
	def implicit_cast_type_object(self) -> type | None:
		return self.type_object

	@functools.cached_property
	def property_info_dict(self) -> dict:
		return {**super().property_info_dict, **dict(
			class_name = self.class_name,
			usage = godot.PropertyUsageFlags.PROPERTY_USAGE_CLASS_IS_ENUM,
		)}


class BitfieldTypeInfo(EnumTypeInfo):
	@classmethod
	@functools.cache
	def from_type(cls, type_object: type) -> TypeInfo:
		if not issubclass(type_object, enum.Flag):
			raise TypeError

		class_name = type_object.__qualname__ # XXX: use exposed name
		return cls(class_name = class_name)

	@classmethod
	def from_property_info(cls, prop_info: gde.GDExtensionPropertyInfo) -> TypeInfo:
		if (prop_info.type != cls.variant_type
			or not (prop_info.usage & godot.PropertyUsageFlags.PROPERTY_USAGE_CLASS_IS_BITFIELD)
		):
			raise ValueError

		return cls(class_name = prop_info.class_name)

	@classmethod
	@functools.cache
	def from_api_info_type_string(cls, type_str: str) -> TypeInfo:
		if not type_str.startswith('bitfield::'):
			raise ValueError

		return cls(class_name = type_str.removeprefix('bitfield::'))

	@functools.cached_property
	def property_info_dict(self) -> dict:
		return {**super().property_info_dict, **dict(
			usage = godot.PropertyUsageFlags.PROPERTY_USAGE_CLASS_IS_BITFIELD,
		)}


class ArrayTypeInfo(TypeInfo, variant_type = godot.Variant.Type.TYPE_ARRAY):
	element_type_info: TypeInfo

	def __init__(self, *, element_type_info: TypeInfo):
		super().__init__()

		self.element_type_info = element_type_info

	def __str__(self) -> str:
		return f'Array[{self.element_type_info}]'

	@classmethod
	@functools.cache
	def from_type(cls, type_object: type) -> TypeInfo:
		if not issubclass(type_object, godot.Array):
			raise TypeError

		element_type = type_object._element_type # XXX

		if element_type is None:
			element_type = types.NoneType # XXX

		return cls(element_type_info = TypeInfo.from_type(element_type))

	@classmethod
	def from_property_info(cls, prop_info: gde.GDExtensionPropertyInfo) -> TypeInfo:
		if prop_info.type != cls.variant_type:
			raise ValueError

		if prop_info.hint != godot.PropertyHint.PROPERTY_HINT_ARRAY_TYPE:
			element_type_info = TypeInfo.from_type(types.NoneType)

		else:
			element_type_str = prop_info.hint_string # XXX
			element_type_info = TypeInfo.from_type(_get_type_object_by_registered_name(element_type_str)) # XXX

		return cls(element_type_info = element_type_info)

	@classmethod
	@functools.cache
	def from_api_info_type_string(cls, type_str: str) -> TypeInfo:
		if type_str != 'Array' and not type_str.startswith('typedarray::'):
			raise ValueError

		if type_str == 'Array':
			element_type_info = TypeInfo.from_type(types.NoneType)

		else:
			element_type_str = type_str.removeprefix('typedarray::')

			# XXX: need proper parsing element types like '24/17:Font'
			element_type_str = element_type_str.rsplit(':', -1)[-1]

			element_type_info = TypeInfo.from_type(_get_type_object_by_registered_name(element_type_str)) # XXX

		return cls(element_type_info = element_type_info)

	@functools.cached_property
	def type_object(self) -> type:
		element_type = self.element_type_info.type_object
		if element_type is types.NoneType:
			element_type = None # XXX
		return godot.Array[element_type]

	# XXX: is this right for arrays?
	@functools.cached_property
	def implicit_cast_type_object(self) -> type | None:
		return self.type_object

	@functools.cached_property
	def property_info_dict(self) -> dict:
		if self.element_type_info.type_object is types.NoneType:
			return super().property_info_dict

		else:
			return {**super().property_info_dict, **dict(
				hint = godot.PropertyHint.PROPERTY_HINT_ARRAY_TYPE,
				hint_string = str(self.element_type_info), # XXX
			)}

	@functools.cached_property
	def doc_type_string(self) -> str:
		return f'{self.element_type_info.doc_type_string}[]' # XXX


class ObjectTypeInfo(TypeInfo, variant_type = godot.Variant.Type.TYPE_OBJECT):
	class_name: str

	def __init__(self, *, class_name: str):
		super().__init__()

		self.class_name = class_name

	def __str__(self) -> str:
		return self.class_name

	@classmethod
	@functools.cache
	def from_type(cls, type_object: type) -> TypeInfo:
		if not issubclass(type_object, godot.Object):
			raise TypeError

		class_name = type_object.__name__ # XXX: use exposed name
		return cls(class_name = class_name)

	@classmethod
	def from_property_info(cls, prop_info: gde.GDExtensionPropertyInfo) -> TypeInfo:
		if prop_info.type != cls.variant_type:
			raise ValueError

		return cls(class_name = prop_info.class_name)

	@classmethod
	@functools.cache
	def from_api_info_type_string(cls, type_str: str) -> TypeInfo:
		if type_str not in _get_api_classes():
			raise ValueError

		return cls(class_name = type_str)

	@functools.cached_property
	def type_object(self) -> type:
		return _get_type_object_by_registered_name(self.class_name)

	@functools.cached_property
	def property_info_dict(self) -> dict:
		return {**super().property_info_dict, **dict(
			class_name = self.class_name,
		)}


class ScriptTypeInfo(ObjectTypeInfo):
	script_type_name: str # XXX: use script resource? use resource and name and path?

	def __init__(self, *, class_name: str, script_type_name: str):
		super().__init__(class_name = class_name)

		self.script_type_name = script_type_name

	def __str__(self) -> str:
		return self.script_type_name

	@classmethod
	@functools.cache
	def from_type(cls, type_object: type) -> TypeInfo:
		if not issubclass(type_object, godot.Object):
			raise TypeError

		def _most_derived_non_script_base(cls: type) -> type: # XXX
			if not isinstance(cls, type) or not issubclass(cls, godot.Object):
				raise TypeError(f'')
			return getattr(cls, '_extension_class', None) or getattr(cls, '_godot_class', godot.Object)

		from godot._python_extension.python_script import PythonScript # XXX

		class_name = _most_derived_non_script_base(type_object).__name__ # XXX: use exposed name
		script = None

		if script_class := getattr(type_object, '_script_class', None):
			for scr in PythonScript.get_all_scripts():
				if scr._class is script_class:
					script = scr
					break

		if script is None:
			raise TypeError

		script_type_name = script._class.__name__ # XXX
		return cls(class_name = class_name, script_type_name = script_type_name)

	@classmethod
	def from_property_info(cls, prop_info: gde.GDExtensionPropertyInfo) -> TypeInfo:
		if prop_info.type != cls.variant_type or prop_info.hint_string == '':
			raise ValueError

		script_type_name = prop_info.hint_string # XXX
		return cls(class_name = prop_info.class_name, script_type_name = script_type_name)

	@classmethod
	@functools.cache
	def from_api_info_type_string(cls, type_str: str) -> TypeInfo:
		raise ValueError

	@functools.cached_property
	def type_object(self) -> type:
		return _get_type_object_by_registered_name(self.script_type_name)

	@functools.cached_property
	def property_info_dict(self) -> dict:
		return {**super().property_info_dict, **dict(
			hint_string = self.script_type_name, # XXX: ???
		)}


class PointerTypeInfo(TypeInfo, variant_type = godot.Variant.Type.TYPE_INT):
	class_name: str

	def __init__(self, *, class_name: str):
		super().__init__()

		self.class_name = class_name

	def __str__(self) -> str:
		return f'{self.class_name or "void"} pointer'

	@classmethod
	@functools.cache
	def from_type(cls, type_object: type) -> TypeInfo:
		raise TypeError

	@classmethod
	def from_property_info(cls, prop_info: gde.GDExtensionPropertyInfo) -> TypeInfo:
		if (prop_info.type != cls.variant_type
			or prop_info.hint != godot.PropertyHint.PROPERTY_HINT_INT_IS_POINTER
		):
			raise ValueError

		raise ValueError # XXX

	@classmethod
	@functools.cache
	def from_api_info_type_string(cls, type_str: str) -> TypeInfo:
		if not type_str.endswith('*'):
			raise ValueError

		return cls(class_name = type_str.removesuffix('*') if type_str != 'void*' else '')

	@property
	def type_object(self) -> type:
		return None
		#raise NotImplementedError(
		#	f'bindings for pointer type {self.class_name!r} not yet implemented')

	@property
	def property_info_dict(self) -> dict:
		return {**super().property_info_dict, **dict(
			hint = godot.PropertyHint.PROPERTY_HINT_INT_IS_POINTER,
		)}


class UnionTypeInfo(TypeInfo, variant_type = godot.Variant.Type.TYPE_OBJECT): # XXX
	def __init__(self, *, type_infos: list[TypeInfo]):
		super().__init__()

		self._type_infos = type_infos

	def __str__(self) -> str:
		return ' | '.join(str(info) for info in self._type_infos) # XXX: ',' sep?

	@classmethod
	@functools.cache
	def from_type(cls, type_object: type) -> TypeInfo:
		if not isinstance(type_object, types.UnionType):
			raise TypeError

		return UnionTypeInfo(type_infos = [
				TypeInfo.from_type(type_) for type_ in typing.get_args(type_object)
			])

	@classmethod
	@functools.cache
	def from_property_info(cls, prop_info: gde.GDExtensionPropertyInfo) -> TypeInfo:
		raise ValueError # XXX

	@classmethod
	def from_api_info_type_string(cls, type_str: str) -> TypeInfo:
		if ',' not in type_str: # XXX
			raise ValueError

		return cls(type_infos = [TypeInfo.from_type(_get_type_object_by_registered_name(s)) for s in type_str.split(',')])

	@functools.cached_property
	def type_object(self) -> type:
		import operator
		return functools.reduce(operator.or_, (info.type_object for info in self._type_infos))

	@functools.cached_property
	def property_info_dict(self) -> dict:
		return {**super().property_info_dict, **dict(
			hint = godot.PropertyHint.PROPERTY_HINT_RESOURCE_TYPE, # XXX
			hint_string = ','.join(str(info) for info in self._type_infos) # XXX
		)}


