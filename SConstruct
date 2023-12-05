#!/usr/bin/env python

'''
This file is partially derived from [godotengine/godot-cpp](https://github.com/godotengine/godot-cpp)'s `SConstruct` file. See [tools/build/platform/license.md](tools/build/platform/license.md) for license.
'''

import sys
import os
import pathlib
import contextlib

from SCons.Errors import UserError

from tools.build import build_utils


EnsureSConsVersion(4, 0)


try:
	Import("env")
except:
	# Default tools with no platform defaults to gnu toolchain.
	# We apply platform specific toolchains via our custom tools.
	env = Environment(tools=["default"], PLATFORM="")


# Default num_jobs to local cpu count if not user specified.
build_utils.set_default_num_jobs(env)


# to enable color output during builds
if 'TERM' in os.environ:
	env['ENV']['TERM'] = os.environ['TERM']

# hide intermediate build artifacts
env["OBJPREFIX"] = '.'
env["SHOBJPREFIX"] = '.'


# Custom options and profile flags.
opts = Variables(build_utils.get_custom_paths(), ARGUMENTS)

opts.Add(
	EnumVariable(
		"platform",
		"Target platform",
		default=env.get("platform", build_utils.detect_platform()),
		allowed_values=build_utils.platforms,
		ignorecase=2,
	)
)


opts.Add(
	EnumVariable(
		key="precision",
		help="Set the floating-point precision level",
		default=env.get("precision", "single"),
		allowed_values=("single", "double"),
	)
)


# Add platform options
tools = {}
for pl in build_utils.platforms:
	tool = Tool(pl, toolpath=["tools/build/platform"])
	if hasattr(tool, "options"):
		tool.options(opts)
	tools[pl] = tool


# CPU architecture options.
opts.Add(
	EnumVariable(
		key="arch",
		help="CPU architecture",
		default=env.get("arch", ""),
		allowed_values=build_utils.architecture_array,
		map=build_utils.architecture_aliases,
	)
)


# godot python options

opts.Add(
	PathVariable(
		key="python",
		help="Path to the `python` to build against.",
		default='python3',
		validator=(lambda key, val, env: build_utils.validate_executable(key, val, env)
			if not env.get('python_lib_dir') else None),
	)
)

opts.Add(
	PathVariable(
		key="python_lib_dir",
		help="Path to the Python `lib` directory or the Python build directory. Used to locate the `_sysconfigdata_*.py` file if the built `python` cannot be run on the local host.",
		default=None,
	)
)

opts.Add(
	BoolVariable(
		key="skip_module_embed",
		help="Skip embedding the Godot module into the compiled library for faster iteration during development. Use with the GODOT_PYTHON_MODULE_LIB_DIR environment variable.",
		default=False,
	)
)


opts.Add(
	BoolVariable(
		key="single_source",
		help="Build using a single translation unit.",
		default=False,
	)
)


# for now there's no distinction between build targets, so always use template_release
env['target'] = 'template_release'


# Targets flags tool (optimizations, debug symbols)
target_tool = Tool("targets", toolpath=["tools/build/platform"])
target_tool.options(opts)


opts.Update(env)
Help(opts.GenerateHelpText(env))


# Process CPU architecture argument.
build_utils.process_arch(env)


# godot-cpp's linux toolchain config needs this set
env['use_hot_reload'] = False


tool = Tool(env["platform"], toolpath=["tools/build/platform"])

if tool is None or not tool.exists(env):
	raise ValueError("Required toolchain not found for platform " + env["platform"])

tool.generate(env)
target_tool.generate(env)


# Detect and print a warning listing unknown SCons variables to ease troubleshooting.
unknown = opts.UnknownVariables()
if unknown:
	print("WARNING: Unknown SCons variables were passed and will be ignored:")
	for item in unknown.items():
		print("	" + item[0] + "=" + item[1])


print("Building for architecture " + env["arch"] + " on platform " + env["platform"])


# Require C++20
if env.get("is_msvc", False):
	env.Append(CXXFLAGS=["/std:c++20"])
	env.Append(CXXFLAGS=["/Zc:preprocessor"])
	env.Append(CCFLAGS=["/EHsc"])
else:
	env.Append(CXXFLAGS=["-std=c++20"])

if env["precision"] == "double":
	env.Append(CPPDEFINES=["REAL_T_IS_DOUBLE"])


scons_cache_path = os.environ.get("SCONS_CACHE")
if scons_cache_path is not None:
	CacheDir(scons_cache_path)
	Decider("MD5")


# ensure generated directory exists
generated_path = pathlib.Path('src/.generated')
generated_path.mkdir(exist_ok=True)


# gather sources

sources = set()
python_sources = set()

sources.update(pathlib.Path('src').glob('**/*.cpp'))

for ext in ('py', 'pyc', 'json', 'svg', 'md'):
	python_sources.update(pathlib.Path('lib').glob(f'**/*.{ext}'))

# exclude `extension_api.json` as it will be retrieved and cached when running from the editor
python_sources.discard(pathlib.Path('lib/godot/_internal/extension_api.json'))


# filter
sources = [os.fspath(path) for path in sorted(sources) if '.generated' not in path.parts]
python_sources = [os.fspath(path) for path in sorted(python_sources)
	if not any(part.startswith('.') for part in path.parts)]

# add back after filtering
sources.append(os.fspath(generated_path / 'godot_module_archive.cpp'))

if env.get('single_source', False):
	single_source_path = (generated_path / 'single_source.cpp')
	single_source_path.write_text(
		'\n'.join(f'#include "{pathlib.Path(source).relative_to("src")}"' for source in sources) + '\n')

	sources[:] = [os.fspath(single_source_path)]


# init builders
from tools.build import builders
builders.init(env)


# setup targets

env.Alias("extract_api", [
	env.ExtractAPI(
		target = [
			os.fspath(generated_path / 'gdextension_interface.h'),
		],
		source = [
			'extern/gdextension/gdextension_interface.h',
			builders.__file__
		],
	)
])

env.Alias("generate_gdextension_api_table", [
	env.GenerateGDExtensionAPITable(
		target = os.fspath(generated_path / 'gdextension_api_table.h'),
		source = [
			'extern/gdextension/gdextension_interface.h',
			builders.__file__,
			'./tools/build/generate_gdextension_api_table.py',
		],
	)
])

env.Alias("archive_importer_r_string", [
	env.MakeRString(
		target = os.fspath(generated_path / 'archive_importer_r_string.h'),
		source = [
			'lib/godot/_internal/utils/archive_importer.py',
			builders.__file__,
		],
	)
])

if not env.get('skip_module_embed', False):
	# pkg_files = Install('src', files)
	godot_zip = Zip(
			target = os.fspath(generated_path / 'godot.zip'),
			source = python_sources,
			ZIPROOT = 'lib',
		)
	Alias('godot_zip', godot_zip)
else:
	godot_zip = None

env.Alias("godot_module_archive", [
	env.MakeGodotModuleArchive(
		target = os.fspath(generated_path / 'godot_module_archive.cpp'),
		source = [
			godot_zip,
			builders.__file__,
		],
	)
])


from tools.build import prepare_python

prepared_python_config = prepare_python.platform_configs[(env['platform'], env['arch'])]


def _fetch_python(target, source, env):
	dest = pathlib.Path(target[0].path).parent
	dest.mkdir(parents=True, exist_ok=True)
	prepare_python.fetch_python_for_platform(env['platform'], env['arch'], dest)

fetch_python_alias = env.Alias("fetch_python", [
	Builder(action = env.Action(_fetch_python, "Fetching Python"))(
		env,
		target = os.fspath(generated_path / 'python'
			/ prepared_python_config.name / pathlib.Path(prepared_python_config.source_url).name),
		source = [
		],
	)
])


def _prepare_python(target, source, env):
	dest = pathlib.Path(target[0].path).parent.resolve()
	dest.mkdir(parents=True, exist_ok=True)

	src = pathlib.Path(source[0].path).parent.resolve()

	env['python'] = prepare_python.prepare_for_platform(env['platform'], env['arch'],
		src_dir = src, dest_dir = dest)

prepare_python_alias = env.Alias("prepare_python", [
	Builder(action = Action(_prepare_python, "Preparing Python"))(
		env,
		target = f'bin/{prepared_python_config.name}/python312.zip', # XXX: version
		source = [
			fetch_python_alias[0].children(),
			prepare_python.__file__,
		],
	)
])



# TODO: build python
# TODO: freeze standard library


# set flags

with_lto = env.get('with_lto', False)
strip = env.get('strip', False)


if not env.get('is_msvc'):
	env.Append(CCFLAGS = ['-fvisibility=hidden', *['-flto'] * with_lto]) # XXX
	env.Append(LINKFLAGS = ['-fvisibility=hidden', *['-flto'] * with_lto, *['-s'] * strip]) # XXX

else:
	env.Append(LIBS = ['Shell32.lib', ])


if env['platform'] == 'windows':
	# linker has trouble if the table is too large
	env.Append(CPPDEFINES = ['CLASS_VIRTUAL_CALL_TABLE_SIZE=512'])


env.Prepend(CPPPATH=['src', os.fspath(generated_path), 'extern/pybind11/include'])

env.Append(CPPDEFINES = [f'PYGODOT_PLATFORM=\\"{env["platform"]}\\"'])
env.Append(CPPDEFINES = [f'PYGODOT_ARCH=\\"{env["arch"]}\\"'])


def _append_python_config(env, target, **kwargs):
	src_dir = generated_path / 'python' / prepared_python_config.name
	env['python'] = os.fspath(prepare_python.get_python_for_platform(env['platform'], env['arch'], src_dir))

	from tools.build import python_config
	_config_vars = python_config.get_python_config_vars(env)

	env.Append(LIBPATH = _config_vars.lib_paths)
	env.Append(LINKFLAGS = _config_vars.link_flags)
	env.Append(LIBS = _config_vars.link_libs)
	env.Append(CPPPATH = _config_vars.include_flags)

	if env['platform'] != 'windows':
		env.Append(CPPDEFINES = [f'PYTHON_LIBRARY_PATH=\\"{_config_vars.ldlibrary or ""}\\"'])

	dest = pathlib.Path(target[0].path)
	dest.write_text(repr(_config_vars))


append_python_config = Builder(action = Action(_append_python_config, None))(
	env, target='src/.generated/.append_python_config', source=None)

env.Depends(append_python_config, prepare_python_alias)
env.AlwaysBuild(append_python_config)

env.Depends(sources, append_python_config)


# library name
suffix = ".{}".format(env["platform"])
if env.dev_build:
	suffix += ".dev"
if env["precision"] == "double":
	suffix += ".double"
suffix += "." + env["arch"]
if env["ios_simulator"]:
	suffix += ".simulator"

env["suffix"] = suffix

env["OBJSUFFIX"] = suffix + env["OBJSUFFIX"]

library_name = "libgodot-python{}{}".format(env["suffix"], env["SHLIBSUFFIX"])

library = env.SharedLibrary(
	target = f"bin/{env['platform']}-{env['arch']}/{library_name}",
	source = sources,
)

Default(library)
Return("env")


