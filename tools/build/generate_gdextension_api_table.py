#!/usr/bin/env python3

import sys
import pathlib
import types
import dataclasses
import re


tools_dir = pathlib.Path(__file__).parent.parent.resolve()
project_dir = tools_dir.parent
gdextension_dir = project_dir / 'extern' / 'gdextension'

gdextension_interface_path = gdextension_dir / 'gdextension_interface.h' # XXX: have passed in
api_info_path = project_dir / 'lib' / 'godot' / '_internal' / 'api_info.py' # XXX: have passed in

header_path = project_dir / 'src' / '.generated' / 'gdextension_api_table.h' # XXX: have passed in

# float_32 float_64 double_32 double_64
build_configuration = 'float_64' # XXX: add support for other build confguations

# float_64
_variant_sizes = dict(
	Nil = 0,
	bool = 1,
	int = 8,
	float = 8,
	String = 8,
	Vector2 = 8,
	Vector2i = 8,
	Rect2 = 16,
	Rect2i = 16,
	Vector3 = 12,
	Vector3i = 12,
	Transform2D = 24,
	Vector4 = 16,
	Vector4i = 16,
	Plane = 16,
	Quaternion = 16,
	AABB = 24,
	Basis = 36,
	Transform3D = 48,
	Projection = 64,
	Color = 16,
	StringName = 8,
	NodePath = 8,
	RID = 8,
	Object = 8,
	Callable = 16,
	Signal = 16,
	Dictionary = 8,
	Array = 8,
	PackedByteArray = 16,
	PackedInt32Array = 16,
	PackedInt64Array = 16,
	PackedFloat32Array = 16,
	PackedFloat64Array = 16,
	PackedStringArray = 16,
	PackedVector2Array = 16,
	PackedVector3Array = 16,
	PackedColorArray = 16,
	PackedVector4Array = 16,
	Variant = 24,
)


def import_path_as(path: pathlib.Path, module_name: str, *, level: int = 0):
	import importlib.util
	spec = importlib.util.spec_from_file_location(module_name, path)
	module = importlib.util.module_from_spec(spec)
	sys.modules[module_name] = module
	spec.loader.exec_module(module)

	import inspect
	frame = inspect.currentframe().f_back
	for i in range(-level):
		frame = frame.f_back

	frame.f_globals[module_name] = module


@dataclasses.dataclass
class VariantTypeInfo:
	name: str
	size: int
	enum_value_name: str | None

	@property
	def gde_type_name(self) -> str:
		return dict(
			Nil = 'Variant',
			bool = 'GDExtensionBool',
			int = 'GDExtensionInt',
			float = 'GDExtensionFloat',
		).get(self.name, self.name)


def get_variant_enum_value_name(variant_type_name):
	if variant_type_name == 'Variant':
		return None
	name = re.sub(r'([a-z0-9])([A-Z])(?!$)', r'\1_\2', variant_type_name).upper()
	return f'GDEXTENSION_VARIANT_TYPE_{name.upper()}'


def main():
	header_path.parent.mkdir(exist_ok=True)

	header_mtime = header_path.stat().st_mtime if header_path.exists() else 0
	self_mtime = pathlib.Path(__file__).stat().st_mtime
	interface_mtime = gdextension_interface_path.stat().st_mtime

	if header_mtime >= max(self_mtime, interface_mtime):
		return

	print(f'generating {header_path.relative_to(project_dir)}')

	#import_path_as(api_info_path, 'api_info')

	#api = api_info.api

	#build_config_info = api.builtin_class_sizes.get(
	#	build_configuration, key='build_configuration', default=api_info.raise_not_found)

	variant_types_info = {}

	#for size_info in build_config_info.sizes:
	for name, size in _variant_sizes.items():
		#print(size_info)
		if name == 'Variant':
			variant_types_info['Nil'].size = size
			continue

		variant_type_info = VariantTypeInfo(name = name, size = size,
			enum_value_name = get_variant_enum_value_name(name))
		variant_types_info[name] = variant_type_info

	data = gdextension_interface_path.read_text()

	s = []

	s.append('// generated api tables')
	s.append('')
	s.append('#pragma once')
	s.append('')
	s.append('// GDEXTENSION_API(api_name, api_typedef_name)')
	s.append('')
	s.append('#define GDEXTENSION_APIS \\')
	for m in re.finditer(r'/\*[^@/]*@name\s+(?P<api_name>\w+)[^/]*\*/[^(]*\(\*(?P<api_typedef_name>\w+)\)\(.*?\);', data):
	#print(data)
	#for m in re.finditer(r'/\*[^@/]*@name\s+(?P<name>\w+)', data):
		ns = types.SimpleNamespace(**m.groupdict())

		s.append(f'\tGDEXTENSION_API({ns.api_name}, {ns.api_typedef_name}) \\')


	s.append('')
	s.append('// GDEXTENSION_VARIANT_TYPE(type_name, type_size, type_enum_name)')
	s.append('')
	s.append('#define GDEXTENSION_VARIANT_TYPES \\')

	for type_ in variant_types_info.values():
		s.append(f'\tGDEXTENSION_VARIANT_TYPE({type_.gde_type_name}, {type_.size}, {type_.enum_value_name or ""}) \\')


	s.append('')
	s.append('')

	text = '\n'.join(s)

	#if not header_path.exists() or header_path.read_text() != text:
	header_path.write_text(text)


if __name__ == '__main__':
	main()

