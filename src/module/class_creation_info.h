#pragma once

#include <pybind11/pybind11.h>

#include "extension/extension.h"


namespace pygodot {


namespace py = pybind11;


class PyGDExtensionClassCreationInfo {
public:
	GDExtensionBool is_virtual;
	GDExtensionBool is_abstract;
	nullable_py_function set_func;
	nullable_py_function get_func;
	nullable_py_function get_property_list_func;
	nullable_py_function free_property_list_func;
	nullable_py_function property_can_revert_func;
	nullable_py_function property_get_revert_func;
	nullable_py_function notification_func;
	nullable_py_function to_string_func;
	nullable_py_function reference_func;
	nullable_py_function unreference_func;
	nullable_py_function create_instance_func;
	nullable_py_function free_instance_func;
	nullable_py_function get_virtual_func;
	nullable_py_function get_rid_func;
	py::object class_userdata = py::none();

	static void def(py::module_& module_);

	operator GDExtensionClassCreationInfo();
};


} // namespace pygodot


