import sys
import dataclasses
import enum
import functools
import inspect
import types
import builtins
import copy

import _gdextension as gde

import godot

from . import utils
from . import extension_classes

from .utils import class_set_attr # XXX
from .utils import unspecified
from .utils import set_attr_if_unspecified

from .type_info import TypeInfo


# NOTE: Be careful in this module with `property`, `classmethod` and `staticmethod`, as these
# shadow their `builtins` equivalent. Also be careful about shadowing any of module globals with
# function locals as the names can be a common choice.


__all__ = (
	'method',
	'classmethod',
	'staticmethod',

	'expose_all_methods',

	'property',
	'property_group',
	'property_subgroup',

	'signal',
	'constant',

	'expose', # XXX

	'register_extension_class',
	#'expose_script_class', # XXX

	'get_class_info', # XXX
)


__class_info_key = '__class_info'


class APIType(enum.Enum): # XXX
	API_CORE = enum.auto()
	API_EDITOR = enum.auto()
	API_EXTENSION = enum.auto()
	API_EDITOR_EXTENSION = enum.auto()
	API_NONE = enum.auto()


class ClassType(enum.Enum): # XXX
	CORE = enum.auto()
	EDITOR = enum.auto()
	EXTENSION = enum.auto()
	EDITOR_EXTENSION = enum.auto()
	SCRIPT = enum.auto()
	DYNAMIC_SCRIPT = enum.auto()


def _repr(obj):
	def indent(text, prefix = '    ', initial_prefix = '    '):
		return (initial_prefix if text else '') + ('\n' + prefix).join(text.splitlines())

	match obj:
		case list():
			inner = '\n'.join(f'{_repr(value)},' for value in obj)
			nl = '\n' if len(obj) > 1 else ''
			return f'[{nl}{indent(inner)}{nl}]'

		case set():
			inner = '\n'.join(f'{_repr(value)},' for value in obj)
			nl = '\n' if len(obj) > 1 else ''
			return f'{{{nl}{indent(inner)}{nl}}}'

		case dict():
			inner = '\n'.join(f'{key!r}: {_repr(value)},' for key, value in obj.items())
			nl = '\n' if len(obj) > 1 else ''
			return f'{{{nl}{indent(inner)}{nl}}}'

		case _:
			if dataclasses.is_dataclass(obj):
				def getfield(name):
					if name == 'name':
						return getattr(obj, name, unspecified) # XXX
					return getattr(obj, name)
				inner = '\n'.join(f'{field.name}: {_repr(getfield(field.name))},'
					for field in dataclasses.fields(obj) if field.repr)
				nl = '\n' if inner else ''
				return f'{type(obj).__qualname__}({nl}{indent(inner)}{nl})'

			return repr(obj)


@dataclasses.dataclass(init=False, repr=False)
class exposed_member:
	name: str

	def as_dict(self):
		return dataclasses.asdict(self)

	def __init_subclass__(cls):
		doc = cls.__doc__

		dataclasses.dataclass(init=False, repr=False)(cls)

		 # XXX: dataclass will override __doc__ and prevent property instances from having docs, so restore
		cls.__doc__ = doc

	def __repr__(self):
		return _repr(self)

	def __set_name__(self, cls, name):
		self.name = name


class method(exposed_member):
	method: callable = dataclasses.field(repr=False)
	info: gde.GDExtensionClassMethodInfo

	def __init_subclass__(cls):
		cls.method = cls._method

	def __init__(self, method):
		if type(self) is godot.exposition.method:
			functools.update_wrapper(self, method)

	@functools.cached_property
	def info(self):
		return get_method_info_from_method(self.method)

	def __get__(self, inst, owner=None):
		return self.method.__get__(inst, owner)

	@builtins.property
	def _method(self):
		return self.__wrapped__

method.method = method._method


class classmethod(builtins.classmethod, method):
	@builtins.property
	def _method(self):
		return self


class staticmethod(builtins.staticmethod, method):
	@builtins.property
	def _method(self):
		return self


def expose_all_methods(cls, *, finalize_class: bool = True):
	update = False

	for name, value in vars(cls).items():
		if name.startswith('__'):
			continue

		elif isinstance(value, exposed_member):
			continue

		elif isinstance(value,
				builtins.classmethod | builtins.staticmethod | types.FunctionType | types.MethodType):
			member = method(value)

			setattr(cls, name, member)
			member.__set_name__(cls, name)

			update = True

	if update and finalize_class:
		_finalize_class(cls)

	return cls


class property(builtins.property, exposed_member):
	__uninitialized_property = {}

	name: str = unspecified
	type: godot.Variant.Type = unspecified
	class_name: str = unspecified
	hint: godot.PropertyHint = unspecified
	hint_string: str = unspecified
	usage: godot.PropertyUsageFlags = unspecified

	def __init__(self,
				*args,

				default = unspecified,
				default_factory = unspecified,

				type: godot.Variant.Type = unspecified,
				name: str = unspecified,
				class_name: str = unspecified,
				hint: godot.PropertyHint = unspecified,
				hint_string: str = unspecified,
				usage: godot.PropertyUsageFlags = unspecified,

				**kwargs
			):
		default = builtins.type(default)(default) if default is not unspecified else unspecified # XXX

		set_attr_if_unspecified(self, 'default', from_value = default)
		set_attr_if_unspecified(self, 'default_factory', from_value = default_factory)

		set_attr_if_unspecified(self, 'type', from_value = type)
		set_attr_if_unspecified(self, 'name', from_value = name)
		set_attr_if_unspecified(self, 'class_name', from_value = class_name)
		set_attr_if_unspecified(self, 'hint', from_value = hint)
		set_attr_if_unspecified(self, 'hint_string', from_value = hint_string)
		set_attr_if_unspecified(self, 'usage', from_value = usage)

		if len(args) == 1 and isinstance(args[0], builtins.property):
			self._update_accessors(copy_from = args[0], **kwargs)

		else:
			super().__init__(*args, **kwargs)

			if self.__doc__ is None and 'doc' in kwargs: # XXX: __doc__ not set by super().__init__?
				self.__doc__ = kwargs['doc']

	def __call__(self, *args, **kwargs):
		self.__init__(*args, **kwargs)
		return self

	def __set_name__(self, cls, name):
		if self.fget is None and self.fset is None and self.fdel is None:
			self._update_accessors(fget = self._get_value, fset = self._set_value)

		#if self.name is unspecified:
		#	self.name = str(godot.String.capitalize(name)) # XXX: do this elsewhere?

		type_info = TypeInfo.from_resolved_annotation(cls, name)
		prop_info = type_info.property_info

		self._prop_name = sys.intern(f'__{cls.__qualname__.replace(".", "_")}_{name}')
		self._prop_type = type_info.type_object

		set_attr_if_unspecified(self, 'type', from_object = prop_info)
		set_attr_if_unspecified(self, 'name', from_value = name)
		set_attr_if_unspecified(self, 'class_name', from_object = prop_info)
		set_attr_if_unspecified(self, 'hint', from_object = prop_info)
		set_attr_if_unspecified(self, 'hint_string', from_object = prop_info)
		set_attr_if_unspecified(self, 'usage', from_object = prop_info)

		super().__set_name__(cls, name)

	def _update_accessors(self, *args, copy_from=unspecified, **kwargs):
		if copy_from is unspecified:
			copy_from = self

		kwargs = {
			**dict(
				fget = copy_from.fget,
				fset = copy_from.fset,
				fdel = copy_from.fdel,
				doc = copy_from.__doc__
			),
			**kwargs
		}

		super().__init__(*args, **kwargs)

		self.__doc__ = copy_from.__doc__ # XXX: __doc__ not set by super().__init__?

		return self

	def _has_default_value(self) -> bool:
		return (self.default is not unspecified or self.default_factory is not unspecified)

	def _get_default_value(self):
		if self.default is not unspecified:
			return self.default

		elif self.default_factory is not unspecified:
			return self.default_factory()

		else:
			return self._prop_type()

	def	_get_value(self, inst):
		value = getattr(inst, self._prop_name, self.__uninitialized_property)

		if value is self.__uninitialized_property:
			value = self._get_default_value()
			self._set_value(inst, value)

		return value

	def	_set_value(self, inst, value):
		setattr(inst, self._prop_name, value)

	def getter(self, fget):
		return self._update_accessors(fget = fget)

	def setter(self, fset):
		return self._update_accessors(fset = fset)

	def deleter(self, fdel):
		return self._update_accessors(fdel = fdel)


class property_group(exposed_member):
	prefix: str

	def __init__(self, name: str = unspecified, *, prefix: str = unspecified):
		self.name = name
		self.prefix = '' if prefix is unspecified else prefix

	def __set_name__(self, cls, name):
		if self.name is unspecified:
			self.name = str(godot.String.capitalize(name)) # XXX: do this elsewhere?


class property_subgroup(property_group, exposed_member): # XXX: isinstance checks?
	pass


class signal(functools.cached_property, exposed_member):
	def __init__(self):
		super().__init__(lambda: None)

	def __set_name__(self, cls, name):
		self.name = name

		super().__init__(
			functools.partial(
				lambda self, name: godot.Signal(self, name),
				name = godot.StringName(self.name)
			)
		)

		super().__set_name__(cls, name)



@dataclasses.dataclass
class ClassInfo:
	name: str
	class_: type

	members: dict = dataclasses.field(default_factory=dict)

	__repr__ = exposed_member.__repr__ # XXX

	def _get_members_of_type(self, type_) -> dict:
		return {name: value for name, value in self.members.items() if isinstance(value, type_)}

	@builtins.property
	def methods(self) -> dict:
		return self._get_members_of_type(method)

	@builtins.property
	def properties(self) -> dict:
		return self._get_members_of_type(property)

	@builtins.property
	def signals(self) -> dict:
		return self._get_members_of_type(signal)





def get_class_info(cls: type) -> ClassInfo:
	if not issubclass(cls, godot.Object):
		raise TypeError(f'cannot get class info for non \'godot.Object\' type: {cls!r}')

	if script_class := getattr(cls, '_script_class', None): # XXX
		cls = script_class

	if info := cls.__dict__.get(__class_info_key):
		return info


	#if info := getattr(cls, __class_info_key, None):
	#	return info

	info = ClassInfo(name = cls.__name__, class_ = cls)
	setattr(cls, __class_info_key, info)

	return info




def constant(x):
	return utils.IntConstant(x)


def _is_method(func) -> bool:
	return not _is_static_method(func) and not _is_class_method(func)

def _is_class_method(func) -> bool:
	return (inspect.ismethod(func) and getattr(func, '__self__', None)) or isinstance(func, builtins.classmethod)

def _is_static_method(func) -> bool:
	return isinstance(func, builtins.staticmethod)


_exposed_classes = {}


#@utils.log_calls
def _finalize_class(cls, *args, expose_all_methods: bool = False, skip_finalization: bool = False, **kwargs):
	if skip_finalization:
		return

	setattr(inspect.getmodule(cls), cls.__name__, cls) # XXX

	if expose_all_methods:
		godot.exposition.expose_all_methods(cls, finalize_class = False)

	class_info = get_class_info(cls)

	class_info.members.clear()

	for name, value in vars(cls).items():
		if name.startswith('__'):
			continue

		if isinstance(value, exposed_member):
			class_info.members[name] = value

	_exposed_classes[class_info.name] = class_info # XXX

	return

	if cls.__name__ != 'Example':
		return

	print(class_info)


# XXX: if using utils.log_calls this wont log when skip_finalization is True
_finalize_class_ = _finalize_class
@functools.wraps(_finalize_class_)
def _finalize_class(*args, skip_finalization: bool = False, **kwargs):
	if skip_finalization:
		return

	return _finalize_class_(*args, skip_finalization=skip_finalization, **kwargs)


def _ensure_class_exposed(cls):
	if (
		getattr(cls, '_godot_class', None) # XXX
		or getattr(cls, '_script_class', None) # XXX
		or getattr(cls, '_extension_class', None) # XXX
	):
		return

	raise RuntimeError(f'{cls!r} is not exposed') # TODO: support unexposed classes


def get_method_info_from_method(method):
	# get and prepare method function and its signature

	func = method.__func__ if isinstance(method, builtins.classmethod) else method

	sig = inspect.signature(func)
	module = inspect.getmodule(method)
	name = getattr(method, '__name__', None) or method.__wrapped__.__name__

	if _is_class_method(method):
		# bind class method function to its class
		cls = getattr(module, method.__qualname__.rsplit('.', 1)[0])
		func = getattr(cls, method.__name__)

	# filter parameters

	parameters = list(sig.parameters.values())

	if any(param.kind == param.KEYWORD_ONLY for param in parameters):
		raise TypeError(f'cannot bind method with keyword only arguments')

	is_var_arg = any(param.kind == param.VAR_POSITIONAL for param in parameters)

	if not _is_static_method(method):
		# pop self and cls from parameters for methods and class methods
		parameters.pop(0)

	parameters = [param for param in parameters
		if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD)]

	# determine flags

	if _is_class_method(method) or _is_static_method(method):
		flags = gde.GDEXTENSION_METHOD_FLAG_STATIC
	else:
		flags = gde.GDEXTENSION_METHOD_FLAG_NORMAL

	if is_var_arg:
		flags &= ~gde.GDEXTENSION_METHOD_FLAG_NORMAL # XXX
		flags |= gde.GDEXTENSION_METHOD_FLAG_VARARG

	flags = gde.GDExtensionClassMethodFlags(flags) # XXX

	# create and return info

	arguments_info = [
		utils.apply_attrs(copy.copy(TypeInfo.from_annotation(param.annotation, context=module).property_info),
			name = param.name,
		)
		for param in parameters
	]

	default_arguments = [param.default for param in parameters if param.default != param.empty]

	return_value_info = TypeInfo.from_annotation(sig.return_annotation, context=module).property_info

	return utils.apply_attrs(gde.GDExtensionClassMethodInfo(),
		name = name,
		call_func = func,
		method_flags = flags,
		arguments_info = arguments_info,
		arguments_metadata = [gde.GDEXTENSION_METHOD_ARGUMENT_METADATA_NONE] * len(arguments_info), # XXX
		default_arguments = default_arguments,
		return_value_info = return_value_info,
	)





def register_extension_class(cls):
	return extension_classes.register_extension_class(extension_classes.bind_all_methods(cls))



def expose(*args, **kwargs):
	if len(args) == 1 and isinstance(args[0], type) and issubclass(args[0], enum.Enum): # XXX
		return args[0]

	from godot._python_extension import python_script # XXX
	return python_script.expose(*args, **kwargs)






