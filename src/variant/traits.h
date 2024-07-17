#pragma once

#include <any>
#include <span>


#include "extension/extension.h"
#include "util/exceptions.h"
#include "util/python_utils.h"


namespace pygodot {


// utilities

template<typename T>
struct is_reference_wrapper : std::false_type {};

template<typename T>
struct is_reference_wrapper<std::reference_wrapper<T>> : std::true_type {};

template<typename T>
static constexpr bool is_reference_wrapper_v = is_reference_wrapper<T>::value;


template<typename T>
struct is_optional : std::false_type {};

template<typename T>
struct is_optional<std::optional<T>> : std::true_type {};

template<typename T>
static constexpr bool is_optional_v = is_optional<T>::value;


template<typename T>
using remove_element_const_t = std::conditional_t<
	std::is_pointer_v<T>,
	std::add_pointer_t<std::remove_const_t<std::remove_pointer_t<T>>>,
	std::remove_const_t<T>
>;

template<typename T>
using add_element_const_t = std::conditional_t<
	std::is_pointer_v<T>,
	std::add_pointer_t<std::add_const_t<std::remove_pointer_t<T>>>,
	std::add_const_t<T>
>;

template<typename T>
static constexpr bool is_element_const_v = std::is_const_v<std::remove_pointer_t<T>>;


template<bool Value, typename Type>
struct bool_constant_and_type : std::bool_constant<Value> {
	using type = Type;
};


template<typename... Ts>
struct type_list {};


template<typename...>
struct _concat_type_lists;

template<>
struct _concat_type_lists<> {
	using type = type_list<>;
};

template<typename... Ts>
struct _concat_type_lists<type_list<Ts...>> {
	using type = type_list<Ts...>;
};

template<typename T>
struct _concat_type_lists<T> {
	using type = type_list<T>;
};

template<typename... T1s, typename... T2s, typename... Rem>
struct _concat_type_lists<type_list<T1s...>, type_list<T2s...>, Rem...> {
	using type = typename _concat_type_lists<type_list<T1s..., T2s...>, Rem...>::type;
};

/*template<typename T, typename... Ts, typename... Rem>
struct _concat_type_lists<T, type_list<Ts...>, Rem...> {
	using type = typename _concat_type_lists<type_list<T, Ts...>, Rem...>::type;
};

template<typename... Ts, typename T, typename... Rem>
struct _concat_type_lists<type_list<Ts...>, T, Rem...> {
	using type = typename _concat_type_lists<type_list<Ts..., T>, Rem...>::type;
};*/

template<typename... T>
struct _concat_type_lists {
	using type = typename _concat_type_lists<typename _concat_type_lists<T>::type...>::type;
};

template<typename... Ls>
using concat_type_lists = typename _concat_type_lists<Ls...>::type;


template<template<typename...> typename Template, typename TypeList>
using apply_type_list = decltype([]<typename... Ts>(type_list<Ts...>)
	-> Template<Ts...>
{
	return std::declval<Template<Ts...>>();
}(TypeList{}));


template<typename T, typename... Ts>
constexpr bool _is_in_type_list(type_list<Ts...>) {
	return (std::is_same_v<T, Ts> || ...);
}

template<typename T, typename TypeList>
constexpr bool _is_in_type_list() {
	return _is_in_type_list<T>(TypeList{});
}

template<typename T, typename... Ts>
static constexpr bool is_in_type_list = _is_in_type_list<T, Ts...>();

} // namespace pygodot


// forward declare variant types

namespace godot {

class Variant;
//class GDExtensionBool;
//class GDExtensionInt;
//class GDExtensionFloat;
class String;
class Vector2;
class Vector2i;
class Rect2;
class Rect2i;
class Vector3;
class Vector3i;
class Transform2D;
class Vector4;
class Vector4i;
class Plane;
class Quaternion;
class AABB;
class Basis;
class Transform3D;
class Projection;
class Color;
class StringName;
class NodePath;
class RID;
class Object;
class Callable;
class Signal;
class Dictionary;
class Array;
class PackedByteArray;
class PackedInt32Array;
class PackedInt64Array;
class PackedFloat32Array;
class PackedFloat64Array;
class PackedStringArray;
class PackedVector2Array;
class PackedVector3Array;
class PackedColorArray;
class PackedVector4Array;

} // namespace godot


namespace pygodot {

using namespace godot;

// variant type lists

using variant_type_list = type_list<
	Variant,
	GDExtensionBool,
	GDExtensionInt,
	GDExtensionFloat,
	String,
	Vector2,
	Vector2i,
	Rect2,
	Rect2i,
	Vector3,
	Vector3i,
	Transform2D,
	Vector4,
	Vector4i,
	Plane,
	Quaternion,
	AABB,
	Basis,
	Transform3D,
	Projection,
	Color,
	StringName,
	NodePath,
	RID,
	Object,
	Callable,
	Signal,
	Dictionary,
	Array,
	PackedByteArray,
	PackedInt32Array,
	PackedInt64Array,
	PackedFloat32Array,
	PackedFloat64Array,
	PackedStringArray,
	PackedVector2Array,
	PackedVector3Array,
	PackedColorArray,
	PackedVector4Array
>;

using variant_array_type_list = type_list<
	Array,
	PackedByteArray,
	PackedInt32Array,
	PackedInt64Array,
	PackedFloat32Array,
	PackedFloat64Array,
	PackedStringArray,
	PackedVector2Array,
	PackedVector3Array,
	PackedColorArray,
	PackedVector4Array
>;


// variant type concepts

template<typename T>
concept VariantType = is_in_type_list<T, variant_type_list>;


template<typename T>
concept VariantArrayType = is_in_type_list<T, variant_array_type_list>;


// variant*

template<typename T>
concept VariantPointer = std::is_same_v<remove_element_const_t<T>, GDExtensionVariantPtr>;

template<typename T>
concept UninitializedVariantPointer = std::is_same_v<T, GDExtensionUninitializedVariantPtr>;

template<typename T>
concept MaybeUninitializedVariantPointer = VariantPointer<T> || UninitializedVariantPointer<T>;

template<typename T>
concept VariantPointerArgs = std::is_pointer_v<T>
	&& VariantPointer<std::remove_const_t<std::remove_pointer_t<T>>>;


// variant value*

template<typename T>
concept VariantValuePointer = std::is_same_v<remove_element_const_t<T>, GDExtensionTypePtr>;

template<typename T>
concept ConstVariantValuePointer = std::is_same_v<T, GDExtensionConstTypePtr>;

template<typename T>
concept UninitializedVariantValuePointer = std::is_same_v<T, GDExtensionUninitializedTypePtr>;

template<typename T>
concept MaybeUninitializedVariantValuePointer = VariantValuePointer<T> || UninitializedVariantValuePointer<T>;

template<typename T>
concept VariantValuePointerArgs = std::is_pointer_v<T>
	&& VariantValuePointer<std::remove_const_t<std::remove_pointer_t<T>>>;


// string*

template<typename T>
concept StringPointer = std::is_same_v<remove_element_const_t<T>, GDExtensionStringPtr>;

template<typename T>
concept UninitializedStringPointer = std::is_same_v<T, GDExtensionUninitializedStringPtr>;

template<typename T>
concept MaybeUninitializedStringPointer = StringPointer<T> || UninitializedStringPointer<T>;

// string name*

template<typename T>
concept StringNamePointer = std::is_same_v<remove_element_const_t<T>, GDExtensionStringNamePtr>;

template<typename T>
concept UninitializedStringNamePointer = std::is_same_v<T, GDExtensionUninitializedStringNamePtr>;

template<typename T>
concept MaybeUninitializedStringNamePointer = StringNamePointer<T> || UninitializedStringNamePointer<T>;

// any pointer

template<typename T>
concept InitializedPointer = VariantPointer<T> || VariantValuePointer<T>
	|| StringPointer<T> || StringNamePointer<T>;

template<typename T>
concept UninitializedPointer = UninitializedVariantPointer<T> || UninitializedVariantValuePointer<T>
	|| UninitializedStringPointer<T> || UninitializedStringNamePointer<T>;

template<typename T>
concept MaybeUninitializedPointer = InitializedPointer<T> || UninitializedPointer<T>;


// py::object

template<typename T>
concept PythonObject = std::is_base_of_v<py::object, std::remove_const_t<T>>
	|| std::is_same_v<std::remove_const_t<T>, py::handle>; // XXX: handle?

template<typename T>
concept PythonObjectPointer = std::is_pointer_v<T> && PythonObject<std::remove_pointer_t<T>>;

template<typename T>
concept PythonObjectReference = std::is_lvalue_reference_v<T> && PythonObject<std::remove_reference_t<T>>;

template<typename T>
concept PythonObjectReferenceWrapper = is_reference_wrapper_v<T> && PythonObject<typename T::type>;

template<typename T>
concept PythonArgs = std::is_same_v<std::remove_const_t<T>, py::args>;


// variarnt pointer traits

template<MaybeUninitializedPointer T>
using as_initialized_pointer_t = typename std::disjunction<
	bool_constant_and_type<InitializedPointer<T>, T>,
	bool_constant_and_type<UninitializedVariantPointer<T>, GDExtensionVariantPtr>,
	bool_constant_and_type<UninitializedVariantValuePointer<T>, GDExtensionTypePtr>,
	bool_constant_and_type<UninitializedStringPointer<T>, GDExtensionStringPtr>,
	bool_constant_and_type<UninitializedStringNamePointer<T>, GDExtensionStringNamePtr>,
	std::true_type
>::type;


template<MaybeUninitializedPointer T>
using as_uninitialized_pointer_t = typename std::disjunction<
	bool_constant_and_type<UninitializedPointer<T>, T>,
	bool_constant_and_type<VariantPointer<T>, GDExtensionUninitializedVariantPtr>,
	bool_constant_and_type<VariantValuePointer<T>, GDExtensionUninitializedTypePtr>,
	bool_constant_and_type<StringPointer<T>, GDExtensionUninitializedStringPtr>,
	bool_constant_and_type<StringNamePointer<T>, GDExtensionUninitializedStringNamePtr>,
	std::true_type
>::type;


// variarnt traits

template<VariantType T>
static constexpr size_t variant_type_size = []() -> size_t {
#define GDEXTENSION_VARIANT_TYPE(type_name, type_size, type_enum_name) \
	if constexpr(std::is_same_v<T, type_name>) { return type_size; }
	GDEXTENSION_VARIANT_TYPES
#undef GDEXTENSION_VARIANT_TYPE
}();


template<VariantType T>
static constexpr GDExtensionVariantType variant_type_to_enum_value = []() -> GDExtensionVariantType {
#define GDEXTENSION_VARIANT_TYPE(type_name, type_size, type_enum_name) \
	if constexpr(std::is_same_v<T, type_name>) { return type_enum_name; }
	GDEXTENSION_VARIANT_TYPES
#undef GDEXTENSION_VARIANT_TYPE
}();


template<GDExtensionVariantType EnumValue>
using variant_enum_value_to_type = typename std::disjunction<
#define GDEXTENSION_VARIANT_TYPE(type_name, type_size, type_enum_name) \
	bool_constant_and_type<EnumValue == type_enum_name, type_name>,
	GDEXTENSION_VARIANT_TYPES
#undef GDEXTENSION_VARIANT_TYPE
	std::true_type
>::type;


template<VariantType T>
static const std::string variant_type_name = []() -> std::string {
	if constexpr(std::is_same_v<T, GDExtensionBool>) { return "bool"; }
	if constexpr(std::is_same_v<T, GDExtensionInt>) { return "int"; }
	if constexpr(std::is_same_v<T, GDExtensionFloat>) { return "float"; }
#define GDEXTENSION_VARIANT_TYPE(type_name, type_size, type_enum_name) \
	if constexpr(std::is_same_v<T, type_name>) { return #type_name; }
	GDEXTENSION_VARIANT_TYPES
#undef GDEXTENSION_VARIANT_TYPE
}();


template<VariantArrayType T>
using variant_array_element_type = typename std::disjunction<
#define VARIANT_ARRAY_TYPE(array_type, element_type) \
	bool_constant_and_type<std::is_same_v<T, array_type>, element_type>,

	VARIANT_ARRAY_TYPE(Array, Variant)
	VARIANT_ARRAY_TYPE(PackedByteArray, GDExtensionInt)
	VARIANT_ARRAY_TYPE(PackedInt32Array, GDExtensionInt)
	VARIANT_ARRAY_TYPE(PackedInt64Array, GDExtensionInt)
	VARIANT_ARRAY_TYPE(PackedFloat32Array, GDExtensionFloat)
	VARIANT_ARRAY_TYPE(PackedFloat64Array, GDExtensionFloat)
	VARIANT_ARRAY_TYPE(PackedStringArray, String)
	VARIANT_ARRAY_TYPE(PackedVector2Array, Vector2)
	VARIANT_ARRAY_TYPE(PackedVector3Array, Vector3)
	VARIANT_ARRAY_TYPE(PackedColorArray, Color)
	VARIANT_ARRAY_TYPE(PackedVector4Array, Vector4)

#undef VARIANT_ARRAY_TYPE
	std::true_type
>::type;



template<typename T>
concept has_variant_type_def = VariantType<T> && requires(T) { T::pre_def; T::def; };


template<VariantType Type>
py::handle variant_type_handle() {
	static py::handle type;
	if(!type) {
		if constexpr(std::is_same_v<Type, GDExtensionBool>) {
			type = reinterpret_cast<PyObject*>(&PyBool_Type);
		}
		else if constexpr(std::is_same_v<Type, GDExtensionInt>) {
			type = reinterpret_cast<PyObject*>(&PyLong_Type);
		}
		else if constexpr(std::is_same_v<Type, GDExtensionFloat>) {
			type = reinterpret_cast<PyObject*>(&PyFloat_Type);
		}
		else {
			type = resolve_name("godot." + variant_type_name<Type>); // XXX
			//py::type::handle_of<Type>();
		}
	}
	return type;
}

py::handle variant_type_handle(std::same_as<GDExtensionVariantType> auto type) {
	py::handle res = with_variant_type(type, []<typename Type>() {
		return variant_type_handle<Type>();
	});
	if(!res) {
		throw std::runtime_error("failed to get variant type handle");
	}
	return res;
}


// evaluation utilities


inline void check_valid(GDExtensionVariantType type) {
	if(type >= GDEXTENSION_VARIANT_TYPE_VARIANT_MAX) {
		throw std::runtime_error("invalid variant type");
	}
}


template<typename... Ts, typename Func>
constexpr decltype(auto) for_each_variant_type(Func&& func, type_list<Ts...>) {
	using Res = decltype(std::declval<Func>().template operator()<Variant>());

	if constexpr(is_optional_v<Res>) {
		Res res;
		((res = std::forward<Func>(func).template operator()<Ts>(), res.has_value()) || ...);
		return res;
	}
	else {
		return (std::forward<Func>(func).template operator()<Ts>(), ...);
	}
}

template<typename TypeList = variant_type_list, typename Func>
constexpr decltype(auto) for_each_variant_type(Func&& func) {
	return for_each_variant_type(std::forward<Func>(func), TypeList{});
}


template<typename Func>
auto with_variant_type(GDExtensionVariantType type, Func&& func) {
	using Res = decltype(std::declval<Func>().template operator()<Variant>());

	check_valid(type);

	if constexpr(std::is_void_v<Res>) {
		for_each_variant_type([func, type]<VariantType Type>() {
			if(variant_type_to_enum_value<Type> == type) {
				func.template operator()<Type>();
			}
		});
	}
	else {
		Res res;

		for_each_variant_type([func, type, &res]<VariantType Type>() {
			if(variant_type_to_enum_value<Type> == type) {
				res = func.template operator()<Type>();
			}
		});

		return res;
	}
}


auto variant_type_from_type_handle_exact(std::convertible_to<py::handle> auto type) {
	return for_each_variant_type([type]<typename Type>() -> std::optional<GDExtensionVariantType> {
		if(type.ptr() == variant_type_handle<Type>().ptr()) {
			return variant_type_to_enum_value<Type>;
		}
		return std::nullopt;
	});
}


auto variant_type_from_type_handle_inferred(std::convertible_to<py::handle> auto type)
	-> std::optional<GDExtensionVariantType>
{
	// XXX: optimize

	// exact

	if(auto res = variant_type_from_type_handle_exact(type)) {
		return res;
	}

	static py::handle str = resolve_name("str");
	static py::handle dict = resolve_name("dict");
	static py::handle list = resolve_name("list");
	static py::handle tuple = resolve_name("tuple");

	static py::handle strname = resolve_name("godot._internal.utils.strname"); // XXX: special case

	// XXX: fast path for str, dict, list and tuple
	if(type.ptr() == str.ptr()) {
		return variant_type_to_enum_value<String>;
	}
	else if(type.ptr() == strname.ptr()) {
		return variant_type_to_enum_value<StringName>;
	}
	else if(type.ptr() == dict.ptr()) {
		return variant_type_to_enum_value<Dictionary>;
	}
	else if(type.ptr() == list.ptr()) {
		return variant_type_to_enum_value<Array>;
	}
	else if(type.ptr() == tuple.ptr()) {
		return variant_type_to_enum_value<Array>;
	}

	// subclass
	// NOTE: except for object these are unlikely

	// XXX: fast path for object
	if(issubclass(type, variant_type_handle<Object>())) {
		return variant_type_to_enum_value<Object>;
	}

	if(auto res = for_each_variant_type([type]<typename Type>() -> std::optional<GDExtensionVariantType> {
			if(issubclass(type, variant_type_handle<Type>())) {
				return variant_type_to_enum_value<Type>;
			}
			return std::nullopt;
		}))
	{
		return res;
	}

	// implicit cast
	// NOTE: order is important

	//static py::handle SupportsBytes = resolve_name("typing.SupportsBytes"); // XXX: bytes / buffer
	//static py::handle Buffer = resolve_name("collections.abc.Buffer"); // XXX: bytes / buffer

	static py::handle Mapping = resolve_name("collections.abc.Mapping");
	static py::handle Sequence = resolve_name("collections.abc.Sequence"); // XXX: bytes

	static py::handle SupportsFloat = resolve_name("typing.SupportsFloat");
	static py::handle SupportsInt = resolve_name("typing.SupportsInt");
	static py::handle SupportsIndex = resolve_name("typing.SupportsIndex");
	//static py::handle SupportsBool = resolve_name("typing.SupportsBool"); // XXX: bool?

	static py::handle Callable_ = resolve_name("collections.abc.Callable"); // XXX

	if(issubclass(type, strname)) {
		return variant_type_to_enum_value<StringName>;
	}
	else if(issubclass(type, str)) {
		return variant_type_to_enum_value<String>;
	}
	else if(issubclass(type, Mapping)) {
		return variant_type_to_enum_value<Dictionary>;
	}
	else if(issubclass(type, Sequence)) {
		return variant_type_to_enum_value<Array>;
	}

	else if(issubclass(type, SupportsFloat)) {
		return variant_type_to_enum_value<GDExtensionFloat>;
	}
	else if(issubclass(type, SupportsInt)) {
		return variant_type_to_enum_value<GDExtensionInt>;
	}
	else if(issubclass(type, SupportsIndex)) {
		return variant_type_to_enum_value<GDExtensionInt>;
	}

	else if(issubclass(type, Callable_)) {
		return variant_type_to_enum_value<Callable>;
	}

	return std::nullopt;
}

auto variant_type_from_instance_inferred_checked(std::convertible_to<py::handle> auto obj) {
	if(!obj || obj.is_none()) {
		return variant_type_to_enum_value<Variant>;
	}

	py::handle type = py::type::handle_of(obj);
	auto res = variant_type_from_type_handle_inferred(type);

	if(!res) {
		throw std::runtime_error("python object of type '"
			+ get_fully_qualified_name(type)
			+ "' is not castable to variant");
	}

	return *res;
}




} // namespace pygodot




