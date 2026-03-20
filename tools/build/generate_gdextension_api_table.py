#!/usr/bin/env python3

import sys
import pathlib
import types
import dataclasses
import re
import argparse
import itertools


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

	composite_depth = 0

	low_type: str = 'void'
	ndim: int = 0
	shape: list = dataclasses.field(default_factory = list)
	strides: list = dataclasses.field(default_factory = list)

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
	parser = argparse.ArgumentParser()
	parser.add_argument('--print', action='store_true')

	args = parser.parse_args()

	header_path.parent.mkdir(exist_ok=True)

	header_mtime = header_path.stat().st_mtime if header_path.exists() else 0
	self_mtime = pathlib.Path(__file__).stat().st_mtime
	interface_mtime = gdextension_interface_path.stat().st_mtime

	update = header_mtime < max(self_mtime, interface_mtime)

	if not update and not args.print:
		return

	if update:
		print(f'generating {header_path.relative_to(project_dir)}')

	import_path_as(api_info_path, 'api_info')

	api = api_info.api

	build_config_info = api.builtin_class_sizes.get(
		build_configuration, key='build_configuration', default=api_info.raise_not_found)

	build_config_info_member_offsets = api.builtin_class_member_offsets.get(
		build_configuration, key='build_configuration', default=api_info.raise_not_found)

	variant_types_info = {}

	for name, size in [size_info.values() for size_info in build_config_info.sizes]:
	#for name, size in _variant_sizes.items():
		#print(name, size)
		if name == 'Variant':
			variant_types_info['Nil'].size = size
			continue

		variant_type_info = VariantTypeInfo(name = name, size = size,
			enum_value_name = get_variant_enum_value_name(name))
		variant_types_info[name] = variant_type_info


	def _resolve_depth(name):
		try:
			members = getattr(build_config_info_member_offsets.classes, name, None).members
		except ValueError:
			return 0

		return 1 + max(_resolve_depth(member.meta) for member in members)

	for name, members in [info.values() for info in build_config_info_member_offsets.classes]:
		variant_types_info[name].composite_depth = _resolve_depth(name)

		#print(f'{name} : {variant_types_info[name].composite_depth = }')


	def _resolve_member_type(name, depth = 0):
		if name not in variant_types_info or variant_types_info[name].composite_depth <= depth:
			return [name]

		try:
			members = getattr(build_config_info_member_offsets.classes, name, None).members
		except ValueError:
			return [name]

		return [*itertools.chain(*(_resolve_member_type(member.meta, depth) for member in members))]


	def get_size_as_member(name):
		match name.lower():
			case 'float':
				return 4
			case 'double':
				return 8
			case 'byte':
				return 1

		if '32' in name:
			return 4
		if '64' in name:
			return 8

		if '8' in name:
			return 1

		return variant_types_info[name].size

	def fix_member_type(name):
		match name.lower():
			case 'float' | 'float32':
				return 'float'
			case 'float64':
				return 'double'
			case 'int32':
				return 'int32_t'
			case 'int64':
				return 'int64_t'
			case 'byte':
				return 'uint8_t'
		return name


	for name, members in [info.values() for info in build_config_info_member_offsets.classes]:
	#for name, size in _variant_sizes.items():
		#print(name, ':', ', '.join([m.meta for m in members]))

		max_depth_limit = 4

		types_low = _resolve_member_type(name)
		types_high = _resolve_member_type(name, 1 if variant_types_info[name].composite_depth > 1 else 0)

		if any(type_ != types_low[0] for type_ in types_low):
			raise RuntimeError(f'non homogeneous variant type: {name}')

		if (types_high == types_low) or any(type_ != types_high[0] for type_ in types_high):
			types_high = []

		#print(types_low)
		#print(types_high)

		type_ = types_low[0]
		count = len(types_low)

		if variant_types_info[name].size != get_size_as_member(type_) * count:
			raise RuntimeError(f'composite variant member size mismatch: {name}'
				f'\n\t({variant_types_info[name].size = })'
				f' != (get_size_as_member({type_!r}) * {count} = {get_size_as_member(type_) * count})')

		if types_high:
			if len(types_low) % len(types_high) != 0:
				raise RuntimeError()
			shape = [len(types_high), len(types_low) // len(types_high)]
			strides = [get_size_as_member(types_high[0]), get_size_as_member(type_)]
		else:
			shape = [len(types_low)]
			strides = [get_size_as_member(type_)]

		variant_types_info[name].low_type = fix_member_type(type_)
		variant_types_info[name].ndim = len(shape)
		variant_types_info[name].shape = shape
		variant_types_info[name].strides = strides

		#print(f'{name} : {type_}[{len(types_low)}]  {shape = }  {strides = }')

		#print()



	for variant_type_info in variant_types_info.values():
		if not (match_ := re.fullmatch(r'Packed(.+)Array', variant_type_info.name)) or 'String' in match_[1]:
			continue

		name = fix_member_type(match_[1])

		if name in variant_types_info and variant_types_info[name].shape:
			for attr in ['low_type', 'ndim', 'shape', 'strides']:
				setattr(variant_type_info, attr, getattr(variant_types_info[name], attr))

			variant_type_info.ndim += 1
			variant_type_info.shape = [0] + variant_type_info.shape
			variant_type_info.strides = [get_size_as_member(name)] + variant_type_info.strides

		else:

			variant_type_info.low_type = name
			variant_type_info.ndim = 1
			variant_type_info.shape = [0]
			variant_type_info.strides = [get_size_as_member(name)]

	#for variant_type_info in variant_types_info.values():
	#	print(variant_type_info)

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
	s.append('// GDEXTENSION_BUFFER_TYPE(type_name, type_size, base_type, ndim, shape, strides)')
	s.append('')
	s.append('#define _GDE_NO_PAREN(...) __VA_ARGS__ // remove parentheses')
	s.append('')
	s.append('#define GDEXTENSION_BUFFER_TYPES \\')

	for type_ in variant_types_info.values():
		if not type_.ndim:
			continue

		s.append(f'\tGDEXTENSION_BUFFER_TYPE({type_.gde_type_name}, {type_.size}, {type_.low_type or ""}, {type_.ndim}, _GDE_NO_PAREN({', '.join(str(x) for x in type_.shape)}), _GDE_NO_PAREN({', '.join(str(x) for x in type_.strides)})) \\')


	s.append('')
	s.append('')

	text = '\n'.join(s)

	if update:
		#if not header_path.exists() or header_path.read_text() != text:
		header_path.write_text(text)

	if args.print:
		print(text)


if __name__ == '__main__':
	main()

