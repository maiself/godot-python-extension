import enum

from ._internal.utils import resolve_name

from ._internal.utils import update_globals as _update_globals

#from ._internal.utils import import_variant_types
#from ._internal.utils import import_global_enums
#from ._internal.utils import import_enum


__all__ = ()


def import_variant_types():
	import godot
	from ._internal.api_info import api

	_excluded_api_names = {
		'Nil',
		'bool',
		'int',
		'float',
	} | {'Nil', 'RID', 'Variant'}

	_api_names = set()

	_api_names |= {type_info.name
		for type_info in api.builtin_classes if type_info.name not in _excluded_api_names}

	for name in _api_names:
		obj = getattr(godot, name)

		_update_globals({name: obj}, level=-1)

def import_global_enums():
	import godot
	from ._internal.api_info import api

	for enum_info in api.global_enums:
		enum_ = resolve_name(f'godot.{enum_info.name}')

		if '.' not in enum_info.name:
			_update_globals({enum_info.name: enum_}, level=-1)

		_update_globals(enum_.__members__, level=-1)


def import_enum(enum_: enum.Enum):
	_update_globals(enum_.__members__, level=-1)



