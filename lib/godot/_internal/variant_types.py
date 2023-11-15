import _gdextension as gde

import godot

from . import utils
from .utils import fullname


# string and string name

@utils.swap_members
class String(gde.String):
	def __repr__(self):
		return repr(str(self))


@utils.swap_members
class StringName(gde.StringName):
	def __repr__(self):
		return repr(str(self))


# callable

@utils.swap_members
class Callable(godot.Callable):
	__call__ = godot.Callable.call


# dictionary

@utils.swap_members
class Dictionary(godot.Dictionary):
	def __str__(self):
		return f'{fullname(type(self))}({Dictionary.__str__(self)})'

	__repr__ = __str__

	def __init__(self, *args, **kwargs):
		if args and kwargs:
			raise TypeError(
				f'creating a Dictionary from another while also supplying kwargs is currently not supported')

		if kwargs:
			Dictionary.__init__(self, kwargs)

		else:
			Dictionary.__init__(self, *args)

	#def keys(self):
	#	return [str(key) for key in Dictionary.keys(self)]

	def items(self):
		return ((key, self[key]) for key in self.keys())
		#return ((str(key), self[key]) for key in self.keys())

	def __contains__(self, key):
		self.has(key)

	#def __iter__(self):
	#	return (str(key) for key in self.keys())


