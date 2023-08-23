#pragma once

#include <pybind11/pybind11.h>

#include "extension/extension.h"
#include "module/property_info.h"
#include "module/class_method_info.h"
#include "util/python_utils.h"


namespace pygodot {


using variant_ptr_to_python_obj_cast_info_t = py::handle;
using variant_type_ptr_to_python_obj_cast_info_t = std::pair<GDExtensionVariantType, py::handle>;


inline auto get_cast_info(const std::optional<PyGDExtensionPropertyInfo>& property_info) {
	variant_type_ptr_to_python_obj_cast_info_t info;

	if(!property_info) {
		info.first = GDEXTENSION_VARIANT_TYPE_NIL;
		return info;
	}

	info.first = property_info->type;

	if(property_info->python_type && !property_info->python_type.is_none()) {
		info.second = property_info->python_type;
	}

	return info;
}


inline auto get_arguments_cast_info(const PyGDExtensionClassMethodInfo& method_info) {
	std::vector<variant_type_ptr_to_python_obj_cast_info_t> info;

	for(const auto& argument_info : method_info.arguments_info) {
		info.emplace_back(get_cast_info(argument_info));
	}

	return info;
}


inline auto get_return_cast_info(const PyGDExtensionClassMethodInfo& method_info) {
	return get_cast_info(method_info.return_value_info);
}


} // namespace pygodot



