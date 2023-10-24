'''
This file is partially derived from [godotengine/godot-cpp](https://github.com/godotengine/godot-cpp)'s `tools/godotcpp.py` file. See [tools/build/platform/license.md](tools/build/platform/license.md) for license.
'''

import sys
import os
import platform
import shutil
import subprocess

import SCons
from SCons.Errors import UserError

from SCons.Script import *


platforms = (
	"linux",
	"macos",
	"windows",
	"android",
	"ios",
	"web"
)

architecture_array = [
	"",
	"universal",
	"x86_32",
	"x86_64",
	"arm32",
	"arm64",
	"rv64",
	"ppc32",
	"ppc64",
	"wasm32"
]

architecture_aliases = {
	"x64": "x86_64",
	"amd64": "x86_64",
	"armv7": "arm32",
	"armv8": "arm64",
	"arm64v8": "arm64",
	"aarch64": "arm64",
	"rv": "rv64",
	"riscv": "rv64",
	"riscv64": "rv64",
	"ppcle": "ppc32",
	"ppc": "ppc32",
	"ppc64le": "ppc64",
}


def normalize_path(val, env):
	return val if os.path.isabs(val) else os.path.join(env.Dir("#").abspath, val)


def validate_file(key, val, env):
	if not os.path.isfile(normalize_path(val, env)):
		raise UserError("'%s' is not a file: %s" % (key, val))


def validate_dir(key, val, env):
	if not os.path.isdir(normalize_path(val, env)):
		raise UserError("'%s' is not a directory: %s" % (key, val))


def validate_parent_dir(key, val, env):
	if not os.path.isdir(normalize_path(os.path.dirname(val), env)):
		raise UserError("'%s' is not a directory: %s" % (key, os.path.dirname(val)))


def detect_platform() -> str:
	# Try to detect the host platform automatically.
	# This is used if no `platform` argument is passed
	if sys.platform.startswith("linux"):
		return "linux"
	elif sys.platform == "darwin":
		return "macos"
	elif sys.platform == "win32" or sys.platform == "msys":
		return "windows"
	elif ARGUMENTS.get("platform", ""):
		return ARGUMENTS.get("platform")
	else:
		raise ValueError("Could not detect platform automatically, please specify with platform=<platform>")


def set_default_num_jobs(env):
	# Default num_jobs to local cpu count if not user specified.
	# SCons has a peculiarity where user-specified options won't be overridden
	# by SetOption, so we can rely on this to know if we should use our default.
	initial_num_jobs = env.GetOption("num_jobs")
	altered_num_jobs = initial_num_jobs + 1
	env.SetOption("num_jobs", altered_num_jobs)
	if env.GetOption("num_jobs") == altered_num_jobs:
		cpu_count = os.cpu_count()
		if cpu_count is None:
			print("Couldn't auto-detect CPU count to configure build parallelism. Specify it with the -j argument.")
		else:
			safer_cpu_count = cpu_count if cpu_count <= 4 else cpu_count - 1
			print(
				"Auto-detected %d CPU cores available for build parallelism. Using %d cores by default. You can override it with the -j argument."
				% (cpu_count, safer_cpu_count)
			)
			env.SetOption("num_jobs", safer_cpu_count)


def get_custom_paths() -> list[str]:
	customs = ["custom.py"]
	profile = ARGUMENTS.get("profile", "")
	if profile:
		if os.path.isfile(profile):
			customs.append(profile)
		elif os.path.isfile(profile + ".py"):
			customs.append(profile + ".py")

	return customs


def process_arch(env):
	# Process CPU architecture argument.
	if env["arch"] == "":
		# No architecture specified. Default to arm64 if building for Android,
		# universal if building for macOS or iOS, wasm32 if building for web,
		# otherwise default to the host architecture.
		if env["platform"] in ["macos", "ios"]:
			env["arch"] = "universal"
		elif env["platform"] == "android":
			env["arch"] = "arm64"
		elif env["platform"] == "web":
			env["arch"] = "wasm32"
		else:
			host_machine = platform.machine().lower()
			if host_machine in architecture_array:
				env["arch"] = host_machine
			elif host_machine in architecture_aliases.keys():
				env["arch"] = architecture_aliases[host_machine]
			elif "86" in host_machine:
				# Catches x86, i386, i486, i586, i686, etc.
				env["arch"] = "x86_32"
			else:
				print("Unsupported CPU architecture: " + host_machine)
				Exit()


def get_executable_path(key, env):
	val = env.get(key)

	if os.path.sep in val:
		return normalize_path(val, env)

	return shutil.which(val)


def validate_executable(key, val, env):
	if '--help' in sys.argv:
		return

	if not val:
		raise UserError(f"Please specify a path for '{key}'")

	if os.path.sep in val:
		path = normalize_path(val, env)

		if not os.path.exists(path):
			raise UserError(f"Path '{key}' not found: {val!r}")

		elif not os.access(path, os.X_OK):
			raise UserError(f"Path '{key}' is not executable: {val!r}")

	else:
		path = shutil.which(val)

		if not path:
			raise UserError(f"Path '{key}' is not an executable found in PATH: {val!r}")

		elif not os.access(path, os.X_OK):
			raise UserError(f"Path '{key}' is not executable: {val!r} (found in PATH as {path!r})")



def run_with_output(*args: list[str], **kwargs) -> str:
	return subprocess.run(args, capture_output=True, text=True, check=True, **kwargs).stdout

