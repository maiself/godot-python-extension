#!/usr/bin/env python3

import sys
import pathlib
import types
import dataclasses
import re


tools_dir = pathlib.Path(__file__).parent.resolve()
project_dir = tools_dir.parent
gdextension_dir = project_dir / 'extern' / 'gdextension'

gdextension_interface_path = gdextension_dir / 'gdextension_interface.h' # XXX: have passed in
api_info_path = project_dir / 'lib' / 'godot' / '_internal' / 'api_info.py' # XXX: have passed in

header_path = project_dir / 'src' / '.generated' / 'gdextension_api_table.h' # XXX: have passed in

# float_32 float_64 double_32 double_64
build_configuration = 'float_64' # XXX: add support for other build confguations


def import_path_as(path: pathlib.Path, module_name: str, *, level: int = 0):
	import importlib
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

	import_path_as(api_info_path, 'api_info')

	api = api_info.api

	build_config_info = api.builtin_class_sizes.get(
		build_configuration, key='build_configuration', default=api_info.raise_not_found)

	variant_types_info = {}

	for size_info in build_config_info.sizes:
		#print(size_info)
		if size_info.name == 'Variant':
			variant_types_info['Nil'].size = size_info.size
			continue

		variant_type_info = VariantTypeInfo(name = size_info.name, size = size_info.size,
			enum_value_name = get_variant_enum_value_name(size_info.name))
		variant_types_info[size_info.name] = variant_type_info

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

