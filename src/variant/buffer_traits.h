#pragma once

#include <pybind11/pybind11.h>

#include "extension/extension.h"
#include "variant/traits.h"

#include "util/garbage_collection_type_setup.h"


namespace pygodot {


// variant buffer traits

using variant_buffer_type_list = concat_type_lists<
#define GDEXTENSION_BUFFER_TYPE(type_name, type_size, base_type, ndim, shape, strides) \
	type_name,
	GDEXTENSION_BUFFER_TYPES
#undef GDEXTENSION_BUFFER_TYPE
	type_list<>
>;

template<typename T>
concept VariantBufferType = is_in_type_list<T, variant_buffer_type_list>;


template<VariantBufferType T>
auto* variant_buffer_ptrw(T& obj) {
#define VARIANT_BUFFER_TYPE(buffer_type, func) \
	else if constexpr(std::is_same_v<std::decay_t<T>, buffer_type>) \
		{ return extension_interface::func##_operator_index(obj, 0); }

	if constexpr(false) {}
	VARIANT_BUFFER_TYPE(PackedByteArray, packed_byte_array)
	VARIANT_BUFFER_TYPE(PackedInt32Array, packed_int32_array)
	VARIANT_BUFFER_TYPE(PackedInt64Array, packed_int64_array)
	VARIANT_BUFFER_TYPE(PackedFloat32Array, packed_float32_array)
	VARIANT_BUFFER_TYPE(PackedFloat64Array, packed_float64_array)

#undef VARIANT_BUFFER_TYPE

#define VARIANT_BUFFER_TYPE(buffer_type, func, type) \
	else if constexpr(std::is_same_v<std::decay_t<T>, buffer_type>) \
		{ return (type*)extension_interface::func##_operator_index(obj, 0); }

	VARIANT_BUFFER_TYPE(PackedVector2Array, packed_vector2_array, Vector2)
	VARIANT_BUFFER_TYPE(PackedVector3Array, packed_vector3_array, Vector3)
	VARIANT_BUFFER_TYPE(PackedColorArray, packed_color_array, Color)
	VARIANT_BUFFER_TYPE(PackedVector4Array, packed_vector4_array, Vector4)

#undef VARIANT_BUFFER_TYPE

	else {
		return &obj;
	}
}


template<VariantBufferType T>
const auto* variant_buffer_ptr(const T& obj) {
#define VARIANT_BUFFER_TYPE(buffer_type, func) \
	else if constexpr(std::is_same_v<std::decay_t<T>, buffer_type>) \
		{ return extension_interface::func##_operator_index_const(obj, 0); }

	if constexpr(false) {}
	VARIANT_BUFFER_TYPE(PackedByteArray, packed_byte_array)
	VARIANT_BUFFER_TYPE(PackedInt32Array, packed_int32_array)
	VARIANT_BUFFER_TYPE(PackedInt64Array, packed_int64_array)
	VARIANT_BUFFER_TYPE(PackedFloat32Array, packed_float32_array)
	VARIANT_BUFFER_TYPE(PackedFloat64Array, packed_float64_array)

#undef VARIANT_BUFFER_TYPE

#define VARIANT_BUFFER_TYPE(buffer_type, func, type) \
	else if constexpr(std::is_same_v<std::decay_t<T>, buffer_type>) \
		{ return (const type*)extension_interface::func##_operator_index_const(obj, 0); }

	VARIANT_BUFFER_TYPE(PackedVector2Array, packed_vector2_array, Vector2)
	VARIANT_BUFFER_TYPE(PackedVector3Array, packed_vector3_array, Vector3)
	VARIANT_BUFFER_TYPE(PackedColorArray, packed_color_array, Color)
	VARIANT_BUFFER_TYPE(PackedVector4Array, packed_vector4_array, Vector4)

#undef VARIANT_BUFFER_TYPE

	else {
		return &obj;
	}
}


template<VariantBufferType T>
using variant_buffer_base_type = typename std::disjunction<
#define GDEXTENSION_BUFFER_TYPE(type_name, type_size, base_type, ndim, shape, strides) \
	bool_constant_and_type<std::is_same_v<T, type_name>, base_type>,
	GDEXTENSION_BUFFER_TYPES
#undef GDEXTENSION_BUFFER_TYPE
	std::true_type
>::type;


template<VariantBufferType T>
static constexpr size_t variant_buffer_base_type_size = []() {
	if constexpr(VariantType<variant_buffer_base_type<T>>) {
		return variant_type_size<variant_buffer_base_type<T>>;
	}
	else {
		return sizeof(variant_buffer_base_type<T>);
	}
}();


template<VariantBufferType T>
static constexpr size_t variant_buffer_ndim = []() -> size_t {
#define GDEXTENSION_BUFFER_TYPE(type_name, type_size, base_type, ndim, shape, strides) \
	if constexpr(std::is_same_v<T, type_name>) { return ndim; }
	GDEXTENSION_BUFFER_TYPES
#undef GDEXTENSION_BUFFER_TYPE
}();



template<VariantBufferType T>
static constexpr std::array<size_t, variant_buffer_ndim<T>> variant_buffer_shape;

#define GDEXTENSION_BUFFER_TYPE(type_name, type_size, base_type, ndim, shape, strides) \
	template<> constexpr std::array<size_t, variant_buffer_ndim<type_name>> \
		variant_buffer_shape<type_name>{shape};
	GDEXTENSION_BUFFER_TYPES
#undef GDEXTENSION_BUFFER_TYPE


template<VariantBufferType T>
static constexpr std::array<size_t, variant_buffer_ndim<T>> variant_buffer_strides;

#define GDEXTENSION_BUFFER_TYPE(type_name, type_size, base_type, ndim, shape, strides) \
	template<> constexpr std::array<size_t, variant_buffer_ndim<type_name>> \
		variant_buffer_strides<type_name>{strides};
	GDEXTENSION_BUFFER_TYPES
#undef GDEXTENSION_BUFFER_TYPE



template<VariantBufferType T, typename StringName = StringName> // XXX: workaround incomplete type
size_t variant_buffer_length(const T& obj) {
	if constexpr(VariantArrayType<T>) {
		static auto* size_method = extension_interface::variant_get_ptr_builtin_method(
			variant_type_to_enum_value<std::decay_t<T>>,
			StringName("size"), 3173160232); // () -> GDExtensionInt

		GDExtensionInt size = 0;
		size_method(const_cast<T&>(obj), nullptr, (GDExtensionTypePtr)&size, 0); // XXX: const_cast?

		return size;
	}

	return 1;
}


template<VariantBufferType T>
static inline const Py_buffer variant_buffer_default_structure = []() -> Py_buffer {
	static std::string format;
	ssize_t item_size;

	format = py::format_descriptor<variant_buffer_base_type<T>>::format();
	item_size = variant_buffer_base_type_size<T>;

	Py_buffer res = {
		nullptr, // buf
		nullptr, // obj
		0, // len
		item_size, // itemsize
		static_cast<int>(true), // readonly
		variant_buffer_ndim<T>, // ndim
		const_cast<char*>(format.data()), // format
		nullptr, // shape
		nullptr, // strides
		nullptr, // suboffsets
		nullptr, // internal
	};

	static Py_ssize_t shape[variant_buffer_ndim<T>];
	static Py_ssize_t strides[variant_buffer_ndim<T>];

	if(variant_buffer_ndim<T> > 0) {
		for(size_t i = 0; i < variant_buffer_ndim<T>; i++) {
			shape[i] = variant_buffer_shape<T>[i];
			strides[i] = variant_buffer_strides<T>[i];
		}
	}

	if(res.ndim) {
		res.shape = shape;
		res.strides = strides;
	}

	return res;
}();


template<VariantBufferType Type>
int variant_get_buffer(PyObject* obj_base, Py_buffer* view, int flags) {
	bool writable = static_cast<bool>(flags & PyBUF_WRITABLE);

	Type& source_obj = py::cast<Type&>(py::handle(obj_base));

	// trigger cow if writing (do before copy so that copy has same cow ptr)
	if(writable) {
		variant_buffer_ptrw(source_obj);
	}

	// copy to inc cow refcount
	// note: copy here means copying the obj that holds the cow data, not the data itself
	py::object copied_obj_py;

	if constexpr(VariantArrayType<Type>) {
		copied_obj_py = make_copy(static_cast<GDExtensionTypePtr>(source_obj),
			variant_type_to_enum_value<Type>, nullptr);
	}
	else {
		// the rest of the code and comments in this function are written assuming a cow type, but some types
		// are more like pod. this is the only branch where the difference is important, every whereelse
		// the difference is basically a no op

		// for non cow data we dont copy, and instead use a new reference to the existing object

		copied_obj_py = py::reinterpret_borrow<py::object>(obj_base);
	}

	Type& copied_obj = py::cast<Type&>(py::handle(copied_obj_py));

	// get the ptr from the copy (likely the same ptr, but safer to grab from local copy)
	const variant_buffer_base_type<Type>*
		buffer = reinterpret_cast<const variant_buffer_base_type<Type>*>(variant_buffer_ptr(copied_obj));

	// the original object and the copy now point to the same cow memory (or at least with very high likelihood)
	// (for read only view cow refcount is >= 2, for writable view cow refcount == 2, uncertainty from threading)
	// if a write happens to the original cow is triggered, but the copy still has a valid pointer
	// if a writable view was requested writes to the copy will be visible on the original without triggering cow
	// (cow not triggered on writes to writable copy as cow already happened before copy)

	// fill out buffer info

	*view = variant_buffer_default_structure<Type>;

	view->buf = const_cast<variant_buffer_base_type<Type>*>(buffer);
	view->obj = copied_obj_py.ptr();

	if(view->shape && view->shape[0] == 0) {
		std::unique_ptr<Py_ssize_t[]> shape(new Py_ssize_t[view->ndim]);

		shape[0] = variant_buffer_length(copied_obj);

		for(size_t i = 1; i < view->ndim; i++) {
			shape[i] = view->shape[i];
		}

		view->shape = shape.release();

		view->internal = static_cast<void*>(view->shape);
	}

	view->len = view->itemsize;

    for(size_t i = 0; i < view->ndim; i++) {
		view->len *= view->shape[i];
	}

	view->readonly = static_cast<int>(!writable);

	Py_INCREF(view->obj);
	return 0;
}


template<VariantBufferType Type>
void variant_release_buffer(PyObject* obj_base, Py_buffer* view) {
	if(view->internal) {
		std::unique_ptr<Py_ssize_t[]> shape(static_cast<Py_ssize_t*>(view->internal));
	}
}


class MemoryReference {
	py::object obj;
	py::buffer_info info;

	MemoryReference(py::object obj, py::buffer_info&& info)
		: obj(obj), info(std::move(info))
	{}

public:
	static py::memoryview from(py::object obj, py::buffer_info&& info) {
		bool readonly = info.readonly;

		return py::memoryview(
			py::buffer(
				py::cast(new MemoryReference(obj, std::move(info)),
					py::return_value_policy::take_ownership)
			).request(!readonly)
		);
	}

	static void def(py::module_& module_) {
		using type = MemoryReference;

		py::class_<type>(module_, "_MemoryReference",
			py::buffer_protocol(),
			py::custom_type_setup(garbage_collection_type_setup<type>()
				.collect(&type::obj)
			)
		)
			.def_readonly("obj", &type::obj)

			.def_buffer([](MemoryReference& ref) -> py::buffer_info {
				return py::buffer_info(
					ref.info.ptr,
					ref.info.itemsize,
					ref.info.format,
					ref.info.ndim,
					ref.info.shape,
					ref.info.strides,
					ref.info.readonly
				);
			})
		;
	}
};


} // namespace pygodot

