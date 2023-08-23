#pragma once

#include <pybind11/pybind11.h>

#include "extension/extension.h"


namespace pygodot {


namespace py = pybind11;


class PyGDExtensionClassCreationInfo {
public:
	GDExtensionBool is_virtual;
	GDExtensionBool is_abstract;
	py::function set_func;
	py::function get_func;
	py::function get_property_list_func;
	py::function free_property_list_func;
	py::function property_can_revert_func;
	py::function property_get_revert_func;
	py::function notification_func;
	py::function to_string_func;
	py::function reference_func;
	py::function unreference_func;
	py::function create_instance_func;
	py::function free_instance_func;
	py::function get_virtual_func;
	py::function get_rid_func;
	py::object class_userdata;

	static void def(py::module_& module_);

	operator GDExtensionClassCreationInfo();
};


} // namespace pygodot


