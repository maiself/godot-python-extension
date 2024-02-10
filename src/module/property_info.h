#pragma once

#include <pybind11/pybind11.h>

#include "extension/extension.h"
#include "variant/string.h"
#include "variant/string_name.h"


namespace pygodot {


namespace py = pybind11;
	

class PyGDExtensionPropertyInfo {
public:
	GDExtensionVariantType type;
	StringName name;
	StringName class_name;
	uint32_t hint; // PropertyHint
	String hint_string;
	uint32_t usage; // PropertyUsageFlags

	py::handle python_type = py::none().release(); // XXX: handle?

	static void def(py::module_& module_);

	operator GDExtensionPropertyInfo();
};


} // namespace pygodot


