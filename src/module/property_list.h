#pragma once

#include <pybind11/pybind11.h>

#include "module/property_info.h"


namespace pygodot {


class PropertyList {
	py::object _original_prop_sequence;
	py::list _prop_info_list;
	std::unique_ptr<GDExtensionPropertyInfo[]> _list_ptr;

public:
	PropertyList(py::object prop_sequence);

	static PropertyList* get_from_pointer(const GDExtensionPropertyInfo* list_ptr);
	operator const GDExtensionPropertyInfo*() const;

	size_t size() const;
	operator py::object() const;
};


} // namespace pygodot


