import collections.abc
import types
import atexit

import godot
from . import utils
from .utils import fullname


def _mimic_base_fullname(cls):
	base = cls.__base__
	for key in ('__name__', '__qualname__', '__module__'):
		setattr(cls, key, getattr(base, key))
	return cls

def _mimic_and_replace_base(cls):
	_mimic_base_fullname(cls)
	setattr(
		utils.resolve_name('.'.join(utils.fullname(cls).split('.')[:-1])),
		cls.__name__,
		cls)
	return cls


_ArrayBase = godot.Array


@_mimic_and_replace_base
class ArrayBase(godot.Array):
	def __str__(self):
		return f'{fullname(type(self))}({super().__str__()})'

	__repr__ = __str__


def _get_array_type_params(array):
	import godot
	return (godot.Variant.Type(array.get_typed_builtin()),
		array.get_typed_class_name(), array.get_typed_script())

def _get_typed_array_type(params) -> type:
	variant_type, class_name, script = params

	if variant_type != godot.Variant.Type.TYPE_OBJECT:
		return godot.Array[utils.variant_type_from_enum(variant_type)]

	if script is None:
		return godot.Array[getattr(godot, class_name)]

	return godot.Array[script._class] # XXX



@atexit.register
def _clear_array_type_cache():
	ArrayMeta._type_cache.clear()


class ArrayMeta(type(ArrayBase)):
	_type_cache = {}

	@utils.with_context
	def __new__(meta, name, bases, namespace):
		#print('\033[91;1m__new__\033[0m', (meta, name, bases, namespace))
		if '_element_type' not in namespace:
			raise TypeError(f'Array types must have an \'_element_type\' attribute')
		return super().__new__(meta, name, bases, namespace)

	@utils.with_context
	def __getitem__(cls, element_type):
		meta = ArrayMeta

		if cls not in (ArrayBase, godot.Array):
			raise TypeError(f'{cls.__name__} can only have a single element type')

		if isinstance(element_type, tuple):
			if len(element_type) != 1:
				raise TypeError(f'{cls.__name__} can only have a single element type')
			element_type = element_type[0]

		def norm_element_types(*types):
			nonlocal element_type
			for (godot_type, python_type) in types:
				if element_type in (godot_type, python_type):
					element_type = godot_type
					break

		norm_element_types(
			(godot.Dictionary, dict),
			(godot.String, str),
			(godot.Array, list),
		)

		if element_type is godot.Variant:
			element_type = None

		if array_type := meta._type_cache.get(element_type):
			#print('\033[91;1mcached!\033[0m', element_type)
			return array_type

		ns = types.SimpleNamespace()

		if element_type:
			ns.__name__ = f'{ArrayBase.__name__}[{fullname(element_type)}]'
			ns.__qualname__ = f'{ArrayBase.__qualname__}[{fullname(element_type)}]'
		else:
			ns.__name__ = f'{ArrayBase.__name__}'
			ns.__qualname__ = f'{ArrayBase.__qualname__}'

		ns.__module__ = ArrayBase.__module__

		ns._element_type = element_type

		#ns._variant_type = utils.variant_enum_from_type_inferred(element_type) if element_type else None
		#ns._object_class = '' # TODO
		#ns._script_type = None # TODO

		ns._implicit_casts = True

		#print('\033[91;1m__getitem__\033[0m', element_type)
		array_type = meta(ns.__name__, (ArrayBase, ), vars(ns))

		meta._type_cache[element_type] = array_type

		return array_type

	@utils.with_context
	def __call__(cls, *args, **kwargs):
		meta = type(ArrayBase)

		if not args:
			return meta.__call__(cls)

		array, args = args[0], args[1:]

		if type(array) is _ArrayBase:
			type_alias = cls
			if type_alias is godot.Array:
				type_alias = None

			if type_alias is None and godot.Array.is_typed(array):
				params = (
					godot.Variant.Type(godot.Array.get_typed_builtin(array)),
					godot.Array.get_typed_class_name(array),
					godot.Array.get_typed_script(array)
				)

				type_alias = _get_typed_array_type(params)

				if type_alias is godot.Array:
					raise TypeError

				return type_alias(array)

			obj = cls.__new__(cls, array, *args, **kwargs)

			try:
				if not args:
					godot.Array.__init__._constructors[1](obj, array)
				else:
					godot.Array.__init__._constructors[2](obj, array, *args)

			except BaseException:
				godot.Array.__init__._constructors[0](obj)
				raise

			return obj

		if args or not isinstance(array, (ArrayBase, collections.abc.Sequence)): # XXX
			return meta.__call__(cls, array, *args)

		if getattr(array, '_element_type', None) == cls._element_type:# or cls._element_type is None:
			return meta.__call__(type(array), array)

		typed_array_params = utils.full_type_description(cls._element_type)

		return meta.__call__(cls, array, *typed_array_params)

	@utils.with_context
	def __subclasscheck__(cls, subclass):
		if super().__subclasscheck__(subclass):
			return True

		return cls is godot.Array and issubclass(subclass, ArrayBase) # XXX

	@utils.with_context
	def __instancecheck__(cls, instance):
		if super().__instancecheck__(instance):
			return True

		return cls is godot.Array and isinstance(instance, ArrayBase) # XXX


godot.Array = ArrayMeta.__getitem__(godot.Array, godot.Variant)

if godot.Array is not utils.variant_type_from_enum(godot.Variant.Type.TYPE_ARRAY):
	raise RuntimeError(f'failed in install typed array machinery')





'''class Array(metaclass=ArrayMeta):
	def __init__(self, *args, **kwargs):
		pass

	def _check_cast(self, value):
		if not self._element_type or isinstance(value, self._element_type):
			return value

		if self._implicit_casts:
			try:
				return self._element_type(value)
			except Exception:
				pass

		raise ValueError(
			f'value {value!r} is not of type {self._element_type.__name__!r}')

	def __setitem__(self, index, value):
		super().__setitem__(index, self._check_cast(value))

	def append(self, value):
		super().append(self._check_cast(value))

	def __repr__(self):
		return f'{type(self).__name__}({super().__repr__()})'
'''





