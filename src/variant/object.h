#pragma once

#include <pybind11/pytypes.h>

#include "extension/extension.h"
#include "variant/variant_base.h"
#include "variant/string_name.h"
#include "util/call_deferred.h"


namespace godot {


namespace py = pybind11;


class Object {
private:
	GDExtensionObjectPtr _ptr = nullptr;
	py::handle _handle = nullptr;

	deferred_call_t* _deferred_release = nullptr;

	bool _is_reference_counted = false;

	void _free();
	bool _reference(bool reference);

	int _traverse(PyObject* self_base, visitproc visit, void* arg);
	void _clear(PyObject* self_base);

	void _destroy();

	friend class _ObjectAccessor;

	Object() = delete;
	Object(const Object&) = delete;
	Object(Object&&) = delete;

	Object(GDExtensionObjectPtr ptr);
	Object(const py::str& class_name, const py::str& base_class_name);

public:
	~Object();

	StringName get_class_name() const;

	bool is_reference_counted() const;
	size_t get_reference_count() const;

	bool init_ref();
	bool reference();
	bool unreference();

	operator GDExtensionTypePtr() { // XXX
		return reinterpret_cast<GDExtensionTypePtr>(&_ptr);
	}

	operator GDExtensionConstTypePtr() const { // XXX
		return reinterpret_cast<GDExtensionConstTypePtr>(&_ptr);
	}

	operator GDExtensionObjectPtr&() {
		return _ptr;
	}

	static py::object get_bound_instance(GDExtensionObjectPtr ptr);

	static void pre_def(py::module_& module_);
	static void def(py::module_& module_);
};


} // namespace godot


