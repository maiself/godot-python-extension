#include <pybind11/stl.h>

#include "extension/extension.h"
#include "util/exceptions.h"
#include "module/class_method_info.h"
#include "casting/cast_args.h"
#include "util/garbage_collection_type_setup.h"


namespace pygodot {


namespace py = pybind11;


class PyGDExtensionClassMethodInfo::CachedData {
public:
	std::vector<GDExtensionPropertyInfo> method_arguments_info;
	std::unique_ptr<cast_t<py::args>> method_default_arguments; // XXX
	GDExtensionPropertyInfo method_return_value_info;
};


void PyGDExtensionClassMethodInfo::def(py::module_& module_) {
	using type = PyGDExtensionClassMethodInfo;

	py::class_<type>(module_, "GDExtensionClassMethodInfo",
		py::custom_type_setup(garbage_collection_type_setup<type>()
			.collect(&type::method_userdata)
			.collect(&type::call_func)
			//.collect(&type::ptrcall_func)
		)
	)
		.def(py::init())
		.def_readwrite("name", &type::name)
		.def_readwrite("method_userdata", &type::method_userdata)
		.def_readwrite("call_func", &type::call_func)
		//.def_readwrite("ptrcall_func", &type::ptrcall_func)
		.def_readwrite("method_flags", &type::method_flags)

		.def_readwrite("return_value_info", &type::return_value_info)
		.def_readwrite("return_value_metadata", &type::return_value_metadata)

		.def_readwrite("arguments_info", &type::arguments_info)
		.def_readwrite("arguments_metadata", &type::arguments_metadata)

		.def_readwrite("default_arguments", &type::default_arguments)
	;
}


PyGDExtensionClassMethodInfo::operator GDExtensionClassMethodInfo() {
	_cached_data = std::make_unique<decltype(_cached_data)::element_type>();

	for(auto& argument_info : arguments_info) {
		_cached_data->method_arguments_info.push_back(argument_info);
	}

	{
		py::args defaults(py::tuple{default_arguments.size()});

		for(size_t i = 0; i < default_arguments.size(); i++) {
			defaults[i] = default_arguments[i];
		}

		_cached_data->method_default_arguments =
			std::make_unique<decltype(_cached_data->method_default_arguments)::element_type>(defaults);
	}

	auto* default_arguments_ptr = const_cast<GDExtensionVariantPtr*>(
		static_cast<GDExtensionConstVariantPtr*>(*_cached_data->method_default_arguments));

	if(return_value_info) {
		_cached_data->method_return_value_info = *return_value_info;
	}

	GDExtensionClassMethodInfo method_info = {
		.name = name,
		.method_userdata = reinterpret_cast<void*>(this),

		.call_func = [](
			void *method_userdata, GDExtensionClassInstancePtr instance,
			const GDExtensionConstVariantPtr* args, GDExtensionInt argument_count,
			GDExtensionVariantPtr res, GDExtensionCallError* error)
		{
			auto& method_info = *reinterpret_cast<PyGDExtensionClassMethodInfo*>(method_userdata);

			py::gil_scoped_acquire gil;

			if(error) {
				error->error = GDEXTENSION_CALL_OK; // XXX
			}

			try {
				if(method_info.method_flags & GDEXTENSION_METHOD_FLAG_STATIC) {
					cast(res)
						= method_info.call_func(*cast(args, argument_count)); // XXX: cast info
				}
				else {
					py::object self = py::cast(reinterpret_cast<Object*>(instance));
					cast(res)
						= method_info.call_func(self, *cast(args, argument_count)); // XXX: cast info
				}
				return;
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS(
				"While calling: " + get_fully_qualified_name(method_info.call_func))

			//cast(res, get_return_cast_info(method_info)) = py::object(); // XXX

			if(error) {
				error->error = GDEXTENSION_CALL_ERROR_INVALID_METHOD; // XXX
			}
		},

		.ptrcall_func = [](
			void *method_userdata, GDExtensionClassInstancePtr p_instance,
			const GDExtensionConstTypePtr *args, GDExtensionTypePtr res)
		{
			auto& method_info = *reinterpret_cast<PyGDExtensionClassMethodInfo*>(method_userdata);

			py::gil_scoped_acquire gil;

			try {
				if(method_info.method_flags & GDEXTENSION_METHOD_FLAG_STATIC) {
					cast(res, get_return_cast_info(method_info)) // XXX: cache
						= method_info.call_func(*cast(args, get_arguments_cast_info(method_info)));
				}
				else {
					py::object self = py::cast(reinterpret_cast<Object*>(p_instance));
					cast(res, get_return_cast_info(method_info)) // XXX: cache
						= method_info.call_func(self, *cast(args, get_arguments_cast_info(method_info)));
				}
				return;
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS(
				"While calling: " + get_fully_qualified_name(method_info.call_func))

			cast(res, get_return_cast_info(method_info)) = py::object(); // XXX
		},

		.method_flags = static_cast<uint32_t>(method_flags),

		.has_return_value = return_value_info.has_value(),
		.return_value_info = &_cached_data->method_return_value_info,
		.return_value_metadata = return_value_metadata,

		.argument_count = static_cast<uint32_t>(_cached_data->method_arguments_info.size()),
		.arguments_info = _cached_data->method_arguments_info.data(),
		.arguments_metadata = arguments_metadata.data(),

		.default_argument_count = static_cast<uint32_t>(default_arguments.size()),
		.default_arguments = default_arguments_ptr,
	};

	return method_info;
}


} // namespace pygodot


