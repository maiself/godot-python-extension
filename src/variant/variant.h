#pragma once

#include <pybind11/pybind11.h>

#include "variant/variant_base.h"


namespace godot {


namespace py = pybind11;


class Variant {
	std::aligned_storage_t<variant_type_size<Variant>> data;

public:
	typedef GDExtensionUninitializedVariantPtr uninitialized_ptr_t;

	Variant(const uninitialized_t&) {
	}

	//Variant(const Variant&) = delete;
	//Variant(Variant&&) = delete;

	Variant() : Variant(uninitialized) {
		extension_interface::variant_new_nil(uninitialized(this));
	}

	~Variant() {
		extension_interface::variant_destroy(*this);
	}

	operator GDExtensionVariantPtr() {
		return reinterpret_cast<GDExtensionVariantPtr>(this);
	}

	operator GDExtensionConstVariantPtr() const {
		return reinterpret_cast<GDExtensionConstVariantPtr>(this);
	}

	operator GDExtensionTypePtr() {
		return reinterpret_cast<GDExtensionTypePtr>(this);
	}

	operator GDExtensionConstTypePtr() const {
		return reinterpret_cast<GDExtensionConstTypePtr>(this);
	}

	static void pre_def(py::module_& module_);
	static void def(py::module_& module_);
};


} // namespace godot


