#include <array>
#include <string>
#include <cstdio>
#include <cstring>
#include <format>

#ifdef UNIX_ENABLED
#include <dlfcn.h>
#endif

#include <pybind11/embed.h>


#include "extension/extension.h"
#include "util/exceptions.h"
#include "variant/string.h"


namespace pygodot {


namespace py = pybind11;


extern const char* godot_module_archive_data;
extern const size_t godot_module_archive_size;


static std::unique_ptr<py::gil_scoped_release> released_gil;


static std::vector<std::function<void()>> cleanup_functions;

void register_cleanup_func(std::function<void()> func) {
	cleanup_functions.push_back(func);
}


#ifdef UNIX_ENABLED

static bool promote_lib_to_global(const char* path) {
	if(void* lib = dlopen(path, RTLD_GLOBAL | RTLD_NOW | RTLD_NOLOAD)) {
		dlclose(lib);
		return true;
	}
	else if(const char* err = dlerror()) {
		printf("error promoting %s to RTLD_GLOBAL via dlopen: %s\n", path, err);
	}
	return false;
}

#endif


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
#ifdef UNIX_ENABLED
		promote_lib_to_global(PYTHON_LIBRARY_PATH);
#endif

		//printf("initializing interpreter...\n");

		py::initialize_interpreter();

		//printf("interpreter initialized\n");

		released_gil = std::make_unique<py::gil_scoped_release>();

		py::gil_scoped_acquire gil;

		initialization_level = level;

		try {
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

#define GDEXTENSION_API(name, type) \
	extension_interface::name = reinterpret_cast<type>(get_proc_address(#name)); \
	if(!extension_interface::name) { \
		extension_interface::print_error("Unable to load GDExtension interface function " #name "()", \
			__FUNCTION__, __FILE__, __LINE__, false); \
		return false; \
	}

	GDEXTENSION_APIS

#undef GDEXTENSION_API

	extension_interface::get_godot_version(&extension_interface::godot_version);

	GDExtensionGodotVersion minium_version = {.major = 4, .minor = 2, .patch = 0, .string = nullptr};

	auto version_to_uint = [](const GDExtensionGodotVersion& version) -> uint32_t {
		return (version.major << 16) + (version.minor << 8) + version.patch;
	};

	if(version_to_uint(extension_interface::godot_version) < version_to_uint(minium_version)) {
		auto error_msg = std::format(
			"Minimum required version for Python extension not met. Need v{}.{}.{} or newer, have v{}.{}.{}\n",
			minium_version.major, minium_version.minor, minium_version.patch,
			extension_interface::godot_version.major,
			extension_interface::godot_version.minor,
			extension_interface::godot_version.patch
		);

		extension_interface::print_error(error_msg.data(), __FUNCTION__, __FILE__, __LINE__, false);

		return false;
	}

	initialization->initialize = initialize_python_module;
	initialization->deinitialize = uninitialize_python_module;
	initialization->minimum_initialization_level = GDEXTENSION_INITIALIZATION_CORE;

	return true;
}


