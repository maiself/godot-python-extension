#include "extension/extension.h"
#include "module/property_info.h"
#include "util/garbage_collection_type_setup.h"


namespace pygodot {


void PyGDExtensionPropertyInfo::def(py::module_& module_) {
	using type = PyGDExtensionPropertyInfo;

	py::class_<type>(module_, "GDExtensionPropertyInfo"//,
		/*py::custom_type_setup(garbage_collection_type_setup<type>()
			//.collect(&type::python_type)
		*/
	)
		.def(py::init())
		.def_readwrite("type", &type::type)
		.def_readwrite("name", &type::name)
		.def_readwrite("class_name", &type::class_name)
		.def_readwrite("hint", &type::hint)
		.def_readwrite("hint_string", &type::hint_string)
		.def_readwrite("usage", &type::usage)

		.def_readwrite("python_type", &type::python_type)
	;
}

PyGDExtensionPropertyInfo::operator GDExtensionPropertyInfo() {
	GDExtensionPropertyInfo property_info = {
		.type = type,
		.name = name,
		.class_name = class_name,
		.hint = hint,
		.hint_string = hint_string,
		.usage = usage,
	};

	return property_info;
}


} // namespace pygodot


