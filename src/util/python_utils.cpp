#include <pybind11/pybind11.h>
#include <pybind11/eval.h>

#include "util/python_utils.h"


#include "extension/extension.h"


namespace pygodot {


static std::vector<resolved_name*> resolved_names;


py::object resolve_name(py::str name) {
	static py::function resolve_name;

	if(!resolve_name) {
		resolve_name = py::module_::import("godot._internal.utils").attr("resolve_name");

		register_cleanup_func([]() {
			resolve_name = py::object();

			while(!resolved_names.empty()) {
				resolved_names.front()->reset();
			}

			resolved_names.clear();
		});
	}

	return resolve_name(name);
}


resolved_name::resolved_name(py::str name) {
	py::object::operator=(resolve_name(name));

	//py::print("\033[36;1m", "cached name '", name, "' -> ", this, "\033[0m", py::arg("sep") = py::str(""));

	resolved_names.push_back(this);
}


resolved_name::~resolved_name() {
	reset();
}


void resolved_name::reset() {
	if(!*this) {
		return;
	}

	std::erase(resolved_names, this);

	if(!Py_IsInitialized()) {
		//printf("\033[36;1m" "released cached name " "???" "\033[0m" "\n");
		return;
	}

	py::gil_scoped_acquire gil;

	//py::print("\033[36;1m", "released cached name ", this, "\033[0m", py::arg("sep") = py::str(""));

	py::object::operator=(py::object());
}


bool issubclass(py::handle cls, py::handle class_or_tuple) {
	const auto res = PyObject_IsSubclass(cls.ptr(), class_or_tuple.ptr());
	if(res == -1) {
		throw py::error_already_set();
	}
	return res != 0;
}


} // namespace pygodot

