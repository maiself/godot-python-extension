import godot

from . import utils


_script_class_cache = {}



def _most_derived_non_script_base(cls: type) -> type:
	if not isinstance(cls, type) or not issubclass(cls, godot.Object):
		raise TypeError(f'')
	return getattr(cls, '_extension_class', None) or getattr(cls, '_godot_class', godot.Object)


class script_class_type(type(godot.Object)):
	'''Metaclass for all script classes'''

	def __repr__(cls):
		return f'<script class {utils.fullname(cls)!r}>'

	def __eq__(cls, other):
		return super(cls._script_class).__eq__(other)

	def __subclasscheck__(cls, subclass):
		return cls._script_class in subclass.__mro__

	def __instancecheck__(cls, instance):
		return cls._script_class in instance.__class__.__mro__

	def __hash__(cls):
		return id(cls)

	def __call__(cls, *args, **kwargs):
		obj = cls.__new__(cls, *args, **kwargs)

		obj.set_script(godot.ResourceLoader.load(cls._script_path))

		if (res := obj.__init__(*args, **kwargs)) is not None:
			raise TypeError(
				f'__init__() should return None, not \'{type(res).__name__}\'')

		return obj


def set_script_class(obj: godot.Object, cls: type):
	obj_base = _most_derived_non_script_base(type(obj))

	if cls is None:
		obj.__class__ = obj_base
		return

	cls_base = _most_derived_non_script_base(cls)

	if cls == cls_base:
		msg = f'{cls!r} is not a script class'
		raise TypeError(msg)

	if type(obj) == cls:
		return

	if not issubclass(obj_base, cls_base):
		msg = f'cannot assign more derived script class {utils.fullname(cls)!r} to object {obj!r}, ' \
			f'{utils.fullname(cls_base)!r} is more derived than ' \
			f'{utils.fullname(obj_base)!r}'
		raise TypeError(msg)

	if obj_base is cls_base:
		obj.__class__ = cls
		return

	key = (obj_base, cls)

	if key not in _script_class_cache:
		_script_class_cache[key] = script_class_type(
			cls.__name__,
			(cls, obj_base),
			dict(
				__qualname__ = cls.__qualname__,
				__module__ = cls.__module__,
				_script_class = cls,
			),
			skip_finalization = True,
			reuse_type_object = False,
		)

	obj.__class__ = _script_class_cache[key]




