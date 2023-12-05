#include "extension/extension.h"
#include "util/exceptions.h"
#include "module/script_instance_info.h"
#include "module/property_list.h"
#include "util/garbage_collection_type_setup.h"

#include "variant/string_name.h"
#include "casting/cast_args.h"


namespace pygodot {


void PyGDExtensionScriptInstanceInfo::def(py::module_& module_) {
	using type = PyGDExtensionScriptInstanceInfo;

	py::class_<type, std::shared_ptr<type>>(module_, "GDExtensionScriptInstanceInfo",
		py::custom_type_setup(garbage_collection_type_setup<type>()
			.collect(&type::set_func)
			.collect(&type::get_func)
			.collect(&type::get_property_list_func)
			.collect(&type::free_property_list_func)

			.collect(&type::property_can_revert_func)
			.collect(&type::property_get_revert_func)

			.collect(&type::get_owner_func)
			.collect(&type::get_property_state_func)

			.collect(&type::get_method_list_func)
			.collect(&type::free_method_list_func)
			.collect(&type::get_property_type_func)

			.collect(&type::has_method_func)

			.collect(&type::call_func)
			.collect(&type::notification_func)

			.collect(&type::to_string_func)

			.collect(&type::refcount_incremented_func)
			.collect(&type::refcount_decremented_func)

			.collect(&type::get_script_func)

			.collect(&type::is_placeholder_func)

			.collect(&type::set_fallback_func)
			.collect(&type::get_fallback_func)

			.collect(&type::get_language_func)

			.collect(&type::free_func)
		)
	)
		.def(py::init())

		.def_readwrite("set_func", &type::set_func)
		.def_readwrite("get_func", &type::get_func)
		.def_readwrite("get_property_list_func", &type::get_property_list_func)
		.def_readwrite("free_property_list_func", &type::free_property_list_func)

		.def_readwrite("property_can_revert_func", &type::property_can_revert_func)
		.def_readwrite("property_get_revert_func", &type::property_get_revert_func)

		.def_readwrite("get_owner_func", &type::get_owner_func)
		.def_readwrite("get_property_state_func", &type::get_property_state_func)

		.def_readwrite("get_method_list_func", &type::get_method_list_func)
		.def_readwrite("free_method_list_func", &type::free_method_list_func)
		.def_readwrite("get_property_type_func", &type::get_property_type_func)

		.def_readwrite("has_method_func", &type::has_method_func)

		.def_readwrite("call_func", &type::call_func)
		.def_readwrite("notification_func", &type::notification_func)

		.def_readwrite("to_string_func", &type::to_string_func)

		.def_readwrite("refcount_incremented_func", &type::refcount_incremented_func)
		.def_readwrite("refcount_decremented_func", &type::refcount_decremented_func)

		.def_readwrite("get_script_func", &type::get_script_func)

		.def_readwrite("is_placeholder_func", &type::is_placeholder_func)

		.def_readwrite("set_fallback_func", &type::set_fallback_func)
		.def_readwrite("get_fallback_func", &type::get_fallback_func)

		.def_readwrite("get_language_func", &type::get_language_func)

		.def_readwrite("free_func", &type::free_func)
	;
}


PyGDExtensionScriptInstanceInfo::operator const GDExtensionScriptInstanceInfo&() const {
	static const GDExtensionScriptInstanceInfo instance_info = {
		.set_func = [](GDExtensionScriptInstanceDataPtr p_instance, GDExtensionConstStringNamePtr p_name, GDExtensionConstVariantPtr p_value) -> GDExtensionBool
		{
			py::gil_scoped_acquire gil;
			try {
				try {
					auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(p_instance);
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

		.get_func = [](GDExtensionScriptInstanceDataPtr p_instance, GDExtensionConstStringNamePtr p_name, GDExtensionVariantPtr r_ret) -> GDExtensionBool
		{
			py::gil_scoped_acquire gil;
			try {
				try {
					auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(p_instance);
					cast(r_ret) = info->get_func(self, cast(p_name));
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

		.get_property_list_func = [](GDExtensionScriptInstanceDataPtr p_instance, uint32_t *r_count) -> const GDExtensionPropertyInfo *
		{
			py::gil_scoped_acquire gil;

			try {
				auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(p_instance);

				auto prop_list = std::make_unique<PropertyList>(info->get_property_list_func(self));

				*r_count = prop_list->size();
				return *prop_list.release();
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()

			*r_count = 0;
			return nullptr;
		},

		.free_property_list_func = [](GDExtensionScriptInstanceDataPtr p_instance, const GDExtensionPropertyInfo *p_list) -> void
		{
			py::gil_scoped_acquire gil;

			try {
				std::unique_ptr<PropertyList> prop_list(PropertyList::get_from_pointer(p_list));
				if(!prop_list) {
					return;
				}

				auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(p_instance);

				info->free_property_list_func(self, py::object(*prop_list));
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
		},

		.property_can_revert_func = [](GDExtensionScriptInstanceDataPtr p_instance, GDExtensionConstStringNamePtr p_name) -> GDExtensionBool
		{
			py::gil_scoped_acquire gil;
			try {
				try {
					auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(p_instance);
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

		.property_get_revert_func = [](GDExtensionScriptInstanceDataPtr p_instance, GDExtensionConstStringNamePtr p_name, GDExtensionVariantPtr r_ret) -> GDExtensionBool
		{
			py::gil_scoped_acquire gil;
			try {
				try {
					auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(p_instance);
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

		.get_owner_func = [](GDExtensionScriptInstanceDataPtr p_instance) -> GDExtensionObjectPtr
		{
			py::gil_scoped_acquire gil;
			try {
				auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(p_instance);
				auto* obj = info->get_owner_func(self).cast<Object*>();
				return static_cast<GDExtensionObjectPtr>(*obj);
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
			return nullptr;
		},

		.get_property_state_func = [](GDExtensionScriptInstanceDataPtr p_instance, GDExtensionScriptInstancePropertyStateAdd p_add_func, void *p_userdata) -> void
		{
			py::gil_scoped_acquire gil;
			py::print("get_property_state_func");
		},

		.get_method_list_func = [](GDExtensionScriptInstanceDataPtr p_instance, uint32_t *r_count) -> const GDExtensionMethodInfo *
		{
			py::gil_scoped_acquire gil;
			py::print("get_method_list_func");
			*r_count = 0;
			return nullptr;
		},

		.free_method_list_func = [](GDExtensionScriptInstanceDataPtr p_instance, const GDExtensionMethodInfo *p_list) -> void
		{
			py::gil_scoped_acquire gil;
			py::print("free_method_list_func");
		},

		.get_property_type_func = [](GDExtensionScriptInstanceDataPtr p_instance, GDExtensionConstStringNamePtr p_name, GDExtensionBool *r_is_valid) -> GDExtensionVariantType
		{
			py::gil_scoped_acquire gil;
			try {
				try {
					auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(p_instance);
					auto res = info->get_property_type_func(self, cast(p_name)).cast<GDExtensionVariantType>();
					*r_is_valid = true;
					return res;
				}
				catch(const py::error_already_set& exception) {
					if(!exception.matches(PyExc_AttributeError)) {
						throw;
					}
				}
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()

			*r_is_valid = false;
			return GDEXTENSION_VARIANT_TYPE_NIL;
		},

		.has_method_func = [](GDExtensionScriptInstanceDataPtr instance, GDExtensionConstStringNamePtr name) -> GDExtensionBool
		{
			py::gil_scoped_acquire gil;

			try {
				auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(instance);
				py::bool_ res = info->has_method_func(self, cast(name));
				return static_cast<bool>(res);
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()

			return false;
		},

		.call_func = [](GDExtensionScriptInstanceDataPtr instance, GDExtensionConstStringNamePtr method,
			const GDExtensionConstVariantPtr* args, GDExtensionInt argument_count,
			GDExtensionVariantPtr res, GDExtensionCallError* error) -> void
		{
			py::gil_scoped_acquire gil;

			if(error) {
				error->error = GDEXTENSION_CALL_OK; // XXX
			}

			try {
				try {
					auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(instance);
					cast(res) = info->call_func(self, cast(method), *cast(args, argument_count));
					return;
				}
				catch(const py::error_already_set& exception) {
					if(!exception.matches(PyExc_NotImplementedError)) { // XXX
						throw;
					}
				}
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()

			if(error) {
				error->error = GDEXTENSION_CALL_ERROR_INVALID_METHOD; // XXX
			}
		},

		.notification_func = [](GDExtensionScriptInstanceDataPtr instance, int32_t what) -> void
		{
			py::gil_scoped_acquire gil;
			try {
				auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(instance);
				info->notification_func(self, what);
				return;
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
		},

		.to_string_func = [](GDExtensionScriptInstanceDataPtr instance,
			GDExtensionBool* is_valid, GDExtensionStringPtr out) -> void
		{
			py::gil_scoped_acquire gil;
			try {
				auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(instance);
				cast(out) = info->to_string_func(self);
				*is_valid = true;
				return;
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
			*is_valid = false;
		},

		.refcount_incremented_func = [](GDExtensionScriptInstanceDataPtr p_instance) -> void
		{
			py::gil_scoped_acquire gil;
			//py::print("refcount_incremented_func");
		},

		.refcount_decremented_func = [](GDExtensionScriptInstanceDataPtr p_instance) -> GDExtensionBool
		{
			py::gil_scoped_acquire gil;
			//py::print("refcount_decremented_func");
			return false;
		},

		.get_script_func = [](GDExtensionScriptInstanceDataPtr p_instance) -> GDExtensionObjectPtr
		{
			py::gil_scoped_acquire gil;
			try {
				auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(p_instance);
				auto* obj = info->get_script_func(self).cast<Object*>();
				return static_cast<GDExtensionObjectPtr>(*obj);
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
			return nullptr;
		},

		.is_placeholder_func = [](GDExtensionScriptInstanceDataPtr p_instance) -> GDExtensionBool
		{
			py::gil_scoped_acquire gil;
			py::print("is_placeholder_func");
			return false;
		},

		.get_language_func = [](GDExtensionScriptInstanceDataPtr p_instance) -> GDExtensionScriptLanguagePtr
		{
			py::gil_scoped_acquire gil;
			try {
				auto [info, self] = *reinterpret_cast<ScriptInstanceData*>(p_instance);
				auto* obj = info->get_language_func(self).cast<Object*>();
				return reinterpret_cast<GDExtensionScriptLanguagePtr>( // XXX
					static_cast<GDExtensionObjectPtr>(*obj));
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
			return nullptr;
		},

		.free_func = [](GDExtensionScriptInstanceDataPtr p_instance) -> void
		{
			py::gil_scoped_acquire gil;
		},
	};

	return instance_info;
}


PyGDExtensionScriptInstanceInfo::operator const GDExtensionScriptInstanceInfo*() const {
	return &static_cast<const GDExtensionScriptInstanceInfo&>(*this);
}


} // namespace pygodot


