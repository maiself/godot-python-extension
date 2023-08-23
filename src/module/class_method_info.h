#pragma once

#include <vector>

#include <pybind11/pybind11.h>

#include "extension/extension.h"
#include "module/property_info.h"
#include "variant/string_name.h"


namespace pygodot {


namespace py = pybind11;
	

class PyGDExtensionClassMethodInfo {
	class CachedData;

	std::unique_ptr<CachedData> _cached_data;

public:
	StringName name;
	py::object method_userdata;

	py::function call_func;
	//py::function ptrcall_func; // not used

	GDExtensionClassMethodFlags method_flags;

	std::optional<PyGDExtensionPropertyInfo> return_value_info;
	GDExtensionClassMethodArgumentMetadata return_value_metadata;

	std::vector<PyGDExtensionPropertyInfo> arguments_info;
	std::vector<GDExtensionClassMethodArgumentMetadata> arguments_metadata;

	std::vector<py::object> default_arguments;

	static void def(py::module_& module_);

	operator GDExtensionClassMethodInfo();
};


} // namespace pygodot


