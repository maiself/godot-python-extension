import io
import pathlib
import textwrap
import subprocess
import shutil

from SCons.Script import *

from . import build_utils


def make_extract_api_action(target, source, env):
	godot = build_utils.get_executable_path('godot', env)

	extern_gde = pathlib.Path('extern/gdextension').absolute()
	api_info = pathlib.Path('lib/godot/_internal').absolute()

	subprocess.run([godot, '--headless', '--dump-gdextension-interface', '--dump-extension-api'], cwd=extern_gde, check=True)

	shutil.copy2(extern_gde / 'extension_api.json', api_info)

	shutil.copy2(extern_gde / 'gdextension_interface.h', pathlib.Path('src/.generated'))
	subprocess.run(['git', 'apply', '--directory=src/.generated/', 'tools/gde_interface_types.patch'], check=True)


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

