import io
import pathlib
import textwrap
import subprocess
import shutil
import types
import re

from SCons.Script import *

from . import build_utils


def make_extract_api_action(target, source, env):
	extern_gde = pathlib.Path('extern/gdextension').absolute()
	api_info = pathlib.Path('lib/godot/_internal').absolute()

	if not env.get('skip_extract_api_files'):
		godot = build_utils.get_executable_path('godot', env)
		subprocess.run([godot, '--headless', '--dump-gdextension-interface', '--dump-extension-api-with-docs'], cwd=extern_gde, check=True)

	shutil.copy2(extern_gde / 'extension_api.json', api_info)

	_patch_gdextension_interface_header(
		src = extern_gde / 'gdextension_interface.h',
		dest = pathlib.Path('src/.generated') / 'gdextension_interface.h',
	)


def _patch_gdextension_interface_header(src: pathlib.Path, dest: pathlib.Path):
	'''Patch `gdextension_interface.h` to use opaque pointers for type safety and deduction'''

	# read source
	code = src.read_text()

	# replace pointer typedefs
	def replace_pointer_typedef(match_):
		groups = types.SimpleNamespace(**match_.groupdict())

		if groups.type == 'MethodBind':
			groups.usage = 'Const'

		match groups.usage:
			case 'Uninitialized':
				return f'typedef struct GDExtensionUninitialized{groups.type} *GDExtensionUninitialized{groups.type}Ptr;'

			case 'Const':
				return f'typedef const struct GDExtensionOpaque{groups.type} *GDExtensionConst{groups.type}Ptr;'

			case _:
				return f'typedef struct GDExtensionOpaque{groups.type} *GDExtension{groups.type}Ptr;'

	code = re.sub(r'typedef\s+(const\s+)?void\s*\*\s*GDExtension(?P<usage>Uninitialized|Const)?(?P<type>\w+?)Ptr;',
		replace_pointer_typedef, code)

	# add GDExtensionFloat typedef
	code = re.sub(r'(typedef uint8_t GDExtensionBool;)', r'\1\ntypedef double GDExtensionFloat;', code)

	# make method bind pointers const
	code = re.sub(r'GDExtensionMethodBindPtr', 'GDExtensionConstMethodBindPtr', code)

	# replace function typedefs
	def replace_func_typedef(match_):
		groups = types.SimpleNamespace(**match_.groupdict())
		params = groups.params.split(',')

		match groups.func:
			case 'VariantFromTypeConstructorFunc':
				# fix param const
				params[1] = params[1].replace('GDExtensionTypePtr', 'GDExtensionConstTypePtr')
				return match_[0].replace(f'({groups.params})', ','.join(params).join(['(', ')']))

			case 'TypeFromVariantConstructorFunc':
				# fix param const
				params[1] = params[1].replace('GDExtensionVariantPtr', 'GDExtensionConstVariantPtr')
				return match_[0].replace(f'({groups.params})', ','.join(params).join(['(', ')']))

			case _:
				return match_[0]

	code = re.sub('typedef\s+.+?\(\*GDExtension(?P<func>\w+?)\)\((?P<params>.+?)\);', replace_func_typedef, code)

	# write dest
	dest.write_text(code)


def make_generate_gdextension_api_table_action(target, source, env):
	subprocess.run(['python', './tools/generate_gdextension_api_table.py'], check=True)


def make_r_string_action(target, source, env):
	with open(source[0].path, 'r') as file:
		data = file.read()

	buf = io.StringIO()

	delim = '-r-string-delim-'
	buf.write(f'''// generated\n\nR"{delim}({data}){delim}"\n\n''')

	with open(target[0].path, 'w') as file:
		file.write(buf.getvalue())

	buf.close()


def godot_zip_action(target, source, env):
	if not source:
		data = b''
	else:
		with open(source[0].path, 'rb') as file:
			data = file.read()

	buf = io.StringIO()

	buf.write(textwrap.dedent('''

	// generated archive of godot module

	#include <cstddef>

	namespace pygodot {

		extern const char* godot_module_archive_data;
		const char* godot_module_archive_data =
			"

	''').strip())

	line_l = 0
	for i, x in enumerate(data):
		line_l += buf.write(f'\\{hex(x)[1:]}')
		if line_l >= 100 - (4 * 3 + 2):
			line_l = 0
			buf.write(f'"\n\t\t"')

	buf.write(textwrap.dedent(f'''

	";

		extern const size_t godot_module_archive_size;
		const size_t godot_module_archive_size = {len(data)};

	}} // namespace pygodot

	''').lstrip())

	with open(target[0].path, 'w') as file:
		file.write(buf.getvalue())

	buf.close()


def init(env):
	env["BUILDERS"]["ExtractAPI"] = Builder(
		action = env.Action(make_extract_api_action,
			"Extracting GDExtension API"
		),
	)

	env["BUILDERS"]["GenerateGDExtensionAPITable"] = Builder(
		action = env.Action(make_generate_gdextension_api_table_action,
			"Generating GDExtension API Table"
		),
		suffix = ".h",
	)

	env["BUILDERS"]["MakeRString"] = Builder(
		action = env.Action(make_r_string_action,
			"Generating R string header"
		),
		suffix = ".h",
	)

	env["BUILDERS"]["MakeGodotModuleArchive"] = Builder(
		action = env.Action(godot_zip_action,
			"Generating Godot module archive."
		),
		suffix = ".cpp",
		src_suffix = ".zip",
	)

