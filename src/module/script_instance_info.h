#pragma once

#include <pybind11/pybind11.h>

#include "extension/extension.h"
#include "variant/object.h"


namespace pygodot {


namespace py = pybind11;


class PyGDExtensionScriptInstanceInfo {
public:
	nullable_py_function set_func;
	nullable_py_function get_func;
	nullable_py_function get_property_list_func;
	nullable_py_function free_property_list_func;

	nullable_py_function property_can_revert_func;
	nullable_py_function property_get_revert_func;

	nullable_py_function get_owner_func;
	nullable_py_function get_property_state_func;

	nullable_py_function get_method_list_func;
	nullable_py_function free_method_list_func;
	nullable_py_function get_property_type_func;

	nullable_py_function has_method_func;

	nullable_py_function call_func;
	nullable_py_function notification_func;

	nullable_py_function to_string_func;

	nullable_py_function refcount_incremented_func;
	nullable_py_function refcount_decremented_func;

	nullable_py_function get_script_func;

	nullable_py_function is_placeholder_func;

	nullable_py_function set_fallback_func;
	nullable_py_function get_fallback_func;

	nullable_py_function get_language_func;

	nullable_py_function free_func;

	static void def(py::module_& module_);

	operator const GDExtensionScriptInstanceInfo&() const;
	operator const GDExtensionScriptInstanceInfo*() const;
};


py::int_ script_instance_create(std::shared_ptr<const PyGDExtensionScriptInstanceInfo> info,
	py::object instance);
py::int_ placeholder_script_instance_create(Object* language, Object* script, Object* owner);



} // namespace pygodot


