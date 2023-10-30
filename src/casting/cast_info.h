#pragma once

#include <pybind11/pybind11.h>

#include "extension/extension.h"
#include "module/property_info.h"
#include "module/class_method_info.h"
#include "util/python_utils.h"


namespace pygodot {


struct cast_info_t {
	GDExtensionVariantType variant_type;
	py::handle python_type;
	bool is_derived_type;
};


inline auto get_cast_info(const std::optional<PyGDExtensionPropertyInfo>& property_info) {
	cast_info_t info;

	if(!property_info) {
		info.variant_type = GDEXTENSION_VARIANT_TYPE_NIL;
		return info;
	}

	info.variant_type = property_info->type;

	if(property_info->python_type && !property_info->python_type.is_none()) {
		info.python_type = property_info->python_type;
	}

	if(property_info->type == GDEXTENSION_VARIANT_TYPE_OBJECT) {
		info.is_derived_type = (std::string(property_info->class_name) != "Object");
	}

	return info;
}


inline auto get_arguments_cast_info(const PyGDExtensionClassMethodInfo& method_info) {
	std::vector<cast_info_t> info;

	for(const auto& argument_info : method_info.arguments_info) {
		info.emplace_back(get_cast_info(argument_info));
	}

	return info;
}


inline auto get_return_cast_info(const PyGDExtensionClassMethodInfo& method_info) {
	return get_cast_info(method_info.return_value_info);
}


} // namespace pygodot



