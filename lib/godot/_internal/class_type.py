import inspect

import _gdextension as gde

from . import utils


class cached_class_property:
	def __init__(self, fget=None):
		self.fget = fget

	def __set_name__(self, cls, name):
		if name.startswith('__') and not name.endswith('__'):
			name = f'_{cls.__name__}{name}'
		self.name = name

	def __get__(self, instance, owner):
		value = self.fget(owner)
		setattr(owner, self.name, value)
		return value


def _get_named_kwargs(func) -> set[str]:
	sig = inspect.signature(func)
	return [param.name for param in sig.parameters.values() if param.kind == param.KEYWORD_ONLY]


class class_type(utils.metaclasses.reuse_type_object_meta, type(gde.Object)):
	'''Metaclass for all godot.Object derived classes'''

	@cached_class_property
	def __finalize_class(cls):
		from .exposition import _finalize_class # XXX: cant import exposition from global scope
		return _finalize_class

	@cached_class_property
	def __finalize_class_named_kwargs(cls):
		return _get_named_kwargs(cls.__finalize_class)

	def __new__(meta, *args, **kwargs):
		filtered_kwargs = {
			key: value
			for key, value in kwargs.items()
			if key not in meta.__finalize_class_named_kwargs
		}

		cls = super().__new__(meta, *args, **filtered_kwargs)

		meta.__finalize_class(cls, *args, **kwargs)

		return cls


