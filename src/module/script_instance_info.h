#pragma once

#include <pybind11/pybind11.h>

#include "extension/extension.h"
#include "variant/object.h"


namespace pygodot {


namespace py = pybind11;


class PyGDExtensionScriptInstanceInfo {
public:
	py::function set_func;
	py::function get_func;
	py::function get_property_list_func;
	py::function free_property_list_func;

	py::function property_can_revert_func;
	py::function property_get_revert_func;

	py::function get_owner_func;
	py::function get_property_state_func;

	py::function get_method_list_func;
	py::function free_method_list_func;
	py::function get_property_type_func;

	py::function has_method_func;

	py::function call_func;
	py::function notification_func;

	py::function to_string_func;

	py::function refcount_incremented_func;
	py::function refcount_decremented_func;

	py::function get_script_func;

	py::function is_placeholder_func;

	py::function set_fallback_func;
	py::function get_fallback_func;

	py::function get_language_func;

	py::function free_func;

	static void def(py::module_& module_);

	operator const GDExtensionScriptInstanceInfo&() const;
	operator const GDExtensionScriptInstanceInfo*() const;
};


py::int_ script_instance_create(std::shared_ptr<const PyGDExtensionScriptInstanceInfo> info,
	py::object instance);
py::int_ placeholder_script_instance_create(Object* language, Object* script, Object* owner);



} // namespace pygodot


