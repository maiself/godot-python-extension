import types
import abc
import collections.abc
import functools
import operator

import godot
import godot.variant_types


__all__ = (
	'strname',

	'StringType',
	'ArrryType',
	'VariantType',

	'StringLikeType',

	'CustomCallable',
)


def _type_union_from_iter(it) -> types.UnionType:
	return functools.reduce(operator.or_, it)


# XXX
strname = godot.strname


# type unions

StringType = godot.String | godot.StringName

ArrayType = _type_union_from_iter(
	getattr(godot, type_name)
	for type_name in sorted(godot.variant_types.__all__)
	if 'Array' in type_name
)

VariantType = _type_union_from_iter(
	getattr(godot, type_name)
	for type_name in sorted(godot.variant_types.__all__)
)


# abstract base classes

class StringLikeType(abc.ABC):
	pass

StringLikeType.register(str)
StringLikeType.register(godot.String)
StringLikeType.register(godot.StringName)


class _CustomCallableMeta(abc.ABCMeta):
	def __call__(cls, *args, **kwargs):
		return cls._class_call(cls, *args, **kwargs)


class CustomCallable(collections.abc.Callable, metaclass=_CustomCallableMeta):
	'''Abstract base class that represents all `collections.abc.Callable`s that are not `godot.Callable`s.

	If called as a function with a single argument, returns that callable unmodified, or retrieves
	the custom callable from that `godot.Callable` if any.
	'''

	def _class_call(cls, *args, **kwargs):
		# if the first argument is a `godot.Callable` try to get the custom callable from it
		if args and isinstance(args[0], godot.Callable):
			args = args[0].get_custom(), *args[1:]

		if cls is __class__ and args and isinstance(args[0], godot.Callable | collections.abc.Callable):
			# if `CustomCallable` is called directly and the first argument is a callable return it
			return args[0]
		else:
			# otherwise create the object normally
			return super(type(cls), type(cls)).__call__(cls, *args, **kwargs)

	@classmethod
	def __subclasshook__(cls, subclass):
		if cls is __class__:
			if issubclass(subclass, godot.Callable):
				return False

			return collections.abc.Callable.__subclasshook__(subclass)

		return NotImplemented



