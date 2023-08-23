import enum

import _gdextension as gde

import godot

from . import utils
from .utils import apply_attrs, fullname


@utils.swap_members
class GDExtensionClassMethodInfo(gde.GDExtensionClassMethodInfo):
	def __repr__(info): # XXX
		from . import api_info
		return api_info.pretty_string(dict(
			name = info.name,
			call_func = info.call_func,
			method_flags = info.method_flags,
			arguments_info = info.arguments_info,
			arguments_metadata = info.arguments_metadata,
			return_value_info = info.return_value_info,
		))


@utils.swap_members
class GDExtensionPropertyInfo(gde.GDExtensionPropertyInfo):
	def __getattribute__(self, name):
		res = object.__getattribute__(self, name)

		if isinstance(res, (godot.String, godot.StringName)):
			return str(res)

		match name:
			case 'type':
				return godot.Variant.Type(res)

			case 'hint':
				return godot.PropertyHint(res)

			case 'usage':
				return godot.PropertyUsageFlags(res)

			case _:
				return res

	def __str__(self):
		def fmt(x):
			if isinstance(x, enum.Enum):
				return x.name.replace(
					'PROPERTY_USAGE_STORAGE|PROPERTY_USAGE_EDITOR', 'PROPERTY_USAGE_DEFAULT')
			return repr(x)

		args = ', '.join(f'{name}={fmt(getattr(self, name))}'
			for name in ['type', 'name', 'class_name', 'hint', 'hint_string', 'usage', 'python_type'])

		return f'<PropertyInfo({args})>'

	def __repr__(info): # XXX
		from . import api_info
		return api_info.pretty_string(dict(
			type = info.type,
			name = info.name,
			class_name = info.class_name,
			hint = info.hint,
			hint_string = info.hint_string,
			usage = info.usage,
		))

	def __copy__(self):
		return apply_attrs(gde.GDExtensionPropertyInfo(),
			type = self.type,
			name = self.name,
			class_name = self.class_name,
			hint = self.hint,
			hint_string = self.hint_string,
			usage = self.usage,
			python_type = self.python_type,
		)

	@classmethod
	def from_dict(cls, dict_: dict) -> gde.GDExtensionPropertyInfo:
		return apply_attrs(cls(), **dict_)

	def as_dict(self) -> gde.GDExtensionPropertyInfo:
		return dict(
			type = self.type,
			name = self.name,
			class_name = self.class_name,
			hint = self.hint,
			hint_string = self.hint_string,
			usage = self.usage,
			#python_type = self.python_type,
		)


