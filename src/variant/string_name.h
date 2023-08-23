#pragma once

#include "extension/extension.h"
#include "variant/variant_base.h"
#include "variant/string.h"


namespace godot {


namespace py = pybind11;


class StringName : public VariantTypeBase<StringName>
{
public:
	using VariantTypeBase::VariantTypeBase;

	using VariantTypeBase::operator GDExtensionTypePtr;
	using VariantTypeBase::operator GDExtensionConstTypePtr;

	typedef GDExtensionUninitializedStringNamePtr uninitialized_ptr_t;

	StringName();

	StringName(StringName&& other);
	StringName(const StringName& other);
	StringName(const String& other);

	StringName(const char* str);
	StringName(const std::string& str);
	StringName(const py::str& str);

	StringName& operator=(const StringName& other);
	StringName& operator=(StringName&& other);

	operator GDExtensionConstStringNamePtr() const {
		return reinterpret_cast<GDExtensionConstStringNamePtr>(this);
	}

	operator GDExtensionStringNamePtr() {
		return reinterpret_cast<GDExtensionStringNamePtr>(this);
	}

	operator std::string() const;
	operator py::str() const;

	/*bool operator==(const StringName& other) const;
	bool operator!=(const StringName& other) const;*/

	static void pre_def(py::module_& module_);
	static void def(py::module_& module_);
};


} // namespace godot


