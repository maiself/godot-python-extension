#pragma once

#include <array>

#include <pybind11/pybind11.h>

#include "extension/extension.h"
#include "variant/traits.h"


namespace pygodot {


namespace py = pybind11;


struct uninitialized_t {
	template<MaybeUninitializedPointer Pointer>
		requires (MaybeUninitializedStringPointer<Pointer> || MaybeUninitializedStringNamePointer<Pointer>)
	auto operator()(Pointer ptr) const {
		static_assert(!is_element_const_v<Pointer>);
		struct {
			Pointer ptr;
			operator as_uninitialized_pointer_t<Pointer>() const {
				return reinterpret_cast<as_uninitialized_pointer_t<Pointer>>(ptr);
			}
			operator GDExtensionUninitializedTypePtr() const {
				return reinterpret_cast<GDExtensionUninitializedTypePtr>(ptr);
			}
		} res{ptr};
		return res;
	}

	template<MaybeUninitializedPointer Pointer>
	auto operator()(Pointer ptr) const {
		static_assert(!is_element_const_v<Pointer>);
		return reinterpret_cast<as_uninitialized_pointer_t<Pointer>>(ptr);
	}

	template<typename T> requires requires (T) { typename T::uninitialized_ptr_t; }
	auto operator()(T& value) const {
		return operator()(reinterpret_cast<typename T::uninitialized_ptr_t>(&value));
	}

	template<typename T> requires requires (T) { typename T::uninitialized_ptr_t; }
	auto operator()(T* value) const {
		return operator()(reinterpret_cast<typename T::uninitialized_ptr_t>(value));
	}
};

static const inline uninitialized_t uninitialized;


template<typename Type>
inline auto def_init_uninitialized(Type&& cls) {
	py::function init_uninitialized = cls.def(py::init([]() {
		return new typename std::decay_t<Type>::type(uninitialized);
	})).attr("__init__");
	py::delattr(cls, "__init__");
	cls.attr("__init_uninitialized__") = init_uninitialized;
	return std::forward<Type>(cls);
}


template<VariantType Type>
class VariantTypeBase {
	Type* this_as_type() {
		return static_cast<Type*>(this);
	}

protected:
	std::aligned_storage_t<variant_type_size<Type>> data;

	template<int constructor_index, typename... Args>
	void construct(Args&&... args) {
		static const GDExtensionPtrConstructor constructor =
			extension_interface::variant_get_ptr_constructor(
				variant_type_to_enum_value<Type>, constructor_index);

		constructor(uninitialized(this_as_type()),
			std::array<GDExtensionConstTypePtr, sizeof...(Args)>{{std::forward<Args>(args)...}}.data());
	}

public:
	VariantTypeBase(const uninitialized_t&) {
	}

	VariantTypeBase(const VariantTypeBase&) = delete;
	VariantTypeBase(VariantTypeBase&&) = delete;

	VariantTypeBase() : VariantTypeBase(uninitialized) {
		construct<0>();
	}

	VariantTypeBase(GDExtensionConstVariantPtr other) : VariantTypeBase(uninitialized) {
		extension_interface::get_variant_to_type_constructor(variant_type_to_enum_value<Type>)(
			*this_as_type(),
			const_cast<GDExtensionVariantPtr>(other)
		);
	}

	~VariantTypeBase() {
		if(auto* destructor
			= extension_interface::variant_get_ptr_destructor(variant_type_to_enum_value<Type>))
		{
			destructor(*this_as_type());
		}
	}

	operator GDExtensionTypePtr() {
		return reinterpret_cast<GDExtensionTypePtr>(this);
	}

	operator GDExtensionConstTypePtr() const {
		return reinterpret_cast<GDExtensionConstTypePtr>(this);
	}
};


#define EMPTY_VARIANT_TYPE(type_name) \
class type_name : public VariantTypeBase<type_name> { \
	typedef py::class_<type_name> class_def_t; \
	static inline std::unique_ptr<class_def_t> class_def; \
	\
public: \
	using VariantTypeBase::VariantTypeBase; \
	\
	using VariantTypeBase::operator GDExtensionTypePtr; \
	using VariantTypeBase::operator GDExtensionConstTypePtr; \
	\
	typedef GDExtensionUninitializedTypePtr uninitialized_ptr_t; \
	\
	static void pre_def(py::module_& module_) { \
		class_def = std::make_unique<class_def_t>(module_, #type_name); \
	} \
	static void def(py::module_& module_) { \
		def_init_uninitialized(*class_def); \
		class_def.reset(); \
	} \
};

} // namespace pygodot

namespace godot {

using namespace pygodot;

//EMPTY_VARIANT_TYPE(Variant)
//EMPTY_VARIANT_TYPE(GDExtensionBool)
//EMPTY_VARIANT_TYPE(GDExtensionInt)
//EMPTY_VARIANT_TYPE(GDExtensionFloat)
//EMPTY_VARIANT_TYPE(String)
EMPTY_VARIANT_TYPE(Vector2)
EMPTY_VARIANT_TYPE(Vector2i)
EMPTY_VARIANT_TYPE(Rect2)
EMPTY_VARIANT_TYPE(Rect2i)
EMPTY_VARIANT_TYPE(Vector3)
EMPTY_VARIANT_TYPE(Vector3i)
EMPTY_VARIANT_TYPE(Transform2D)
EMPTY_VARIANT_TYPE(Vector4)
EMPTY_VARIANT_TYPE(Vector4i)
EMPTY_VARIANT_TYPE(Plane)
EMPTY_VARIANT_TYPE(Quaternion)
EMPTY_VARIANT_TYPE(AABB)
EMPTY_VARIANT_TYPE(Basis)
EMPTY_VARIANT_TYPE(Transform3D)
EMPTY_VARIANT_TYPE(Projection)
EMPTY_VARIANT_TYPE(Color)
//EMPTY_VARIANT_TYPE(StringName)
EMPTY_VARIANT_TYPE(NodePath)
EMPTY_VARIANT_TYPE(RID)
//EMPTY_VARIANT_TYPE(Object)
EMPTY_VARIANT_TYPE(Callable)
EMPTY_VARIANT_TYPE(Signal)
EMPTY_VARIANT_TYPE(Dictionary)
EMPTY_VARIANT_TYPE(Array)
EMPTY_VARIANT_TYPE(PackedByteArray)
EMPTY_VARIANT_TYPE(PackedInt32Array)
EMPTY_VARIANT_TYPE(PackedInt64Array)
EMPTY_VARIANT_TYPE(PackedFloat32Array)
EMPTY_VARIANT_TYPE(PackedFloat64Array)
EMPTY_VARIANT_TYPE(PackedStringArray)
EMPTY_VARIANT_TYPE(PackedVector2Array)
EMPTY_VARIANT_TYPE(PackedVector3Array)
EMPTY_VARIANT_TYPE(PackedColorArray)
EMPTY_VARIANT_TYPE(PackedVector4Array)

#undef EMPTY_VARIANT_TYPE

} // namespace godot


