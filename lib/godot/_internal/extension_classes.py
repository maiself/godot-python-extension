import functools
import logging
import enum
import inspect
import typing

import godot

import _gdextension as gde

from . import utils

from .utils import apply_attrs


__all__ = (
	'register_extension_class',
	#'register_extension_class_method',
	#'bind_method',
	'bind_all_methods',
)

def bind_all_methods(c):
	return c

logger = logging.Logger(__name__)


_registered_classes = {}
_registered_class_infos = {}


class _extension_class_info_meta(type(gde.GDExtensionClassCreationInfo)):
	def __new__(cls, name, bases, namespace):
		def __new__(info, cls, *args, **kwargs):
			def wrap(func): # XXX
				import sys, functools

				if hasattr(func, '__wrapped__') and not isinstance(func, classmethod):
					func = func.__wrapped__

				if isinstance(func, classmethod):
					func = func.__wrapped__

					@functools.wraps(func)
					def wrapper(*args, **kwargs):
						try:
							return func(cls, *args, **kwargs)
						except Exception as exc:
							exc.__traceback__ = exc.__traceback__.tb_next
							raise

				else:
					@functools.wraps(func)
					def wrapper(*args, **kwargs):
						try:
							return func(*args, **kwargs)
						except Exception as exc:
							exc.__traceback__ = exc.__traceback__.tb_next
							raise

				return wrapper

			return utils.apply_attrs(bases[0](),
				**{name: wrap(value) for name, value in namespace.items() if not name.startswith('__')},
				create_instance_func = cls,
				class_userdata = cls,
			)

		return type(name, (), dict(__new__ = __new__))


class ExtensionClassInfo(gde.GDExtensionClassCreationInfo, metaclass=_extension_class_info_meta):
	@utils.with_context
	@classmethod
	def get_virtual_func(cls, name: str):
		func = getattr(cls, name, None)

		if getattr(func, '_not_implemented', False): # XXX
			return None

		method_info = utils.get_method_info(cls, name)

		if not method_info:
			raise RuntimeError(
				f'failed to get method info for virtual {cls.__qualname__}.{name}')

		ret_cls = str(method_info.return_value_info.class_name) # XXX
		#if ret_cls and ret_cls.startswith('godot.'):
		#	import godot
		#	ret_cls = getattr(godot, ret_cls.removeprefix('godot.'), None)
		#	if issubclass(ret_cls)

		if ret_cls == 'godot.Error': # XXX
			@functools.wraps(func)
			def wrapper(*args, **kwargs):
				try:
					return func(*args, **kwargs)
				except Exception as exc:
					msg = ''.join(utils.format_exception(exc)).removesuffix('\n')
					gde.print_error(msg, '', '', 0, False) # XXX
					return godot.Error.FAILED

			return wrapper

		return func

	@utils.with_context
	#@utils.log_calls
	@classmethod
	def get_property_list_func(cls, inst) -> list[dict]:
		class_info = godot.exposition.get_class_info(cls)#type(inst)) # XXX
		return []
		return [
			prop_info.as_dict() for prop_info in class_info.properties
		]
		return [dict(
			name = 'test_prop_a',
			type = godot.Variant.Type.TYPE_FLOAT,
			usage = godot.PropertyUsageFlags.PROPERTY_USAGE_DEFAULT,
		)]

	def free_property_list_func(inst, prop_list):
		pass

	def set_func(inst, name, value):
		if hasattr(inst, str(name)):
			setattr(inst, str(name), value)
			return True
		return False

	def get_func(inst, name):
		return getattr(inst, str(name))
		return False

	def property_can_revert_func(inst, name) -> bool:
		if hasattr(inst, str(name)):
			return True
		return False

	def property_get_revert_func(inst, name):
		return getattr(inst, str(name))


@utils.with_context
def register_extension_class(cls):
	logger.info(f'\033[96;2mregistering extension class \033[96;1m{cls.__name__}\033[0m')

	if _registered_classes.get(cls.__name__) is cls: # XXX: reloaded class
		return cls

	_registered_classes[cls.__name__] = cls

	class_info = ExtensionClassInfo(cls)

	_registered_class_infos[cls.__name__] = class_info

	cls._extension_class = cls # XXX

	gde.classdb_register_extension_class(cls.__name__, cls.__mro__[1].__name__, class_info)

	setattr(inspect.getmodule(cls), cls.__name__, cls) # XXX

	'''import types
	for name, value in vars(cls).items():
		if isinstance(value, classmethod):
			value = value.__wrapped__

		if not hasattr(value, '_deferred_register'):
			continue

		del value._deferred_register

		register_extension_class_method(value, cls)'''



	for key, val in cls.__dict__.items():
		if not isinstance(val, type) or not issubclass(val, enum.Enum): # XXX: check if exposed
			continue

		for enum_ in val:
			gde.classdb_register_extension_class_integer_constant(cls.__name__, val.__name__,
					enum_.name, enum_.value, isinstance(enum_, enum.Flag)
				)

	for key, val in cls.__dict__.items():
		if not isinstance(val, utils.IntConstant):
			continue

		gde.classdb_register_extension_class_integer_constant(cls.__name__, '',
				val.name, val, False
			)

	bounds_method_names = set()

	for member in godot.exposition.get_class_info(cls).members.values():
		if isinstance(member, godot.exposition.method):
			if member.name in bounds_method_names:
				raise TypeError(f'method {member.name!r} already bound')

			gde.classdb_register_extension_class_method(cls.__name__, member.info)
			bounds_method_names.add(member.name)

		elif isinstance(member, godot.exposition.signal):
			gde.classdb_register_extension_class_signal(cls.__name__, member.name, [])

		elif isinstance(member, godot.exposition.property_subgroup):
			gde.classdb_register_extension_class_property_subgroup(cls.__name__, member.name, member.prefix)

		elif isinstance(member, godot.exposition.property_group):
			gde.classdb_register_extension_class_property_group(cls.__name__, member.name, member.prefix)

		elif isinstance(member, godot.exposition.property):
			prop_info = gde.GDExtensionPropertyInfo.from_dict(member.as_dict())

			def get_bound_member_name(func: typing.Callable | None) -> str | None:
				if func and func.__name__ in bounds_method_names:
					return func.__name__

			getter_name = get_bound_member_name(member.fget)
			setter_name = get_bound_member_name(member.fset)

			class AccessorType(enum.Enum):
				GET = enum.auto()
				SET = enum.auto()

			def make_accessor(func, accessor_type: AccessorType) -> str:
				accessor_name = f'_{accessor_type.name.lower()}_{prop_info.name}'

				if accessor_name in bounds_method_names:
					raise TypeError(f'property accessor {accessor_name!r} already bound')

				method_info = godot.exposition.method(func)
				method_info.name = accessor_name
				method_info.info.name = accessor_name

				match accessor_type:
					case AccessorType.GET:
						if len(method_info.info.arguments_info) != 0:
							raise TypeError(f'property getter {accessor_name!r} must not have any arguments')

						method_info.info.return_value_info = \
							gde.GDExtensionPropertyInfo.from_dict(member.as_dict())

					case AccessorType.SET:
						if len(method_info.info.arguments_info) != 1:
							raise TypeError(f'property setter {accessor_name!r} must have exactly one argument')

						method_info.info.arguments_info = [
							gde.GDExtensionPropertyInfo.from_dict(member.as_dict())
						]

						method_info.info.return_value_info = \
							gde.GDExtensionPropertyInfo.from_dict(dict(type=godot.Variant.Type.TYPE_NIL))

				gde.classdb_register_extension_class_method(cls.__name__, method_info.info)
				bounds_method_names.add(accessor_name)

				# XXX: is this needed? leads to binding twice
				#godot.exposition.get_class_info(cls).members.append(method_info)

				return accessor_name

			if not getter_name and member.fget:
				getter_name = make_accessor(member.fget, AccessorType.GET)

			if not setter_name and member.fset:
				setter_name = make_accessor(member.fset, AccessorType.SET)

			gde.classdb_register_extension_class_property(cls.__name__, prop_info, setter_name, getter_name)

		else:
			raise TypeError(f'unknown member type {member!r}')

	return cls



