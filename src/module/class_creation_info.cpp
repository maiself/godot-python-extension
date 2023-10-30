#include "extension/extension.h"
#include "util/exceptions.h"
#include "module/class_creation_info.h"
#include "module/class_method_info.h"
#include "module/property_list.h"
#include "util/garbage_collection_type_setup.h"


#include "variant/string_name.h"
#include "casting/cast_args.h"


#include <pybind11/stl.h>


#ifndef CLASS_VIRTUAL_CALL_TABLE_SIZE
#define CLASS_VIRTUAL_CALL_TABLE_SIZE 1024
#endif


namespace std {
	template<>
	struct hash<std::pair<PyObject*, size_t>> {
		size_t operator()(const auto& p) const {
			return std::hash<PyObject*>{}(p.first) ^ std::hash<size_t>{}(p.second);
		}
	};
}


namespace pygodot {


static std::unordered_map<PyObject*, size_t> _num_virt_funcs;
static std::unordered_map<std::pair<PyObject*, size_t>, py::function> _virt_funcs;
static std::unordered_map<std::pair<PyObject*, size_t>, std::reference_wrapper<PyGDExtensionClassMethodInfo>> _virt_funcs_info;


void call_virtual(size_t index,
	GDExtensionClassInstancePtr instance,
	const GDExtensionConstTypePtr* args,
	GDExtensionTypePtr ret)
{
	py::gil_scoped_acquire gil;

	py::handle func;

	try {
		py::object self = py::cast(reinterpret_cast<Object*>(instance));
		PyObject* type = py::type::handle_of(self).ptr();

		func = _virt_funcs[{type, index}];
		auto& method_info = _virt_funcs_info.at({type, index}).get();

		//py::print(method_info.name, func, method_info.return_type(), method_info.argument_types());

		try {
			func = py::type::handle_of(self).attr(func.attr("__name__")); // XXX: need this for reloaded...

			cast(ret, get_return_cast_info(method_info)) // XXX
				= func(self, *cast(args, get_arguments_cast_info(method_info)));
		}
		catch(...) {
			cast(ret, get_return_cast_info(method_info)) = py::object();
			throw;
		}
	}
	CATCH_EXCEPTIONS_AND_PRINT_ERRORS([func]() {
		return py::str("While calling: ") + (func
			? py::str(get_fully_qualified_name(func))
			: py::str("unknown vertual method")
		);
	})
}


template<size_t... Is>
consteval auto generate_call_virtuals(std::index_sequence<Is...> seq) {
	return std::array<GDExtensionClassCallVirtual, seq.size()>({
		[](GDExtensionClassInstancePtr instance,
			const GDExtensionConstTypePtr* args,
			GDExtensionTypePtr ret)
		{
			call_virtual(Is, instance, args, ret);
		}
		...
	});
}


template<size_t N = CLASS_VIRTUAL_CALL_TABLE_SIZE>
consteval auto generate_call_virtuals() {
	return generate_call_virtuals(std::make_index_sequence<N>{});
}


static constexpr auto call_virtuals = generate_call_virtuals();


void PyGDExtensionClassCreationInfo::def(py::module_& module_) {
	using type = PyGDExtensionClassCreationInfo;

	py::class_<type>(module_, "GDExtensionClassCreationInfo",
		py::custom_type_setup(garbage_collection_type_setup<type>()
			.collect(&type::set_func)
			.collect(&type::get_func)

			.collect(&type::get_property_list_func)
			.collect(&type::free_property_list_func)

			.collect(&type::property_can_revert_func)
			.collect(&type::property_get_revert_func)

			.collect(&type::notification_func)
			.collect(&type::to_string_func)

			.collect(&type::reference_func)
			.collect(&type::unreference_func)

			.collect(&type::create_instance_func)
			.collect(&type::free_instance_func)
			.collect(&type::get_virtual_func)

			.collect(&type::get_rid_func)
			.collect(&type::class_userdata)
		)
	)
		.def(py::init())
		.def_readwrite("is_virtual", &type::is_virtual)
		.def_readwrite("is_abstract", &type::is_abstract)
		.def_readwrite("set_func", &type::set_func)
		.def_readwrite("get_func", &type::get_func)
		.def_readwrite("get_property_list_func", &type::get_property_list_func)
		.def_readwrite("free_property_list_func", &type::free_property_list_func)
		.def_readwrite("property_can_revert_func", &type::property_can_revert_func)
		.def_readwrite("property_get_revert_func", &type::property_get_revert_func)
		.def_readwrite("notification_func", &type::notification_func)
		.def_readwrite("to_string_func", &type::to_string_func)
		.def_readwrite("reference_func", &type::reference_func)
		.def_readwrite("unreference_func", &type::unreference_func)
		.def_readwrite("create_instance_func", &type::create_instance_func)
		.def_readwrite("free_instance_func", &type::free_instance_func)
		.def_readwrite("get_virtual_func", &type::get_virtual_func)
		.def_readwrite("get_rid_func", &type::get_rid_func)
		.def_readwrite("class_userdata", &type::class_userdata)
	;
}

static auto* _get_extension_class_from_instance(py::object self) {
	py::object info = resolve_name("godot._internal.extension_classes._registered_class_infos")[
		py::type::of(self).attr("_extension_class").attr("__name__")]; // XXX
	return py::cast<PyGDExtensionClassCreationInfo*>(info);
}


PyGDExtensionClassCreationInfo::operator GDExtensionClassCreationInfo() {
	GDExtensionClassCreationInfo class_info = {
		.is_virtual = is_virtual,
		.is_abstract = is_abstract,

		.set_func = [](
			GDExtensionClassInstancePtr p_instance, GDExtensionConstStringNamePtr p_name,
			GDExtensionConstVariantPtr p_value) -> GDExtensionBool
		{
			py::gil_scoped_acquire gil;
			try {
				try {
					py::object self = py::cast(reinterpret_cast<Object*>(p_instance));
					auto info = _get_extension_class_from_instance(self);

					auto res = info->set_func(self, cast(p_name), cast(p_value)).cast<py::bool_>();
					return static_cast<bool>(res);
				}
				catch(const py::error_already_set& exception) {
					if(!exception.matches(PyExc_AttributeError)) {
						throw;
					}
				}
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
			return false;
		},

		.get_func = [](
			GDExtensionClassInstancePtr instance, GDExtensionConstStringNamePtr name,
			GDExtensionVariantPtr ret) -> GDExtensionBool
		{
			py::gil_scoped_acquire gil;
			try {
				try {
					py::object self = py::cast(reinterpret_cast<Object*>(instance));
					auto info = _get_extension_class_from_instance(self);

					cast(ret) = info->get_func(self, cast(name));
					return true;
				}
				catch(const py::error_already_set& exception) {
					if(!exception.matches(PyExc_AttributeError)) {
						throw;
					}
				}
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
			return false;
		},

		.get_property_list_func = [](GDExtensionClassInstancePtr p_instance, uint32_t *r_count) -> const GDExtensionPropertyInfo *
		{
			py::gil_scoped_acquire gil;

			try {
				py::object self = py::cast(reinterpret_cast<Object*>(p_instance));
				auto info = _get_extension_class_from_instance(self);

				auto prop_list = std::make_unique<PropertyList>(info->get_property_list_func(self));

				*r_count = prop_list->size();
				return *prop_list.release();
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()

			*r_count = 0;
			return nullptr;
		},

		.free_property_list_func = [](GDExtensionClassInstancePtr p_instance, const GDExtensionPropertyInfo *p_list) -> void
		{
			py::gil_scoped_acquire gil;

			try {
				std::unique_ptr<PropertyList> prop_list(PropertyList::get_from_pointer(p_list));
				if(!prop_list) {
					return;
				}

				py::object self = py::cast(reinterpret_cast<Object*>(p_instance));
				auto info = _get_extension_class_from_instance(self);

				info->free_property_list_func(self, py::object(*prop_list));
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
		},


		.property_can_revert_func = [](
			GDExtensionClassInstancePtr p_instance, GDExtensionConstStringNamePtr p_name) -> GDExtensionBool
		{
			py::gil_scoped_acquire gil;
			try {
				try {
					py::object self = py::cast(reinterpret_cast<Object*>(p_instance));
					auto info = _get_extension_class_from_instance(self);

					auto res = info->property_can_revert_func(self, cast(p_name)).cast<py::bool_>();
					return static_cast<bool>(res);
				}
				catch(const py::error_already_set& exception) {
					if(!exception.matches(PyExc_AttributeError)) {
						throw;
					}
				}
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
			return false;
		},

		.property_get_revert_func = [](
			GDExtensionClassInstancePtr p_instance, GDExtensionConstStringNamePtr p_name,
			GDExtensionVariantPtr r_ret) -> GDExtensionBool
		{
			py::gil_scoped_acquire gil;
			try {
				try {
					py::object self = py::cast(reinterpret_cast<Object*>(p_instance));
					auto info = _get_extension_class_from_instance(self);

					cast(r_ret) = info->property_get_revert_func(self, cast(p_name));
					return true;
				}
				catch(const py::error_already_set& exception) {
					if(!exception.matches(PyExc_AttributeError)) {
						throw;
					}
				}
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
			return false;
		},

		.notification_func = [](GDExtensionClassInstancePtr p_instance, int32_t p_what)
		{
			py::gil_scoped_acquire gil;
			//printf("# notification_func %d\n", p_what);
		},

		.to_string_func = [](
			GDExtensionClassInstancePtr p_instance, GDExtensionBool *r_is_valid, GDExtensionStringPtr p_out)
		{
			py::gil_scoped_acquire gil;
			//printf("# to_string_func\n");
		},

		.reference_func = [](GDExtensionClassInstancePtr p_instance)
		{
			py::gil_scoped_acquire gil;
			//printf("# reference_func\n");
		},

		.unreference_func = [](GDExtensionClassInstancePtr p_instance)
		{
			py::gil_scoped_acquire gil;
			//printf("# unreference_func\n");
		},

		.create_instance_func = [](void* userdata) -> GDExtensionObjectPtr
		{
			py::gil_scoped_acquire gil;

			try {
				//printf("# create_instance_func\n");

				auto& self = *reinterpret_cast<PyGDExtensionClassCreationInfo*>(userdata);

				return py::cast<Object&>(self.create_instance_func());

			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS(/*[func]() {
				return py::str("While calling: ") + (func
					? py::str(get_fully_qualified_name(func))
					: py::str("unknown vertual method")
				);
			}*/)

			return nullptr;
		},

		.free_instance_func = [](void* userdata, GDExtensionClassInstancePtr instance) -> void
		{
			py::gil_scoped_acquire gil;
			//printf("# free_instance_func\n");
			return;
		},

		.get_virtual_func = [](void* userdata, GDExtensionConstStringNamePtr name) -> GDExtensionClassCallVirtual
		{
			auto& self = *reinterpret_cast<PyGDExtensionClassCreationInfo*>(userdata);

			py::gil_scoped_acquire gil;

			try {
				py::str name_str = cast(name);

				//printf("# get_virtual_func %s %s\n",
				//	get_fully_qualified_name(self.class_userdata).data(), std::string(name_str).data());

				if(!self.get_virtual_func) {
					return nullptr;
				}

				py::object func = self.get_virtual_func(name_str);

				if(!func || func.is_none()) {
					return nullptr;
				}

				py::handle cls = self.class_userdata;
				auto& num_virt_funcs = _num_virt_funcs[cls.ptr()];

				if(num_virt_funcs >= call_virtuals.size()) {
					//try {
						py::handle cls = self.class_userdata;
						throw std::runtime_error(
							"all virtual call jump functions consumed for type '"
							+ get_fully_qualified_name(cls) + "'"
						);
					//}
					// XXX: CATCH_FATAL_EXCEPTIONS_PRINT_ERRORS_AND_ABORT() ?
				}

				_virt_funcs[{cls.ptr(), num_virt_funcs}] = func;

				// XXX
				py::handle method_info = resolve_name("godot._internal.utils.get_method_info")(cls, name_str);

				if(!method_info || method_info.is_none()) {
					printf("get virtual %s %s failed\n",
						get_fully_qualified_name(self.class_userdata).data(), std::string(name_str).data());
					return nullptr;
				}

				_virt_funcs_info.insert({{cls.ptr(), num_virt_funcs},
					py::cast<PyGDExtensionClassMethodInfo&>(method_info)});

				return call_virtuals[num_virt_funcs++];
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
			return nullptr;
		},

		.get_rid_func = [](GDExtensionClassInstancePtr p_instance) -> uint64_t
		{
			py::gil_scoped_acquire gil;
			//printf("# get_rid_func\n");
			return 0;
		},

		.class_userdata = this,
	};

	return class_info;
}


} // namespace pygodot


