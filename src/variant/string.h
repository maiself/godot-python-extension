#pragma once

#include "extension/extension.h"
#include "variant/variant_base.h"


namespace godot {


namespace py = pybind11;


class StringName;


class String : public VariantTypeBase<String>
{
public:
	using VariantTypeBase::VariantTypeBase;

	using VariantTypeBase::operator GDExtensionTypePtr;
	using VariantTypeBase::operator GDExtensionConstTypePtr;

	typedef GDExtensionUninitializedStringPtr uninitialized_ptr_t;

	String();
	String(String&& other);
	String(const String& other);
	String(const StringName& other);

	//String(const NodePath &from);

	String(const char* str);
	String(const std::string& str);
	String(const py::str& str);

	String& operator=(const String& other);
	String& operator=(String&& other);

	operator GDExtensionConstStringPtr() const {
		return reinterpret_cast<GDExtensionConstStringPtr>(this);
	}

	operator GDExtensionStringPtr() {
		return reinterpret_cast<GDExtensionStringPtr>(this);
	}

	operator std::string() const;
	operator py::str() const;

	static void pre_def(py::module_& module_);
	static void def(py::module_& module_);
};


} // namespace godot


