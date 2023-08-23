import _gdextension as gde

import godot

from . import python_language
from . import utils
from . import script_utils


class _script_instance_info_meta(type(gde.GDExtensionScriptInstanceInfo)):
	def __new__(cls, name, bases, namespace):
		def wrap(func): # XXX
			import sys, functools
			@functools.wraps(func)
			def wrapper(*args, **kwargs):
				try:
					return func(*args, **kwargs)
				except Exception as exc:
					exc.__traceback__ = exc.__traceback__.tb_next
					raise
			return wrapper

		return utils.apply_attrs(bases[0](),
			**{name: wrap(value) for name, value in namespace.items() if not name.startswith('__')})


class PythonScriptInstanceInfo(gde.GDExtensionScriptInstanceInfo, metaclass=_script_instance_info_meta):
	def set_func(inst, name: godot.StringName, value: object) -> bool:
		if _set := getattr(inst, '_set', None):
			return _set(name, value)

		setattr(inst, str(name), value) # XXX
		return True # XXX

		return False

	def get_func(inst, name: godot.StringName) -> object:
		if _get := getattr(inst, '_get', None):
			return _get(name)

		return getattr(inst, str(name)) # XXX

		raise AttributeError

	def get_property_list_func(inst) -> list[dict]:
		class_info = godot.exposition.get_class_info(type(inst)) # XXX
		return [
			prop_info.as_dict() for prop_info in class_info.properties.values()
		]
		return [
			dict( # XXX
				name = 'test_prop',
				type = godot.Variant.Type.TYPE_FLOAT,
				usage = godot.PropertyUsageFlags.PROPERTY_USAGE_DEFAULT,
			),
		]

	def free_property_list_func(inst, props: list[dict]):
		pass


	def property_can_revert_func(inst, name: godot.StringName) -> bool:
		return False

	def property_get_revert_func(inst, name: godot.StringName) -> object:
		raise AttributeError


	def get_owner_func(inst):
		return inst

	def get_property_state_func(inst):
		pass


	def get_method_list_func(inst):
		pass

	def free_method_list_func(inst):
		pass

	def get_property_type_func(inst, name: godot.StringName) -> godot.Variant.Type | None:
		raise AttributeError


	def has_method_func(inst, name):
		meth = script_utils._get_script_class_attr(type(inst), str(name), None)
		#print(f'has_method_func', inst, name, meth, callable(meth))
		return isinstance(meth, godot.exposition.method)
		return callable(meth)

		return callable(script_utils._get_script_class_attr(type(inst), str(name), None))


	#@utils.with_context
	def call_func(inst, method, *args):
		try:
			method = getattr(inst, str(method))
		except AttributeError:
			raise NotImplementedError

		return method(*args)

	def notification_func(inst, what):
		if hasattr(inst, '_notification'):
			inst._notification(utils.IntConstant.lookup(type(inst), what, prefix='NOTIFICATION_'))


	def to_string_func(inst) -> str:
		return str(inst)


	#def refcount_incremented_func():
	#def refcount_decremented_func():

	def get_script_func(inst) -> godot.Script:
		return inst.get_script() # XXX

	#def is_placeholder_func():

	#def set_fallback_func():
	#def get_fallback_func():

	def get_language_func(inst) -> godot.ScriptLanguage:
		return python_language.PythonLanguage.get()

	#def free_func():


