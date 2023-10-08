import types
import enum
import functools

import _gdextension as gde

import godot

from . import utils
from .utils import class_set_attr

from .api_info import api

from . import class_type
#from . import method_bind


@utils.with_context
def bind_variant_type(type_info):
	from . import method_bind
	from .type_info import TypeInfo

	if type_info.name == 'Array':
		from .typed_arrays import ArrayBase
		cls = ArrayBase
	else:
		cls = getattr(godot, type_info.name) # gde vs godot, arrays

	method_bind.bind_variant_constructors(cls, type_info)

	if cls.__name__ not in ['String', 'StringName']:
		cls.__str__ = lambda self: gde.variant_stringify(self) # XXX
		cls.__repr__ = lambda self: f'<{utils.fullname(type(self))} {str(self)}>' # XXX

	if cls.__name__ in ['NodePath']:
		cls.__str__ = lambda self: gde.variant_stringify(self) # XXX
		cls.__repr__ = lambda self: f'<{utils.fullname(type(self))} {str(self)!r}>' # XXX

	for info in type_info.get('constants', []):
		if info.type == 'int':
			const = utils.IntConstant(info.value)
		else:
			const = utils.parse_value_str_to_value(info.value, type_ = info.type)

		class_set_attr(cls, info.name, const)

	for info in type_info.get('enums', []):
		bind_enum(cls, info)

	for member_info in type_info.get('members', []):
		variant_type = TypeInfo.from_api_info_type_string(type_info.name).variant_type
		member_type = TypeInfo.from_api_info_type_string(member_info.type).variant_type

		getter = gde.variant_get_ptr_getter(variant_type, member_info.name, member_type)
		setter = gde.variant_get_ptr_setter(variant_type, member_info.name, member_type)

		prop = property(getter, setter)

		class_set_attr(cls, member_info.name, prop)

	for method_info in type_info.get('methods', []):
		method_bind.bind_method(cls, type_info, method_info)

	method_bind.bind_variant_operators(cls, type_info)


	# XXX XXX: move this elsewhere

	variant_type_has_members = bool(type_info.get('members'))
	variant_type_has_non_const_methods = False
	variant_type_has_destructor = type_info.has_destructor

	for method_info in type_info.get('methods', []):
		if method_info.get('is_static'):
			continue

		if not method_info.get('is_const'):
			variant_type_has_non_const_methods = True
			break

	'''print(dict(
		name = type_info.name,
		has_members = variant_type_has_members,
		has_non_const_methods = variant_type_has_non_const_methods,
		has_destructor = variant_type_has_destructor,
	))'''

	cls._variant_type_has_members = variant_type_has_members # XXX
	cls._variant_type_has_non_const_methods = variant_type_has_non_const_methods # XXX
	cls._variant_type_has_destructor = variant_type_has_destructor # XXX

	# XXX



	#print_doc(cls)
	return cls




class property_proxy_attr_descriptor:
	def __init__(self, descriptor):
		self._descriptor = descriptor

	#@utils.log_calls
	def __get__(self, prop_proxy, obj_type=None):
		return self._descriptor.__get__(prop_proxy._bound_property_proxy__get(), obj_type)

	#@utils.log_calls
	def __set__(self, prop_proxy, value):
		self._descriptor.__set__(prop_proxy._bound_property_proxy__get(), value)
		prop_proxy._bound_property_proxy__set()


def property_proxy_non_const_method(method):
	#@utils.log_calls
	@functools.wraps(method)
	def wrapper(prop_proxy, *args, **kwargs):
		res = method.__get__(prop_proxy._bound_property_proxy__get())(*args, **kwargs)
		prop_proxy._bound_property_proxy__set()
		return res

	return wrapper


def _is_non_const_method(obj):
	return getattr(obj, '_is_non_const_method', False) # XXX


#property
class property_proxy(): # XXX
	_bound_property_proxy_types = {}

	def __init__(self, getter, setter, *, type):
		self.fget = getter
		self.fset = setter
		self._type = type

	def __set_name__(self, cls, name):
		self._name = f'_{cls.__name__}__{name}'

	def __repr__(self):
		return f'<{type(self).__name__} {self._name!r}>'

	@classmethod
	def _get_bound_property_proxy_type(cls, type_):
		if proxy_type := cls._bound_property_proxy_types.get(type_):
			return proxy_type

		assert(not type_._variant_type_has_destructor)

		class bound_property_proxy(type_):
			def __init__(self, obj, getter, setter):
				self.__obj = obj
				self.__getter = getter
				self.__setter = setter

				self.__get()

			#@utils.log_calls
			def __get(self):
				super().__init__(self.__getter(self.__obj)) # XXX: __init__
				return self

			#@utils.log_calls
			def __set(self):
				self.__setter(self.__obj, self)
				return self

		for name, value in list(vars(type_).items()):
			if hasattr(value, '__get__'):
				if name.startswith('__init_') or name in ('__new__', ):
					continue

				if _is_non_const_method(value):
					desc = property_proxy_non_const_method(value)
				else:
					desc = property_proxy_attr_descriptor(value)
				setattr(bound_property_proxy, name, desc)

		bound_property_proxy.__name__ = type_.__name__
		bound_property_proxy.__qualname__ = type_.__qualname__
		bound_property_proxy.__module__ = type_.__module__

		cls._bound_property_proxy_types[type_] = bound_property_proxy

		return bound_property_proxy

	#@utils.log_calls
	def __get__(self, obj, obj_type=None):
		if prop := getattr(obj, self._name, None):
			return prop

		else:
			prop = self._get_bound_property_proxy_type(self._type)(obj, self.fget, self.fset)
			setattr(obj, self._name, prop)
			return prop

	#@utils.log_calls
	def __set__(self, obj, value):
		if prop := getattr(obj, self._name, None):
			if value is prop:
				return # XXX: implace ops may call __set__ twice, is this the best way to handle?

		self.fset(obj, value)



_class_bindings_in_progress = set()

@utils.with_context
def bind_class(class_info):
	from . import method_bind
	from .type_info import TypeInfo

	if class_info.name in _class_bindings_in_progress:
		raise RuntimeError(f'binding of class {class_info.name!r} already in process')

	_class_bindings_in_progress.add(class_info.name)

	if inherits := class_info.get('inherits'):
		bases = (getattr(godot, inherits), )
	else:
		bases = ()

	namespace = types.SimpleNamespace()

	namespace.__module__ = 'godot'
	namespace.__name__ = class_info.name
	namespace.__qualname__ = class_info.name

	namespace._godot_class = None # XXX

	for info in class_info.get('constants', []):
		class_set_attr(namespace, info.name, utils.IntConstant(info.value))

	for info in class_info.get('enums', []):
		bind_enum(namespace, info)

	if class_info.name == 'Object':
		cls = class_type.class_type(class_info.name, (gde.Object, ), vars(namespace), skip_finalization=True)

		@utils.swap_members
		class Object(cls, skip_finalization=True):
			def __new__(cls, *args, **kwargs):
				inst = Object.__new__(cls, *args, **kwargs) # creates the object
				Object.__init__(inst) # creates the c++ / python object association
				return inst

			def __init__(self, *args, **kwargs):
				pass

			def free(self):
				self.callv('free', []) # XXX

	else:
		cls = type(class_info.name, bases, vars(namespace), skip_finalization=True)

	cls._godot_class = cls # XXX

	class_set_attr(godot, class_info.name, cls)

	for method_info in class_info.get('methods', []):
		if method_info.get('is_hidden'): # XXX
			continue

		method_bind.bind_method(cls, class_info, method_info)

	for prop_info in class_info.get('properties', []):
		if prop_info.get('is_hidden'): # XXX
			continue

		getter = getattr(cls, prop_info.get('getter'), None) if prop_info.get('getter') else None
		setter = getattr(cls, prop_info.get('setter'), None) if prop_info.get('setter') else None

		if not getter and not setter:
			continue

		prop_type = TypeInfo.from_api_info_type_string(prop_info.type).type_object

		if getattr(prop_type, '_variant_type_has_members', False): # XXX
			prop = property_proxy(getter, setter, type=prop_type)
		else:
			prop = property(getter, setter)

		class_set_attr(cls, prop_info.name, prop)

	for signal_info in class_info.get('signals', []):
		signal_prop = functools.cached_property(
			functools.partial(
				lambda self, name: godot.Signal(self, name),
				name = godot.StringName(signal_info.name)
			)
		)

		class_set_attr(cls, signal_info.name, signal_prop)

	_class_bindings_in_progress.remove(class_info.name)

	return cls




@utils.with_context
def bind_enum(cls, enum_info):
	name = enum_info.name
	qualname = name if isinstance(cls, types.ModuleType) else f'{cls.__qualname__}.{name}'
	module = cls.__name__ if isinstance(cls, types.ModuleType) else cls.__module__

	enum_type = enum.IntFlag if enum_info.get('is_bitfield') else enum.IntEnum

	if name.startswith('Variant.'):
		# special handling of variant enums to mirror the same enums from gdextension
		cls = godot.Variant
		name = name.split('.', 1)[1]

		gde_type = getattr(gde, f'GDExtensionVariant{name}')

		enum_meta = type(f'Variant{name}Meta', (type(gde_type), enum.EnumType), dict(
			__call__ = enum.EnumType.__call__,
		))

		enum_type = type.__new__(enum_meta, f'Variant{name}Enum', (enum.Enum, gde_type), dict(
			__init__ = gde_type.__init__,
			__str__ = lambda self: f'{qualname}.{self.name}',
			__repr__ = lambda self: f'<{self}: {int(self.value)}>',
		))

	elif '.' in name:
		raise NameError(f'unexpected enum type name: {name!r}')

	enum_ = enum_type(
			name,
			{value.name: value.value for value in enum_info.get('values')},
			module = module,
			qualname = qualname,
		)

	class_set_attr(cls, name, enum_)

	return enum_


