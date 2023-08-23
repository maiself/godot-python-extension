#pragma once

#include <pybind11/pybind11.h>

#include "extension/extension.h"
#include "util/exceptions.h"
#include "variant/traits.h"
#include "variant/variant.h"
#include "variant/object.h"
#include "variant/callable.h"

#include "casting/cast.h"


namespace pygodot {


// variant pointer -> variant pointer

template<MaybeUninitializedPointer DestPointer, InitializedPointer SourcePointer>
auto make_copy(DestPointer dest, SourcePointer src, GDExtensionVariantType variant_type) {
	static_assert(!MaybeUninitializedVariantPointer<DestPointer>);
	static_assert(!VariantPointer<SourcePointer>);

	static_assert(UninitializedPointer<DestPointer>
		|| std::is_same_v<DestPointer, remove_element_const_t<SourcePointer>>);

	const auto constructor = extension_interface::variant_get_ptr_constructor(variant_type, 1); // XXX

	if(!constructor) {
		throw std::runtime_error("invalid variant constructor 91");
		// XXX: initialize uninitialized variant?
	}

	if constexpr(!UninitializedPointer<DestPointer>) {
		with_variant_type(variant_type, [dest]<VariantType Type>() {
			reinterpret_cast<Type*>(dest)->~Type();
		});
	}

	constructor(uninitialized(dest),
		std::array<GDExtensionConstTypePtr, 1>{reinterpret_cast<GDExtensionConstTypePtr>(src)}.data());

	return reinterpret_cast<as_initialized_pointer_t<DestPointer>>(dest);
}


// variant pointer -> python object

template<InitializedPointer Pointer>
py::object make_copy(Pointer ptr, GDExtensionVariantType variant_type, py::handle python_type/* = nullptr*/) {
	assert(!VariantPointer<Pointer> || variant_type == variant_type_to_enum_value<Variant>);
	assert(!StringPointer<Pointer> || variant_type == variant_type_to_enum_value<String>);
	assert(!StringNamePointer<Pointer> || variant_type == variant_type_to_enum_value<StringName>);

	if(!ptr) {
		return py::none();
	}

	return with_variant_type(variant_type, [ptr, python_type]<VariantType Type>() -> py::object {
		const Type& val = *reinterpret_cast<const Type*>(ptr);

		py::object obj;

		if constexpr(std::is_same_v<Type, GDExtensionBool>) {
			obj = py::bool_(val);
		}
		else if constexpr(std::is_same_v<Type, GDExtensionInt>) {
			obj = py::int_(val);
		}
		else if constexpr(std::is_same_v<Type, GDExtensionFloat>) {
			obj = py::float_(val);
		}

		else if constexpr(std::is_same_v<Type, Object>) {
			obj = cast(*reinterpret_cast<const GDExtensionConstObjectPtr*>(ptr));
			return obj; // XXX: python_type?
		}

		else if constexpr(std::is_same_v<Type, Variant>) {
			GDExtensionVariantType variant_type = extension_interface::variant_get_type(val);
			if(variant_type == variant_type_to_enum_value<Variant>) {
				return py::none();
			}
			auto constructor = extension_interface::get_variant_to_type_constructor(variant_type);
			if(!constructor) {
				throw std::runtime_error("invalid variant constructor");
			}
			constructor(cast(std::ref(obj), variant_type, python_type), const_cast<Type&>(val)); // XXX
			return obj;
		}

		else {
			if constexpr(std::is_same_v<Type, String> || std::is_same_v<Type, StringName>) {
				if(python_type.ptr() == reinterpret_cast<PyObject*>(&PyUnicode_Type)) {
					return py::str(val);
				}
			}

			if constexpr(std::is_same_v<Type, Callable>) {
				auto* obj_ptr = static_cast<PyObject*>(extension_interface::callable_custom_get_userdata(
					val, nullptr));
				if(obj_ptr) {
					return py::reinterpret_borrow<py::function>(obj_ptr);
				}
			}

			Type* obj_ptr;

			if constexpr(std::is_same_v<Type, Array>) { // XXX XXX
				obj = resolve_name("godot.Array")();
				obj_ptr = py::cast<Type*>(obj);
			}
			else {
				obj_ptr = new Type(uninitialized); // uninitialized variant value
				obj = py::cast(obj_ptr, py::return_value_policy::take_ownership);
			}

			auto constructor = extension_interface::variant_get_ptr_constructor(
				variant_type_to_enum_value<Type>, 1); // XXX
			if(!constructor) {
				throw std::runtime_error("invalid variant constructor");
			}
			constructor(uninitialized(obj_ptr),
				std::array<GDExtensionConstTypePtr, 1>{val}.data());

			if constexpr(std::is_same_v<Type, Array>) { // XXX
				obj.attr("_set_as_typed")();
				/*py::int_ v = obj.attr("get_typed_builtin")();

				if(int(v) > 0) {
					auto n = with_variant_type(GDExtensionVariantType(int(v)), []<typename T>() {
						if constexpr(std::is_fundamental_v<T>) {
							return variant_type_name<T>;
						}
						else {
							return "godot." + variant_type_name<T>;
						}
					});
					auto t = resolve_name("godot.Array[" + n + "]");

					obj.attr("__class__") = t;
				}*/
			}
		}

		if(python_type && !python_type.is_none()) {
			return python_type(obj);
		}
		else {
			return obj;
		}
	});
}


// python object -> variant pointer

template<MaybeUninitializedPointer Pointer, PythonObject ObjectType>
auto make_copy(Pointer ptr, ObjectType obj, GDExtensionVariantType variant_type)
	-> as_initialized_pointer_t<Pointer>
{
	static_assert(!is_element_const_v<Pointer>);

	assert(!MaybeUninitializedVariantPointer<Pointer>
		|| variant_type == variant_type_to_enum_value<Variant>);
	assert(!MaybeUninitializedStringPointer<Pointer>
		|| variant_type == variant_type_to_enum_value<String>);
	assert(!MaybeUninitializedStringNamePointer<Pointer>
		|| variant_type == variant_type_to_enum_value<StringName>);

	constexpr bool initialized = InitializedPointer<Pointer>;

	if(!ptr) {
		if(obj && !obj.is_none()) {
			throw std::runtime_error("cannot copy python object of type '"
				+ get_fully_qualified_name(py::type::handle_of(obj))
				+ "' to nullptr");
		}
		return nullptr;
	}

	if(!obj) {
		with_variant_type(variant_type, [ptr]<VariantType Type>() {
			if constexpr(std::is_same_v<Type, Object>) {
				*reinterpret_cast<GDExtensionObjectPtr*>(ptr) = nullptr;
			}
			else if constexpr(!initialized || std::is_trivially_constructible_v<Type>) { // XXX
				::new(reinterpret_cast<Type*>(ptr)) Type();
			}
		});
		return reinterpret_cast<as_initialized_pointer_t<Pointer>>(ptr);
	}

	with_variant_type(variant_type, [ptr, obj]<VariantType Type>() {
		Type& ref = *reinterpret_cast<Type*>(ptr);

		if constexpr(std::is_same_v<Type, GDExtensionBool>) {
			ref = static_cast<Type>(py::cast<py::bool_>(obj)); // bool(obj)
		}
		else if constexpr(std::is_same_v<Type, GDExtensionInt>) {
			ref = static_cast<Type>(py::cast<py::int_>(obj)); // int(obj)
		}
		else if constexpr(std::is_same_v<Type, GDExtensionFloat>) {
			ref = static_cast<Type>(py::cast<py::float_>(obj)); // float(obj)
		}

		else if constexpr(std::is_same_v<Type, Object>) {
			if(obj.is_none()) {
				*reinterpret_cast<GDExtensionObjectPtr*>(ptr) = nullptr;
			}
			else {
				*reinterpret_cast<GDExtensionObjectPtr*>(ptr) = *py::cast<Object*>(obj);
			}
		}

		else if constexpr(std::is_same_v<Type, Variant>) {
			auto variant_type = variant_type_from_instance_inferred_checked(obj);

			if constexpr(initialized) {
				ref.~Type();
			}

			if(obj.is_none()) {
				::new(&ref) Type();
			}
			else {
				auto constructor = extension_interface::get_variant_from_type_constructor(variant_type);
				if(!constructor) {
					throw std::runtime_error("invalid variant constructor");
				}
				constructor(uninitialized(ref), cast(obj, variant_type));
			}
		}

		else if(py::isinstance<Type>(obj)) {
			if constexpr(!MaybeUninitializedVariantPointer<Pointer>) { // XXX
				make_copy(ptr, reinterpret_cast<as_initialized_pointer_t<Pointer>>(py::cast<Type*>(obj)),
					variant_type_to_enum_value<Type>);
			}
			// XXX: error here?
		}

		else if constexpr(std::is_same_v<Type, String> || std::is_same_v<Type, StringName>) {
			// XXX: node path?
			if(!PyUnicode_Check(obj.ptr())) {
				throw make_type_error(py::type::handle_of(obj),
					py::type::handle_of<Type>(), "str");
			}

			if constexpr(initialized) {
				ref.~Type();
			}

			::new(&ref) Type(py::cast<py::str>(obj));
		}
		else if constexpr(std::is_same_v<Type, Dictionary>) {
			if(!PyMapping_Check(obj.ptr())) {
				throw make_type_error(py::type::handle_of(obj),
					py::type::handle_of<Type>(), "mapping");
			}

			auto dict = py::cast<py::dict>(obj); // dict(obj) // XXX: makes a copy

			if constexpr(!initialized) {
				::new(&ref) Type();
			}

			auto setter = extension_interface::variant_get_ptr_keyed_setter(variant_type_to_enum_value<Type>);

			for(auto [key, value] : dict) {
				setter(ref,
					cast(key, variant_type_to_enum_value<Variant>),
					cast(value, variant_type_to_enum_value<Variant>)
				); // XXX
			}
		}
		else if constexpr(is_in_type_list<Type, variant_array_type_list>) {//VariantArrayType<Type>) {
			if(!PySequence_Check(obj.ptr())) {
				throw make_type_error(py::type::handle_of(obj),
					py::type::handle_of<Type>(), "sequence");
			}

			auto seq = py::cast<py::sequence>(obj); // (obj) if seq

			if constexpr(!initialized) {
				::new(&ref) Type();
			}

			variant_type_handle<Type>().attr("resize")(
				py::cast(ref, py::return_value_policy::reference), seq.size()); // XXX

			//py::cast(ref, py::return_value_policy::reference).attr("resize")(seq.size()); // XXX

			auto setter = extension_interface::variant_get_ptr_indexed_setter(variant_type_to_enum_value<Type>);

			using ElementType = variant_array_element_type<Type>;
			const auto element_type = variant_type_to_enum_value<ElementType>;

			size_t index = 0;
			for(const py::object& item : seq) {
				setter(ref, index++, cast(item, element_type)); // XXX
			}
		}
		else if constexpr(std::is_same_v<Type, Callable>) {
			if(!PyCallable_Check(obj.ptr())) {
				throw make_type_error(py::type::handle_of(obj),
					py::type::handle_of<Type>(), "callable");
			}

			auto func = py::cast<py::function>(obj);

			if constexpr(initialized) {
				ref.~Type();
			}

			func_to_callable(uninitialized(ref), func); // XXX: move to new file?
		}
		else {
			throw std::runtime_error("python object of type '"
				+ get_fully_qualified_name(py::type::handle_of(obj))
				+ "' is not castable to variant of type " + variant_type_name<Type>);
		}
	});

	return reinterpret_cast<as_initialized_pointer_t<Pointer>>(ptr);
}


} // namespace pygodot


