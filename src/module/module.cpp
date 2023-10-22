#include <pybind11/embed.h>
#include <pybind11/stl.h>

#include "variant/variant.h"
#include "variant/string.h"
#include "variant/string_name.h"
#include "variant/object.h"

#include "casting/cast_args.h"

#include "module/property_info.h"
#include "module/property_list.h"
#include "module/class_method_info.h"
#include "module/class_creation_info.h"
#include "module/script_instance_info.h"


namespace pygodot {


namespace py = pybind11;


py::object variant_get_ptr_constructor(
	GDExtensionVariantType type, const PyGDExtensionClassMethodInfo& method, GDExtensionInt constructor_index)
{
	GDExtensionPtrConstructor constructor_ptr = extension_interface::variant_get_ptr_constructor(
		type, constructor_index);

	if(!constructor_ptr) {
		return py::none();
	}

	py::handle __init_uninitialized__ = variant_type_handle(type)
		.attr("__init_uninitialized__");

	const auto arg_types = get_arguments_cast_info(method);

	// TODO: default args? python side?

	auto func = [type, constructor_ptr, __init_uninitialized__, arg_types]
		(py::object self, py::args args) -> void
	{
		__init_uninitialized__(self);
		constructor_ptr(cast(self, type), cast(args, arg_types));
	};

	return py::cpp_function(std::move(func), py::name("constructor")); // TODO: name
}

py::object variant_get_ptr_indexed_getter(GDExtensionVariantType type, GDExtensionVariantType return_value_type)
{
	auto* indexed_getter = extension_interface::variant_get_ptr_indexed_getter(type);

	if(!indexed_getter) {
		return py::none();
	}

	//py::handle return_type = variant_type_handle(return_value_type);

	return py::cpp_function([type, indexed_getter, return_value_type](py::object self, GDExtensionInt index)
			-> py::object
		{
			py::object ret;
			indexed_getter(cast(self, type), index,
				cast(std::ref(ret), return_value_type, nullptr)); // XXX: cast info
			return ret;
		},
		py::is_method(variant_type_handle(type)),
		py::name("indexed_getter") // TODO: name
	);
}

py::object variant_get_ptr_indexed_setter(GDExtensionVariantType type, GDExtensionVariantType value_type)
{
	auto* indexed_setter = extension_interface::variant_get_ptr_indexed_setter(type);

	if(!indexed_setter) {
		return py::none();
	}

	//py::handle type_ = variant_type_handle(value_type);

	return py::cpp_function([type, indexed_setter, value_type](py::object self, GDExtensionInt index,
			const py::object value)
		{
			indexed_setter(cast(self, type), index, cast(value, value_type)); // XXX: cast info
		},
		py::is_method(variant_type_handle(type)),
		py::name("indexed_setter") // TODO: name
	);
}

py::object variant_get_ptr_keyed_getter(GDExtensionVariantType type, GDExtensionVariantType key_type,
	GDExtensionVariantType return_value_type)
{
	auto* keyed_getter = extension_interface::variant_get_ptr_keyed_getter(type);

	if(!keyed_getter) {
		return py::none();
	}

	//py::handle return_type = variant_type_handle(return_value_type);

	return py::cpp_function([type, keyed_getter, key_type, return_value_type](py::object self, py::object key)
			-> py::object
		{
			py::object ret;
			keyed_getter(cast(self, type), cast(key, key_type),
				cast(std::ref(ret), return_value_type, nullptr)); // XXX: cast info
			return ret;
		},
		py::is_method(variant_type_handle(type)),
		py::name("keyed_getter") // TODO: name
	);
}


py::object variant_get_ptr_keyed_setter(GDExtensionVariantType type, GDExtensionVariantType key_type,
	GDExtensionVariantType value_type)
{
	auto* keyed_setter = extension_interface::variant_get_ptr_keyed_setter(type);

	if(!keyed_setter) {
		return py::none();
	}

	//py::handle type_ = variant_type_handle(value_type);

	return py::cpp_function([type, keyed_setter, key_type, value_type](py::object self, py::object key,
			py::object value)
		{
			keyed_setter(cast(self, type), cast(key, key_type), cast(value, value_type)); // XXX: cast info
		},
		py::is_method(variant_type_handle(type)),
		py::name("keyed_setter") // TODO: name
	);
}





py::object variant_get_ptr_getter(GDExtensionVariantType type, const StringName& member_name,
	GDExtensionVariantType member_type)
{
	auto* getter = extension_interface::variant_get_ptr_getter(type, member_name);

	if(!getter) {
		return py::none();
	}

	//py::handle return_type = variant_type_handle(return_value_type);

	auto name = std::make_unique<std::string>(member_name);
	auto* name_data = name->data();

	return py::cpp_function([name = std::move(name), type, getter, member_type](py::object self)
			-> py::object
		{
			py::object ret;
			getter(cast(self, type), cast(std::ref(ret), member_type, nullptr)); // XXX: cast info
			return ret;
		},
		py::is_method(variant_type_handle(type)),
		py::name(name_data) // TODO: name
	);
}


py::object variant_get_ptr_setter(GDExtensionVariantType type, const StringName& member_name,
	GDExtensionVariantType member_type)
{
	auto* setter = extension_interface::variant_get_ptr_setter(type, member_name);

	if(!setter) {
		return py::none();
	}

	//py::handle type_ = variant_type_handle(value_type);

	auto name = std::make_unique<std::string>(member_name);
	auto* name_data = name->data();

	return py::cpp_function([name = std::move(name), type, setter, member_type](
			py::object self, py::object value)
		{
			setter(cast(self, type), cast(value, member_type)); // XXX: cast info
		},
		py::is_method(variant_type_handle(type)),
		py::name(name_data) // TODO: name
	);
}




py::object variant_get_ptr_operator_evaluator(GDExtensionVariantOperator operator_,
	GDExtensionVariantType type_a, GDExtensionVariantType type_b, GDExtensionVariantType return_type)
{
	auto* eval = extension_interface::variant_get_ptr_operator_evaluator(operator_, type_a, type_b);

	if(!eval) {
		return py::none();
	}

	return py::cpp_function([eval, type_a, type_b, return_type](
			py::object obj_a, py::object obj_b) -> py::object
		{
			py::object ret;
			eval(cast(obj_a, type_a), cast(obj_b, type_b),
				cast(std::ref(ret), return_type, nullptr)); // XXX: cast info
			return ret;
		},
		py::name("eval") // TODO: name
	);
}




py::object variant_get_ptr_builtin_method(
	GDExtensionVariantType type, const PyGDExtensionClassMethodInfo& method, GDExtensionInt hash)
{
	bool is_static_method = ((method.method_flags & GDEXTENSION_METHOD_FLAG_STATIC) != 0);
	bool is_vararg = ((method.method_flags & GDEXTENSION_METHOD_FLAG_VARARG) != 0);

	GDExtensionPtrBuiltInMethod method_ptr = extension_interface::variant_get_ptr_builtin_method(
		type, method.name, hash);

	if(!method_ptr) {
		return py::none();
	}

	const auto arg_types = get_arguments_cast_info(method);
	const auto return_type = get_return_cast_info(method);

	auto name = std::make_unique<std::string>(method.name);
	auto* name_data = name->data();

	// TODO: default args? python side?

	if(is_vararg) { // XXX
		return py::cpp_function(
			[name = std::move(name), type, method_ptr, return_type]
				(py::object self, py::args args) -> py::object
			{
				GDExtensionCallError error;
				py::object ret;
				extension_interface::variant_call(cast(self, variant_type_to_enum_value<Variant>), StringName(*name), cast(args), args.size(),
					cast(std::ref(ret), variant_type_to_enum_value<Variant>, nullptr), &error);
				return ret;
			},
			py::is_method(variant_type_handle(type)),
			py::name(name_data)
		);
	}

	if(!is_static_method) {
		return py::cpp_function(
			[name = std::move(name), type, method_ptr, return_type, arg_types]
				(py::object self, py::args args) -> py::object
			{
				py::object ret;
				method_ptr(cast(self, type), cast(args, arg_types),
					cast(std::ref(ret), return_type), args.size());
				return ret;
			},
			py::is_method(variant_type_handle(type)),
			py::name(name_data)
		);
	}
	else {
		return py::cpp_function(
			[name = std::move(name), method_ptr, return_type, arg_types]
				(py::args args) -> py::object
			{
				py::object ret;
				method_ptr(nullptr, cast(args, arg_types), cast(std::ref(ret), return_type), args.size());
				return ret;
			},
			py::name(name_data)
		);
	}
}


py::object classdb_get_method_bind(
	const StringName& class_name, const PyGDExtensionClassMethodInfo& method, GDExtensionInt hash)
{
	bool is_static_method = ((method.method_flags & GDEXTENSION_METHOD_FLAG_STATIC) != 0);

	GDExtensionConstMethodBindPtr method_ptr = extension_interface::classdb_get_method_bind(
		class_name, method.name, hash);

	if(!method_ptr) {
		return py::none();
	}

	const auto arg_types = get_arguments_cast_info(method);
	const auto return_type = get_return_cast_info(method);

	// TODO: default args? python side?

	auto name = std::make_unique<std::string>(method.name);
	auto* name_data = name->data();

	if(!is_static_method) {
		//auto type = py::type::handle_of(py::module_::import("godot").attr(class_name));
		auto type = resolve_name("godot." + std::string(class_name));

		return py::cpp_function(
			[name = std::move(name), method_ptr, return_type, arg_types]
				(Object& self, py::args args) -> py::object
			{
				py::object ret;
				call_without_gil(extension_interface::object_method_bind_ptrcall,
					method_ptr, self, cast(args, arg_types), cast(std::ref(ret), return_type)
				);
				return ret;
			},
			py::is_method(type),
			py::name(name_data)
		);
	}
	else {
		return py::cpp_function(
			[name = std::move(name), method_ptr, return_type, arg_types]
				(py::args args) -> py::object
			{
				py::object ret;
				call_without_gil(extension_interface::object_method_bind_ptrcall,
					method_ptr, nullptr, cast(args, arg_types), cast(std::ref(ret), return_type)
				);
				return ret;
			},
			py::name(name_data)
		);
	}
}



py::object variant_get_ptr_utility_function(const PyGDExtensionClassMethodInfo& function, GDExtensionInt hash)
{
	bool is_vararg = ((function.method_flags & GDEXTENSION_METHOD_FLAG_VARARG) != 0);

	GDExtensionPtrUtilityFunction func_ptr = extension_interface::variant_get_ptr_utility_function(
		function.name, hash);

	if(!func_ptr) {
		return py::none();
	}

	const auto return_type = get_return_cast_info(function);

	auto name = std::make_unique<std::string>(function.name);
	auto* name_data = name->data();

	// TODO: default args? python side?

	if(is_vararg) { // XXX
		return py::cpp_function(
			[name = std::move(name), func_ptr, return_type]
				(py::args args) -> py::object
			{
				py::object ret;
				func_ptr(cast(std::ref(ret), return_type), cast(args), args.size());
				return ret;
			},
			py::name(name_data)
		);
	}

	const auto arg_types = get_arguments_cast_info(function);

	return py::cpp_function(
		[name = std::move(name), func_ptr, return_type, arg_types]
			(py::args args) -> py::object
		{
			py::object ret;
			func_ptr(cast(std::ref(ret), return_type), cast(args, arg_types), args.size());
			return ret;
		},
		py::name(name_data)
	);
}



/*py::object variant_call(py::object self, const StringName& method, py::args args) {
	GDExtensionCallError error;

	Variant res(uninitialized);

	extension_interface::variant_call(cast(self), method, cast(args), args.size(), &res, &error)

	return cast(res);
}*/


py::str variant_stringify(py::object obj) {
	String res;
	extension_interface::variant_stringify(cast(obj, variant_type_to_enum_value<Variant>), res);
	return res;
}


} // namespace pygodot


PYBIND11_EMBEDDED_MODULE(_gdextension, module_) {
	using namespace pygodot;

	// enumerations

#define ENUM_VALUE(type, name) .value(#name, type::name)

	py::enum_<GDExtensionVariantType>(module_, "GDExtensionVariantType")
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_NIL)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_BOOL)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_INT)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_FLOAT)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_STRING)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_VECTOR2)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_VECTOR2I)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_RECT2)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_RECT2I)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_VECTOR3)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_VECTOR3I)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_TRANSFORM2D)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_VECTOR4)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_VECTOR4I)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_PLANE)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_QUATERNION)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_AABB)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_BASIS)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_TRANSFORM3D)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_PROJECTION)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_COLOR)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_STRING_NAME)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_NODE_PATH)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_RID)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_OBJECT)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_CALLABLE)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_SIGNAL)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_DICTIONARY)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_ARRAY)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_PACKED_BYTE_ARRAY)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_PACKED_INT32_ARRAY)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_PACKED_INT64_ARRAY)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_PACKED_FLOAT32_ARRAY)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_PACKED_FLOAT64_ARRAY)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_PACKED_STRING_ARRAY)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_PACKED_VECTOR2_ARRAY)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_PACKED_VECTOR3_ARRAY)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_PACKED_COLOR_ARRAY)
		ENUM_VALUE(GDExtensionVariantType, GDEXTENSION_VARIANT_TYPE_VARIANT_MAX)
		.export_values()
	;

	py::enum_<GDExtensionVariantOperator>(module_, "GDExtensionVariantOperator")
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_EQUAL)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_NOT_EQUAL)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_LESS)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_LESS_EQUAL)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_GREATER)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_GREATER_EQUAL)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_ADD)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_SUBTRACT)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_MULTIPLY)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_DIVIDE)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_NEGATE)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_POSITIVE)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_MODULE)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_POWER)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_SHIFT_LEFT)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_SHIFT_RIGHT)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_BIT_AND)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_BIT_OR)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_BIT_XOR)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_BIT_NEGATE)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_AND)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_OR)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_XOR)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_NOT)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_IN)
		ENUM_VALUE(GDExtensionVariantOperator, GDEXTENSION_VARIANT_OP_MAX)
		.export_values()
	;

	py::enum_<GDExtensionCallErrorType>(module_, "GDExtensionCallErrorType")
		ENUM_VALUE(GDExtensionCallErrorType, GDEXTENSION_CALL_OK)
		ENUM_VALUE(GDExtensionCallErrorType, GDEXTENSION_CALL_ERROR_INVALID_METHOD)
		ENUM_VALUE(GDExtensionCallErrorType, GDEXTENSION_CALL_ERROR_INVALID_ARGUMENT)
		ENUM_VALUE(GDExtensionCallErrorType, GDEXTENSION_CALL_ERROR_TOO_MANY_ARGUMENTS)
		ENUM_VALUE(GDExtensionCallErrorType, GDEXTENSION_CALL_ERROR_TOO_FEW_ARGUMENTS)
		ENUM_VALUE(GDExtensionCallErrorType, GDEXTENSION_CALL_ERROR_INSTANCE_IS_NULL)
		ENUM_VALUE(GDExtensionCallErrorType, GDEXTENSION_CALL_ERROR_METHOD_NOT_CONST)
		.export_values()
	;

	py::enum_<GDExtensionClassMethodFlags>(module_, "GDExtensionClassMethodFlags", py::arithmetic())
		ENUM_VALUE(GDExtensionClassMethodFlags, GDEXTENSION_METHOD_FLAG_NORMAL)
		ENUM_VALUE(GDExtensionClassMethodFlags, GDEXTENSION_METHOD_FLAG_EDITOR)
		ENUM_VALUE(GDExtensionClassMethodFlags, GDEXTENSION_METHOD_FLAG_CONST)
		ENUM_VALUE(GDExtensionClassMethodFlags, GDEXTENSION_METHOD_FLAG_VIRTUAL)
		ENUM_VALUE(GDExtensionClassMethodFlags, GDEXTENSION_METHOD_FLAG_VARARG)
		ENUM_VALUE(GDExtensionClassMethodFlags, GDEXTENSION_METHOD_FLAG_STATIC)
		ENUM_VALUE(GDExtensionClassMethodFlags, GDEXTENSION_METHOD_FLAGS_DEFAULT)
		.export_values()
	;

	py::enum_<GDExtensionClassMethodArgumentMetadata>(module_, "GDExtensionClassMethodArgumentMetadata")
		ENUM_VALUE(GDExtensionClassMethodArgumentMetadata, GDEXTENSION_METHOD_ARGUMENT_METADATA_NONE)
		ENUM_VALUE(GDExtensionClassMethodArgumentMetadata, GDEXTENSION_METHOD_ARGUMENT_METADATA_INT_IS_INT8)
		ENUM_VALUE(GDExtensionClassMethodArgumentMetadata, GDEXTENSION_METHOD_ARGUMENT_METADATA_INT_IS_INT16)
		ENUM_VALUE(GDExtensionClassMethodArgumentMetadata, GDEXTENSION_METHOD_ARGUMENT_METADATA_INT_IS_INT32)
		ENUM_VALUE(GDExtensionClassMethodArgumentMetadata, GDEXTENSION_METHOD_ARGUMENT_METADATA_INT_IS_INT64)
		ENUM_VALUE(GDExtensionClassMethodArgumentMetadata, GDEXTENSION_METHOD_ARGUMENT_METADATA_INT_IS_UINT8)
		ENUM_VALUE(GDExtensionClassMethodArgumentMetadata, GDEXTENSION_METHOD_ARGUMENT_METADATA_INT_IS_UINT16)
		ENUM_VALUE(GDExtensionClassMethodArgumentMetadata, GDEXTENSION_METHOD_ARGUMENT_METADATA_INT_IS_UINT32)
		ENUM_VALUE(GDExtensionClassMethodArgumentMetadata, GDEXTENSION_METHOD_ARGUMENT_METADATA_INT_IS_UINT64)
		ENUM_VALUE(GDExtensionClassMethodArgumentMetadata, GDEXTENSION_METHOD_ARGUMENT_METADATA_REAL_IS_FLOAT)
		ENUM_VALUE(GDExtensionClassMethodArgumentMetadata, GDEXTENSION_METHOD_ARGUMENT_METADATA_REAL_IS_DOUBLE)
		.export_values()
	;

	py::enum_<GDExtensionInitializationLevel>(module_, "GDExtensionInitializationLevel")
		ENUM_VALUE(GDExtensionInitializationLevel, GDEXTENSION_INITIALIZATION_CORE)
		ENUM_VALUE(GDExtensionInitializationLevel, GDEXTENSION_INITIALIZATION_SERVERS)
		ENUM_VALUE(GDExtensionInitializationLevel, GDEXTENSION_INITIALIZATION_SCENE)
		ENUM_VALUE(GDExtensionInitializationLevel, GDEXTENSION_INITIALIZATION_EDITOR)
		ENUM_VALUE(GDExtensionInitializationLevel, GDEXTENSION_MAX_INITIALIZATION_LEVEL)
		.export_values()
	;

#undef ENUM_VALUE

	// variant classes

	for_each_variant_type([&module_]<typename Type>() {
		if constexpr(has_variant_type_def<Type>) {
			Type::pre_def(module_);
		}
	});

	for_each_variant_type([&module_]<typename Type>() {
		if constexpr(has_variant_type_def<Type>) {
			Type::def(module_);
		}
	});

	// gde classes

	PyGDExtensionPropertyInfo::def(module_);
	PyGDExtensionClassCreationInfo::def(module_);
	PyGDExtensionClassMethodInfo::def(module_);
	PyGDExtensionScriptInstanceInfo::def(module_);

	// implicit conversions

	py::implicitly_convertible<py::str, String>();
	py::implicitly_convertible<py::str, StringName>();

	// methods

	module_.def("classdb_register_extension_class", [](
		const StringName& class_name, const StringName& base_name, PyGDExtensionClassCreationInfo& class_info)
	{
		GDExtensionClassCreationInfo info = class_info;
		extension_interface::classdb_register_extension_class(
			extension_interface::library, class_name, base_name, &info);
	});

	module_.def("classdb_register_extension_class_method", [](
		const StringName& class_name, PyGDExtensionClassMethodInfo& method_info)
	{
		GDExtensionClassMethodInfo info = method_info;
		extension_interface::classdb_register_extension_class_method(
			extension_interface::library, class_name, &info);
	});

	module_.def("classdb_register_extension_class_integer_constant", [](
		const StringName& class_name, const StringName& enum_name,
		const StringName& constant_name, GDExtensionInt constant_value,
		GDExtensionBool is_bitfield)
	{
		extension_interface::classdb_register_extension_class_integer_constant(
			extension_interface::library, class_name, enum_name,
			constant_name, constant_value, is_bitfield);
	});

	module_.def("classdb_register_extension_class_property", [](
		const StringName& class_name, PyGDExtensionPropertyInfo& prop_info,
		const StringName& setter, const StringName& getter)
	{
		GDExtensionPropertyInfo info = prop_info;
		extension_interface::classdb_register_extension_class_property(
			extension_interface::library, class_name, &info, setter, getter);
	});

	module_.def("classdb_register_extension_class_property_group", [](
		const StringName& class_name, const String group_name, const String& prefix)
	{
		extension_interface::classdb_register_extension_class_property_group(
			extension_interface::library, class_name, group_name, prefix);
	});

	module_.def("classdb_register_extension_class_property_subgroup", [](
		const StringName& class_name, const String subgroup_name, const String& prefix)
	{
		extension_interface::classdb_register_extension_class_property_subgroup(
			extension_interface::library, class_name, subgroup_name, prefix);
	});
	
	module_.def("classdb_register_extension_class_signal", [](
		const StringName& class_name, const StringName& signal_name,
		py::object arg_info_sequence)
	{
		PropertyList prop_list{arg_info_sequence};

		extension_interface::classdb_register_extension_class_signal(
			extension_interface::library, class_name, signal_name,
			prop_list, prop_list.size());
	});


	module_.def("print_error", extension_interface::print_error);
	module_.def("print_warning", extension_interface::print_warning);

	module_.def("variant_get_ptr_builtin_method", variant_get_ptr_builtin_method);
	module_.def("variant_get_ptr_constructor", variant_get_ptr_constructor);

	module_.def("variant_get_ptr_indexed_getter", variant_get_ptr_indexed_getter);
	module_.def("variant_get_ptr_indexed_setter", variant_get_ptr_indexed_setter);
	module_.def("variant_get_ptr_keyed_getter", variant_get_ptr_keyed_getter);
	module_.def("variant_get_ptr_keyed_setter", variant_get_ptr_keyed_setter);
	module_.def("variant_get_ptr_getter", variant_get_ptr_getter);
	module_.def("variant_get_ptr_setter", variant_get_ptr_setter);

	module_.def("variant_get_ptr_operator_evaluator", variant_get_ptr_operator_evaluator);

	module_.def("classdb_get_method_bind", classdb_get_method_bind);

	module_.def("variant_get_ptr_utility_function", variant_get_ptr_utility_function);



	module_.def("variant_stringify", variant_stringify);
	//module_.def("variant_call", variant_call);


	module_.def("global_get_singleton", [](const StringName& name) {
		return cast(call_without_gil(extension_interface::global_get_singleton, name));
	});


	module_.def("script_instance_create", script_instance_create);
	module_.def("placeholder_script_instance_create", placeholder_script_instance_create);
	module_.def("placeholder_script_instance_update", [](py::int_ placeholder,
			const py::object& properties, const py::object& values)
	{
		extension_interface::placeholder_script_instance_update(
			reinterpret_cast<GDExtensionScriptInstancePtr>(PyLong_AsVoidPtr(placeholder.ptr())),
			cast(properties, variant_type_to_enum_value<Array>),
			cast(values, variant_type_to_enum_value<Dictionary>)
		);
	});



	module_.def("callable_custom_get_userdata", [](const Callable& callable) -> py::object {
		auto* obj = static_cast<PyObject*>(extension_interface::callable_custom_get_userdata(callable, nullptr));
		if(!obj) {
			return py::none();
		}
		return py::reinterpret_borrow<py::function>(obj);
	});
}


PYBIND11_EMBEDDED_MODULE(_godot_internal_core_utils, module_) {
	using namespace pygodot;

	module_.def("variant_type_from_enum", variant_type_handle<GDExtensionVariantType>);
	module_.def("variant_enum_from_type_inferred", variant_type_from_type_handle_inferred<py::object>);
}



