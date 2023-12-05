import sys
import types
import typing
import abc
import weakref

import _gdextension as gde

import godot

from .general_utils import *


MethodType = typing.Union[*(
	getattr(types, name)
	for name in dir(types)
	if 'Method' in name and 'Descriptor' not in name and callable(getattr(types, name))
)]


def decompose_method(method) -> tuple[types.FunctionType, object]:
	if not isinstance(method, MethodType) or not hasattr(type(method.__self__), method.__name__):
		raise TypeError(f'{method!r} is not a decomposable method object')

	return (getattr(type(method.__self__), method.__name__), method.__self__)


class WeakMethod(abc.ABC):
	def __init__(self, method):
		super().__init__()

		self.__hash = hash(method)
		self.__name = sys.intern(f'{type(method.__self__).__qualname__}.{method.__name__}')

	@property
	@abc.abstractmethod
	def method(self):
		pass

	def __call__(self, *args, **kwargs):
		if method := self.method:
			return method(*args, **kwargs)

	def __bool__(self):
		return bool(self.method)

	def __eq__(self, other):
		if isinstance(other, __class__):
			return self.method == other.method

		elif isinstance(other, weakref.ref):
			return self.method == other()

		else:
			return self.method == other

	def __hash__(self):
		return self.__hash

	def __repr__(self):
		obj = None
		if method := self.method:
			obj = method.__self__
		return f'<{__class__.__name__} {self.__name} of {repr(obj) if obj else "expired"}>'

	__str__ = __repr__


class WeakMethodViaClassFunction(WeakMethod):
	def __init__(self, method):
		super().__init__(method)

		func, obj = decompose_method(method)

		self.__func__ = func
		self.__self_ref__ = weakref.ref(obj)

	@property
	def __self__(self):
		return self.__self_ref__()

	@property
	def method(self):
		if obj := self.__self_ref__():
			return self.__func__.__get__(obj)


class WeakMethodViaName(WeakMethod):
	def __init__(self, method):
		super().__init__(method)

		func, obj = decompose_method(method)

		self.__method_class__ = type(obj)
		self.__method_name__ = func.__name__
		self.__self_ref__ = weakref.ref(obj)

	@property
	def __self__(self):
		return self.__self_ref__()

	@property
	def __func__(self):
		return getattr(self.__method_class__, self.__method_name__, None)

	@property
	def method(self):
		if obj := self.__self_ref__():
			if func := self.__func__:
				return func.__get__(obj)


def weak_method_via_class_function(method):
	return WeakMethodViaClassFunction(method)


def weak_method_via_name(method):
	return WeakMethodViaName(method)


def weak_method(method):
	global weak_method

	class_reloading_enabled = godot.Engine.is_editor_hint()

	weak_method = weak_method_via_name if class_reloading_enabled else weak_method_via_class_function

	return weak_method(method)


def callable_or_weak_method(func):
	if not callable(func):
		raise TypeError(f'{func!r} is not callable')

	if isinstance(func, MethodType):
		# bound method

		if isinstance(func.__self__, godot.Object) and godot.Object.has_method(func.__self__, func.__name__):
			# self object has a method with name visible to godot, so create and use a standard callable
			return godot.Callable(func.__self__, func.__name__)

		try:
			#with print_exceptions_and_continue():
				return weak_method(func)

		except TypeError:
			# unable to decompose the method
			pass

	return func


def original_callable(func): # TODO: hook this up
	if isinstance(func, godot.Callable):
		if func.is_standard():
			return getattr(func.get_object(), func.get_method())

		elif custom := gde.callable_custom_get_userdata(func):
			func = custom

		else:
			return func

	if isinstance(func, WeakMethod):
		if method := func.method:
			return method

	return func


#@log_calls
def cast_to_callable(func):
	'''Prepare the `func` for storing in a `Callable`.'''
	return callable_or_weak_method(func)


#@log_calls
def cast_from_callable(func):
	'''Retrieve the original callable from a `Callable`, or
	the `Callable` itself if not holding a python callable'''
	return original_callable(func)


