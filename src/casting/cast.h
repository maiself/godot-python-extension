#pragma once

#include <variant>

#include <pybind11/pybind11.h>

#include "extension/extension.h"
#include "util/exceptions.h"
#include "variant/traits.h"
#include "variant/variant.h"
#include "variant/object.h"


namespace pygodot {


template<InitializedPointer Pointer>
py::object make_copy(Pointer ptr, GDExtensionVariantType variant_type, py::handle python_type = nullptr);

template<MaybeUninitializedPointer Pointer, PythonObject ObjectType>
auto make_copy(Pointer ptr, ObjectType obj, GDExtensionVariantType variant_type)
	-> as_initialized_pointer_t<Pointer>;


py::handle get_variant_python_type_handle(GDExtensionVariantType type);
GDExtensionVariantType get_python_object_variant_type(py::handle obj);


template<typename T, typename = void>
struct cast_t;

template<typename FromType>
struct cast_intermediate_t;


template<PythonObjectReferenceWrapper WrapperType>
struct cast_intermediate_t<WrapperType> {
private:
	// type list for temp values
	using cast_temp_value_types = type_list<
		GDExtensionBool,
		GDExtensionInt,
		GDExtensionFloat,

		String,
		StringName,
		Variant,

		Array, // XXX

		GDExtensionObjectPtr,

		Callable // XXX
	>;

	// container type for temp values
	using cast_temp_value_t = apply_type_list<std::variant,
		concat_type_lists<std::monostate, cast_temp_value_types>>;

	// object reference to write back to
	py::object& obj;

	// source and dest types
	GDExtensionVariantType variant_type;
	py::handle python_type;

	// container for any needed temp values
	cast_temp_value_t cast_temp_value;

	// pointer to value to be written to and eventually placed into the object reference
	GDExtensionTypePtr ptr = nullptr;

	cast_intermediate_t() = delete;
	cast_intermediate_t(const cast_intermediate_t&) = delete;
	cast_intermediate_t(cast_intermediate_t&&) = delete;

	auto cast_ptr() {
		return [this]<MaybeUninitializedPointer Ptr, bool initialized, VariantType Type>() {
			assert(variant_type == variant_type_to_enum_value<Variant>
				|| variant_type == variant_type_to_enum_value<Type>);

			variant_type = variant_type_to_enum_value<Type>;
			if constexpr(initialized) {
				return reinterpret_cast<Ptr>(operator GDExtensionTypePtr());
			}
			else {
				return reinterpret_cast<Ptr>(operator GDExtensionUninitializedTypePtr());
			}
		};
	}

public:
	cast_intermediate_t(py::object& obj,
			GDExtensionVariantType variant_type, py::handle python_type = nullptr)
		: obj(obj), variant_type(variant_type), python_type(python_type)
	{
	}

	~cast_intermediate_t() noexcept(false) {
		// cast temp values back into the python object reference
		with_variant_type(variant_type, [this]<VariantType Type>() {
			if constexpr(is_in_type_list<Type, cast_temp_value_types> || std::is_same_v<Type, Object>) {
				obj = make_copy(ptr, variant_type, python_type);
			}
			else if(python_type && !python_type.is_none()) {
				obj = python_type(obj);
			}
		});
	}

	// variant type

	operator GDExtensionTypePtr() {
		return with_variant_type(variant_type, [this]<VariantType Type>() -> GDExtensionTypePtr {
			if constexpr(is_in_type_list<Type, cast_temp_value_types>) {
				ptr = reinterpret_cast<GDExtensionTypePtr>(
					&cast_temp_value.emplace<Type>()); // initialized variant temp value
			}
			else if constexpr(std::is_same_v<Type, Object>) {
				ptr = reinterpret_cast<GDExtensionTypePtr>(
					&cast_temp_value.emplace<GDExtensionObjectPtr>(nullptr));
			}
			else {
				auto* typed_ptr = new Type(); // initialized variant value
				ptr = reinterpret_cast<GDExtensionTypePtr>(typed_ptr);
				obj = py::cast(typed_ptr, py::return_value_policy::take_ownership);
			}

			return ptr;
		});
	}

	operator GDExtensionUninitializedTypePtr() {
		return with_variant_type(variant_type, [this]<VariantType Type>()
			-> GDExtensionUninitializedTypePtr
		{
			if constexpr(is_in_type_list<Type, cast_temp_value_types>) {
				if constexpr(std::is_constructible_v<Type, decltype(uninitialized)>) {
					// uninitialized variant temp value
					ptr = reinterpret_cast<GDExtensionTypePtr>(
						&cast_temp_value.emplace<Type>(uninitialized));
				}
				else {
					ptr = reinterpret_cast<GDExtensionTypePtr>(
						&cast_temp_value.emplace<Type>());
				}
			}
			else if constexpr(std::is_same_v<Type, Object>) {
				ptr = reinterpret_cast<GDExtensionTypePtr>(
					&cast_temp_value.emplace<GDExtensionObjectPtr>(nullptr));
			}
			else {
				auto* typed_ptr = new Type(uninitialized); // uninitialized variant value
				ptr = reinterpret_cast<GDExtensionTypePtr>(typed_ptr);
				obj = py::cast(typed_ptr, py::return_value_policy::take_ownership);
			}

			return uninitialized(ptr);
		});
	}

	// variant

	operator GDExtensionVariantPtr() {
		return cast_ptr().template operator()<GDExtensionVariantPtr, true, Variant>();
	}

	operator GDExtensionUninitializedVariantPtr() {
		return cast_ptr().template operator()<GDExtensionUninitializedVariantPtr, false, Variant>();
	}

	// string

	operator GDExtensionStringPtr() {
		return cast_ptr().template operator()<GDExtensionStringPtr, true, String>();
	}

	operator GDExtensionUninitializedStringPtr() {
		return cast_ptr().template operator()<GDExtensionUninitializedStringPtr, false, String>();
	}

	// string name

	operator GDExtensionStringNamePtr() {
		return cast_ptr().template operator()<GDExtensionStringNamePtr, true, StringName>();
	}

	operator GDExtensionUninitializedStringNamePtr() {
		return cast_ptr().template operator()<GDExtensionUninitializedStringNamePtr, false, StringName>();
	}
};




// cast a const py::object to a const variant type pointer
// the pointer is valid only as long as the returned intermediate temporary is
// implicit casts are preformed and temp var created if needed (py to var implicit above)


// wants cast from ptr for =
template<PythonObject ObjectType>
struct cast_intermediate_t<ObjectType> {
private:
	using not_held_by_python_object = type_list<
		GDExtensionBool,
		GDExtensionInt,
		GDExtensionFloat,

		GDExtensionObjectPtr,

		Variant
	>;

	// type list for temp values
	using cast_temp_value_types = concat_type_lists<
		not_held_by_python_object,

		String,
		StringName,
		//NodePath,

		Dictionary,

		variant_array_type_list,

		Callable
	>;

	// container type for temp values
	using cast_temp_value_t = apply_type_list<std::variant,
		concat_type_lists<std::monostate, cast_temp_value_types>>;

	// object reference
	ObjectType obj;

	// dest type
	GDExtensionVariantType variant_type;

	// container for any needed temp values
	cast_temp_value_t cast_temp_value;

	cast_intermediate_t() = delete;
	cast_intermediate_t(const cast_intermediate_t&) = delete;
	cast_intermediate_t(cast_intermediate_t&&) = delete;

	auto maybe_emplace_and_get_pointer(GDExtensionVariantType variant_type) {
		return with_variant_type(variant_type, [this]<VariantType Type>() {
			GDExtensionTypePtr ptr;

			if constexpr(is_in_type_list<Type, not_held_by_python_object>) {
				if constexpr(std::is_constructible_v<Type, decltype(uninitialized)>) {
					ptr = reinterpret_cast<GDExtensionTypePtr>(
						&cast_temp_value.emplace<Type>(uninitialized));
				}
				else {
					ptr = reinterpret_cast<GDExtensionTypePtr>(
						&cast_temp_value.emplace<Type>());
				}
				make_copy(uninitialized(ptr), obj, variant_type_to_enum_value<Type>);
			}

			else if(py::isinstance<Type>(obj)) {
				ptr = reinterpret_cast<GDExtensionTypePtr>(
					py::cast<Type*>(obj));
			}

			else if constexpr(is_in_type_list<Type, cast_temp_value_types>) {
				ptr = reinterpret_cast<GDExtensionTypePtr>(
					&cast_temp_value.emplace<Type>(uninitialized));
				make_copy(uninitialized(ptr), obj, variant_type_to_enum_value<Type>);
			}

			else {
				throw std::runtime_error("python object of type '"
					+ get_fully_qualified_name(py::type::handle_of(obj))
					+ "' is not castable to variant of type " + variant_type_name<Type>);
			}

			return ptr;
		});
	}

	template<MaybeUninitializedPointer Ptr>
	auto cast(GDExtensionVariantType expected_variant_type) {
		static_assert(std::is_const_v<Ptr> || !std::is_const_v<ObjectType>);

		if(variant_type != variant_type_to_enum_value<Variant> && variant_type != expected_variant_type) {
			throw std::runtime_error("variant of type '"
				+ with_variant_type(variant_type,
					[]<VariantType T>(){ return variant_type_name<T>; }) // XXX
				+ "' is not castable to variant of type "
				+ with_variant_type(expected_variant_type,
					[]<VariantType T>(){ return variant_type_name<T>; }) // XXX
			);
		}

		auto* ptr = maybe_emplace_and_get_pointer(expected_variant_type);

		if constexpr(UninitializedPointer<Ptr>) {
			if(!std::holds_alternative<std::monostate>(cast_temp_value)) {
				throw std::runtime_error("python object of type '"
					+ get_fully_qualified_name(py::type::handle_of(obj))
					+ "' is not castable as an uninitialized variant");
			}
		}

		return reinterpret_cast<Ptr>(ptr);
	}

public:
	cast_intermediate_t(const ObjectType& obj, GDExtensionVariantType variant_type)
		: obj(obj), variant_type(variant_type)
	{
	}

	// variant type

	template<MaybeUninitializedVariantValuePointer Ptr>
	operator Ptr() {
		return cast<Ptr>(variant_type);
	}

	// variant

	template<MaybeUninitializedVariantPointer Ptr>
	operator Ptr() {
		return cast<Ptr>(variant_type_to_enum_value<Variant>);
	}

	// string

	template<MaybeUninitializedStringPointer Ptr>
	operator Ptr() {
		return cast<Ptr>(variant_type_to_enum_value<String>);
	}

	// string name

	template<MaybeUninitializedStringNamePointer Ptr>
	operator Ptr() {
		return cast<Ptr>(variant_type_to_enum_value<StringName>);
	}
};







// cast a variant type pointer to a py::object reference to use to write back a ret result
// the pointer will be written to when the returned temporary intermediate is destroyed
// implicit casts are preformed when writing to the pointer (py to var implicit above)


// wants obj to ptr
// also ref(obj) to ptr
template<MaybeUninitializedPointer Pointer>
struct cast_intermediate_t<Pointer> {
private:
	GDExtensionTypePtr ptr;

	py::handle python_type = nullptr;

	GDExtensionVariantType variant_type;
	bool initialized;

	cast_intermediate_t() = delete;
	cast_intermediate_t(const cast_intermediate_t&) = delete;
	cast_intermediate_t(cast_intermediate_t&&) = delete;

public:
	template<MaybeUninitializedVariantPointer Pointer_>
	cast_intermediate_t(Pointer_ ptr, py::handle python_type = nullptr)
		: ptr(reinterpret_cast<GDExtensionTypePtr>(ptr))
		, python_type(python_type)
		, variant_type(variant_type_to_enum_value<Variant>)
		, initialized(InitializedPointer<Pointer_>)
	{
		//static_assert(!is_element_const_v<Pointer_>);
	}

	template<MaybeUninitializedStringPointer Pointer_>
	cast_intermediate_t(Pointer_ ptr, py::handle python_type = nullptr)
		: ptr(reinterpret_cast<GDExtensionTypePtr>(ptr))
		, python_type(python_type)
		, variant_type(variant_type_to_enum_value<String>)
		, initialized(InitializedPointer<Pointer_>)
	{
		//static_assert(!is_element_const_v<Pointer_>);
	}

	template<MaybeUninitializedStringNamePointer Pointer_>
	cast_intermediate_t(Pointer_ ptr, py::handle python_type = nullptr)
		: ptr(reinterpret_cast<GDExtensionTypePtr>(ptr))
		, python_type(python_type)
		, variant_type(variant_type_to_enum_value<StringName>)
		, initialized(InitializedPointer<Pointer_>)
	{
		//static_assert(!is_element_const_v<Pointer_>);
	}

	template<MaybeUninitializedVariantValuePointer Pointer_>
	cast_intermediate_t(Pointer_ ptr, GDExtensionVariantType variant_type, py::handle python_type = nullptr)
		: ptr(reinterpret_cast<GDExtensionTypePtr>(ptr))
		, python_type(python_type)
		, variant_type(variant_type)
		, initialized(InitializedPointer<Pointer_>)
	{
	}

	operator py::object() {
		return make_copy(reinterpret_cast<Pointer>(ptr), variant_type, python_type);
	}

	template<PythonObject ObjectType>
	auto operator=(ObjectType obj) {
		if(!obj && python_type) { // XXX
			static py::handle Error = resolve_name("godot.Error");
			if(python_type.ptr() == Error.ptr()) {
				obj = Error.attr("FAILED");
			}
		}
		return make_copy(reinterpret_cast<Pointer>(ptr), obj, variant_type);
	}

	operator py::str() {
		if(variant_type == variant_type_to_enum_value<String>
			|| variant_type == variant_type_to_enum_value<StringName>
			|| variant_type == variant_type_to_enum_value<Variant>)
		{
			if(!python_type) {
				python_type = reinterpret_cast<PyObject*>(&PyUnicode_Type);
			}
			return operator py::object();
		}
		else {
			throw std::runtime_error("cannot cast variant to py::str");
		}
	}

	auto operator=(const py::str& other) {
		return operator=(static_cast<const py::object&>(other));
	}

	/*operator py::object&() {
		return obj;
	}

	operator py::object*() {
		return &obj;
	}*/
};




template<PythonObjectReferenceWrapper WrapperType>
auto cast(WrapperType obj,
	GDExtensionVariantType variant_type, py::handle python_type)
{
	return cast_intermediate_t<WrapperType>(obj, variant_type, python_type);
}

template<PythonObjectReferenceWrapper WrapperType>
auto cast(WrapperType obj,
	std::pair<GDExtensionVariantType, py::handle> type)
{
	return cast_intermediate_t<WrapperType>(obj, type.first, type.second);
}


template<PythonObject ObjectType>
auto cast(ObjectType obj, GDExtensionVariantType variant_type) {
	return cast_intermediate_t<std::decay_t<ObjectType>>(obj, variant_type);
}


template<MaybeUninitializedPointer Pointer>
auto cast(Pointer ptr) {
	if constexpr(is_element_const_v<Pointer>) {
		return py::object(cast_intermediate_t<Pointer>(const_cast<remove_element_const_t<Pointer>>(ptr)));
	}
	else {
		return cast_intermediate_t<Pointer>(const_cast<remove_element_const_t<Pointer>>(ptr));
	}
}

template<MaybeUninitializedVariantValuePointer Pointer>
auto cast(Pointer ptr, GDExtensionVariantType variant_type) {
	if constexpr(is_element_const_v<Pointer>) {
		return py::object(cast_intermediate_t<Pointer>(const_cast<remove_element_const_t<Pointer>>(ptr), variant_type));
	}
	else {
		return cast_intermediate_t<Pointer>(const_cast<remove_element_const_t<Pointer>>(ptr), variant_type);
	}
}

/*template<VariantValuePointer Pointer>
py::object cast(Pointer ptr,
	GDExtensionVariantType variant_type, py::handle python_type)
{
	return cast_intermediate_t<Pointer>(const_cast<remove_element_const_t<Pointer>>(ptr),
		variant_type, python_type);
}*/ // XXX

template<VariantValuePointer Pointer>
auto cast(Pointer ptr,
	std::pair<GDExtensionVariantType, py::handle> type)
{
	if constexpr(is_element_const_v<Pointer>) {
		return py::object(cast_intermediate_t<Pointer>(const_cast<remove_element_const_t<Pointer>>(ptr),
			type.first, type.second));
	}
	else {
		return cast_intermediate_t<Pointer>(const_cast<remove_element_const_t<Pointer>>(ptr),
			type.first, type.second);
	}
}


inline py::object cast(GDExtensionObjectPtr ptr) {
	return Object::get_bound_instance(ptr);
}

inline py::object cast(GDExtensionConstObjectPtr ptr) {
	return Object::get_bound_instance(const_cast<GDExtensionObjectPtr>(ptr));
}





} // namespace pygodot


#include "casting/make_copy.h"


