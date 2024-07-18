#include <array>
#include <string>
#include <cstdio>
#include <cstring>

#include <pybind11/embed.h>

#include "extension/extension.h"
#include "util/exceptions.h"
#include "util/system.h"
#include "variant/string.h"
#include "variant/string_name.h"


namespace pygodot {


namespace py = pybind11;


extern const char* godot_module_archive_data;
extern const size_t godot_module_archive_size;


static std::unique_ptr<py::gil_scoped_release> released_gil;


static std::vector<std::function<void()>> cleanup_functions;

void register_cleanup_func(std::function<void()> func) {
	cleanup_functions.push_back(func);
}


static struct runtime_config_t {
	std::filesystem::path executable_path;

	std::string program_name;
	std::vector<std::string> argv;

	std::filesystem::path project_path;

	std::filesystem::path library_path;
	std::filesystem::path lib_dir_path;

	std::filesystem::path python_home_path;

	void init() {
		// `executable_path`, `program_name` and `argv`
		executable_path = get_executable_path();

		program_name = (executable_path.is_absolute()
				? "." / std::filesystem::relative(executable_path)
				: executable_path
			).string();

		argv = get_argv();

		// `project_path`
		project_path = std::filesystem::current_path();

		bool likely_running_from_editor = std::filesystem::exists(project_path / ".godot")
			&& std::filesystem::exists(project_path / "project.godot");

		// `library_path`
		{
			// get the current extension library path
			String library_path_string{uninitialized};
			extension_interface::get_library_path(extension_interface::library,
				uninitialized(library_path_string));

			if(std::string(library_path_string).starts_with("res://")) {
				// XXX: this feels very brittle...
				// temporary solution until https://github.com/godotengine/godot/pull/94373 is merged
				if(likely_running_from_editor) {
					library_path = std::filesystem::absolute(std::filesystem::path(
							std::string(library_path_string).substr(std::string("res://").size())
						));
				}
				else {
					library_path = std::filesystem::absolute(
							project_path / std::filesystem::path(std::string(library_path_string)).filename()
						);
				}
			}
			else {
				library_path = std::filesystem::path(std::string(library_path_string));
			}
		}

		// `lib_dir_path`
		lib_dir_path = library_path.parent_path();

		// `python_home_path`
		if(likely_running_from_editor) {
			python_home_path = lib_dir_path;
		}
		else {
			auto platform_arch = std::string(PYGODOT_PLATFORM) + "-" + std::string(PYGODOT_ARCH);
			python_home_path = lib_dir_path / "lib" / platform_arch;
		}
	}
} runtime_config;


static bool init_python_isolated() {
#ifdef UNIX_ENABLED
	if(!promote_lib_to_global(PYTHON_LIBRARY_PATH)) {
		throw std::runtime_error("failed to promote lib \"" PYTHON_LIBRARY_PATH "\" to global");
	}
#endif

	if(Py_IsInitialized()) {
		throw std::runtime_error("python already initialized");
	}

	// gather paths
	runtime_config.init();

	// init python

	PyStatus status;

	auto check_status = [&](const std::string& what) {
		if(PyStatus_Exception(status)) {
			throw std::runtime_error(what + " failed: " + (status.err_msg ? status.err_msg : ""));
		}
	};

	PyPreConfig preconfig;
	PyPreConfig_InitIsolatedConfig(&preconfig);

	preconfig.utf8_mode = 1;

	status = Py_PreInitialize(&preconfig);
	check_status("python preinitialization");

	PyConfig config;
	PyConfig_InitIsolatedConfig(&config);

	config.parse_argv = 0;
	config.write_bytecode = 0;

	auto set_string = [&](auto& config_str, const std::string& name, const std::string& value) {
		status = PyConfig_SetBytesString(&config, &config_str, value.data());
		check_status("python initialization, setting " + name);
	};

	set_string(config.home, "home", runtime_config.python_home_path.string());

	set_string(config.base_prefix, "base_prefix", runtime_config.python_home_path.string());
	set_string(config.prefix, "prefix", runtime_config.python_home_path.string());

	set_string(config.base_exec_prefix, "base_exec_prefix", runtime_config.python_home_path.string());
	set_string(config.exec_prefix, "exec_prefix", runtime_config.python_home_path.string());

	set_string(config.base_executable, "base_executable", runtime_config.executable_path.string());
	set_string(config.executable, "executable", runtime_config.executable_path.string());

	set_string(config.program_name, "program_name", runtime_config.program_name);

	auto add_module_search_path = [&](const std::string& path) {
		wchar_t* wpath = Py_DecodeLocale(path.data(), nullptr);
		PyWideStringList_Append(&config.module_search_paths, wpath);
		PyMem_RawFree(wpath);
		check_status("python initialization, adding module search path");
	};

	auto py_major = std::to_string(PY_MAJOR_VERSION);
	auto py_minor = std::to_string(PY_MINOR_VERSION);
	auto py_version = py_major + "." + py_minor;
	auto py_version_no_dot = py_major + py_minor;
	auto python_zip_name = "python" + py_version_no_dot + ".zip";
	auto python_lib_name = "python" + py_version;

	add_module_search_path((runtime_config.python_home_path / python_zip_name).string());
	add_module_search_path((runtime_config.python_home_path / python_lib_name).string());
	add_module_search_path((runtime_config.python_home_path / python_lib_name / "lib-dynload").string());
	add_module_search_path((runtime_config.python_home_path / python_lib_name / "site-packages").string());

	config.module_search_paths_set = 1;

	if(runtime_config.argv.size()) {
		std::vector<char*> arg_ptrs;
		for(auto& arg : runtime_config.argv) {
			arg_ptrs.push_back(arg.data());
		}

		status = PyConfig_SetBytesArgv(&config, runtime_config.argv.size(), arg_ptrs.data());
		check_status("python initialization, setting argv");
	}

	status = Py_InitializeFromConfig(&config);
	check_status("python initialization");

	PyConfig_Clear(&config);

	return true;
}


static bool _init_godot_module() {
	if(!godot_module_archive_size) {
		return false;
	}

	static const char source[] =
#include "archive_importer_r_string.h"
	;

	static py::object ArchiveImporter;

	if(!ArchiveImporter) {
		py::dict ns;
		py::exec(source, ns, ns);
		ArchiveImporter = ns["ArchiveImporter"];
	}


	auto importer = ArchiveImporter(py::bytes(godot_module_archive_data, godot_module_archive_size),
		py::arg("name") = "godot.zip");

	py::module_::import("sys").attr("meta_path").attr("append")(importer);

	return true;
}


void initialize_python_module(void* userdata, GDExtensionInitializationLevel level) {
	if(level == GDEXTENSION_INITIALIZATION_CORE) {
		try {
			//printf("initializing interpreter...\n");

			init_python_isolated();

			//printf("interpreter initialized\n");

			released_gil = std::make_unique<py::gil_scoped_release>();
		}
		CATCH_FATAL_EXCEPTIONS_PRINT_ERRORS_AND_ABORT("During godot python module initialization")

		py::gil_scoped_acquire gil;

		try {
			initialization_level = level;

			const char* lib_dir = std::getenv("GODOT_PYTHON_MODULE_LIB_DIR");
			if(lib_dir && strlen(lib_dir) > 0) {
				auto sys = py::module_::import("sys");
				auto pathlib = py::module_::import("pathlib");

				if(!pathlib.attr("Path")(lib_dir).attr("joinpath")("godot").attr("is_dir")().cast<bool>()) {
					throw std::runtime_error(std::string("if set 'GODOT_PYTHON_MODULE_LIB_DIR' must be a directory containing the 'godot' python module, path '") + lib_dir + "' does not have a 'godot' subdirectory");
				}

				sys.attr("path").attr("insert")(0, lib_dir);
			}
			else {
				// embedded module
				if(!_init_godot_module()) {
					throw std::runtime_error("the 'godot' python module was not embedded, the environment variable 'GODOT_PYTHON_MODULE_LIB_DIR' must be set to a directory containing the 'godot' module");
				}
			}

			py::module_::import("_gdextension");
			py::module_::import("godot._internal");
		}
		CATCH_FATAL_EXCEPTIONS_PRINT_ERRORS_AND_ABORT("During godot python module initialization")
	}

	if(level >= GDEXTENSION_INITIALIZATION_CORE) {
		initialization_level = level;

		py::gil_scoped_acquire gil;
		try {
			py::module_::import("godot._internal").attr("initialize")(level);
		}
		CATCH_FATAL_EXCEPTIONS_PRINT_ERRORS_AND_ABORT()
	}
}


void uninitialize_python_module(void* userdata, GDExtensionInitializationLevel level) {
	if(level >= GDEXTENSION_INITIALIZATION_CORE) {
		py::gil_scoped_acquire gil;
		try {
			py::module_::import("godot._internal").attr("deinitialize")(level);
		}
		CATCH_FATAL_EXCEPTIONS_PRINT_ERRORS_AND_ABORT()

		initialization_level = level;
	}

	if(level == GDEXTENSION_INITIALIZATION_CORE) {
		released_gil.reset();

		for(auto& func : cleanup_functions) {
			func();
		}
		cleanup_functions.clear();

		//printf("finalizing interpreter...\n");

		py::finalize_interpreter();

		//printf("interpreter finalized\n");

		initialization_level.reset();
	}
}


} // namespace pygodot


extern "C" PYBIND11_EXPORT GDExtensionBool python_extension_init(
	GDExtensionInterfaceGetProcAddress get_proc_address,
	GDExtensionClassLibraryPtr library,
	GDExtensionInitialization* initialization)
{
	using namespace pygodot;

	auto* raw_interface = reinterpret_cast<uint32_t*>(get_proc_address);
	if(raw_interface[0] == 4 && raw_interface[1] == 0) {
		printf("ERROR: Cannot load a GDExtension built for Godot 4.1+ in legacy Godot 4.0 mode.\n");
		return false;
	}

	extension_interface::print_error =
		reinterpret_cast<GDExtensionInterfacePrintError>(get_proc_address("print_error"));

	if(!extension_interface::print_error) {
		printf("ERROR: Unable to load GDExtension interface function print_error()\n");
		return false;
	}

	extension_interface::library = library;
	extension_interface::token = library;


	// TODO: work this into the build system

	// grep -r -h -o --color=no -E '\bextension_interface::\w+' ./src/ | sort | uniq | sed -E 's/\w+::(\w+)/\t\t"\1",/g'

	std::vector<std::string> referenced_extension_apis = {
		"callable_custom_create",
		"callable_custom_get_userdata",
		"classdb_construct_object",
		"classdb_get_method_bind",
		"classdb_register_extension_class",
		"classdb_register_extension_class_integer_constant",
		"classdb_register_extension_class_method",
		"classdb_register_extension_class_property",
		"classdb_register_extension_class_property_group",
		"classdb_register_extension_class_property_subgroup",
		"classdb_register_extension_class_signal",
		"get_godot_version",
		"get_library_path",
		"get_variant_from_type_constructor",
		"get_variant_to_type_constructor",
		"global_get_singleton",
		"godot_version",
		"library",
		"name",
		"object_destroy",
		"object_get_class_name",
		"object_get_instance_binding",
		"object_get_instance_id",
		"object_method_bind_ptrcall",
		"object_set_instance",
		"object_set_instance_binding",
		"packed_byte_array_operator_index_const",
		"placeholder_script_instance_create",
		"placeholder_script_instance_update",
		"print_error",
		"print_warning",
		"ref_set_object",
		"script_instance_create",
		"string_new_with_utf8_chars",
		"string_new_with_utf8_chars_and_len",
		"string_to_utf8_chars",
		"token",
		"variant_call",
		"variant_destroy",
		"variant_get_ptr_builtin_method",
		"variant_get_ptr_constructor",
		"variant_get_ptr_destructor",
		"variant_get_ptr_getter",
		"variant_get_ptr_indexed_getter",
		"variant_get_ptr_indexed_setter",
		"variant_get_ptr_keyed_getter",
		"variant_get_ptr_keyed_setter",
		"variant_get_ptr_operator_evaluator",
		"variant_get_ptr_setter",
		"variant_get_ptr_utility_function",
		"variant_get_type",
		"variant_new_nil",
		"variant_stringify"
	};


#define GDEXTENSION_API(name, type) \
	if(std::find(referenced_extension_apis.begin(), referenced_extension_apis.end(), #name) \
		!= referenced_extension_apis.end()) \
	{ \
		extension_interface::name = reinterpret_cast<type>(get_proc_address(#name)); \
		if(!extension_interface::name) { \
			extension_interface::print_error("Unable to load GDExtension interface function " #name "()", \
				__FUNCTION__, __FILE__, __LINE__, false); \
			return false; \
		} \
	} \
	else { \
		extension_interface::name = reinterpret_cast<type>(static_cast<void(*)()>([]() { \
			extension_interface::print_error("Cannot call unloaded GDExtension interface function " #name "()", \
				__FUNCTION__, __FILE__, __LINE__, false); \
			std::fflush(stdout); \
			std::abort(); \
		})); \
	}

	GDEXTENSION_APIS

#undef GDEXTENSION_API

	extension_interface::get_godot_version(&extension_interface::godot_version);

	GDExtensionGodotVersion minium_version = {.major = 4, .minor = 2, .patch = 0, .string = nullptr};

	if(version_to_uint(extension_interface::godot_version) < version_to_uint(minium_version)) {
		char error_msg[256];
		snprintf(error_msg, sizeof(error_msg),
			"Minimum required version for Python extension not met. Need v%d.%d.%d or newer, have v%d.%d.%d\n",
			minium_version.major, minium_version.minor, minium_version.patch,
			extension_interface::godot_version.major,
			extension_interface::godot_version.minor,
			extension_interface::godot_version.patch
		);

		extension_interface::print_error(error_msg, __FUNCTION__, __FILE__, __LINE__, false);

		return false;
	}

	initialization->initialize = initialize_python_module;
	initialization->deinitialize = uninitialize_python_module;
	initialization->minimum_initialization_level = GDEXTENSION_INITIALIZATION_CORE;

	return true;
}


