import sys
import types
import importlib.abc
import logging

import _gdextension as gde

from . import gdextension_types

import godot

from .api_info import api

from . import utils
from . import type_bind
from . import method_bind


logger = logging.Logger('godot')


_singleton_names = set(singleton.name for singleton in api.singletons)

_Engine = None


def initialize_module():
	godot.__getattr__ = _module_getattr
	godot.__dir__ = _module_dir

	godot.__all__ = ()

	#for name, value in api.header.items():
	#	setattr(godot, name, value)


	# XXX
	godot.strname = utils.strname


	godot.Variant = gde.Variant # XXX
	godot.Variant.__module__ = 'godot'

	# init enums

	with utils.timer('init enums'):
		for enum_info in api.global_enums:
			enum_ = type_bind.bind_enum(godot, enum_info)

			vars(godot).update(enum_.__members__) # XXX

	# bind variant types

	godot.RID = gde.RID # XXX
	godot.RID.__module__ = 'godot'

	with utils.timer('variant binding'):
		variant_type_names_to_skip = ('Nil', 'RID', 'Object', 'Variant')

		variant_types_to_bind = tuple(type_info for type_info in api.builtin_classes
			if not type_info.name.islower() and type_info.name not in variant_type_names_to_skip)

		# make all types available in godot module before binding
		for type_info in variant_types_to_bind:
			cls = getattr(gde, type_info.name)
			cls.__module__ = 'godot' # XXX
			setattr(godot, type_info.name, cls)

		# initialize typed array types
		from . import typed_arrays

		for type_info in variant_types_to_bind:
			type_bind.bind_variant_type(type_info)

		from . import variant_types # XXX

	# bind utilities

	with utils.timer('utility binding'):
		for info in api.utility_functions:
			method_bind.bind_method(godot, None, info)


def _module_getattr(key):
	global _singleton_names, _Engine

	if class_info := api.classes.get(key):
		logger.info(f'\033[94;1mbinding class {key}\033[0m')

		# XXX: return None when singleton is not yet registered... is this really the right thing to do?
		if _Engine and key in _singleton_names and not _Engine.has_singleton(key):
			return None

		try:
			res = type_bind.bind_class(class_info)
		except Exception as exc:
			#print(''.join(utils.format_exception(exc)).removesuffix('\n'), file=sys.stderr) # XXX
			raise# RuntimeError

		#if _Engine:
		#	# XXX: it seems this is needed as available singletons may change
		#	_singleton_names |= set(_Engine.get_singleton_list())

		if key in _singleton_names:
			res = gde.global_get_singleton(key)

			if res is None:
				raise RuntimeError(
					f'failed to retrieve singleton {key!r}')

			if key == 'Engine':
				_Engine = res

		setattr(godot, key, res)

		return res

	raise AttributeError(
		f'module {godot.__name__!r} has no attribute {key!r}')


_api_names = set()
_excluded_api_names = {
	'Nil',
	'bool',
	'int',
	'float',
}

def _module_dir():
	if not _api_names:
		for key in api.keys():
			if key == 'header':
				pass#_api_names.update(api.header.keys())
			else:
				_api_names.update(
					obj.name
					for obj in getattr(api, key)
					if hasattr(obj, 'name') and obj.name not in _excluded_api_names
				)

	return sorted(set(vars(godot).keys()) | _api_names)


