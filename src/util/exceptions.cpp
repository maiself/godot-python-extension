#include "util/exceptions.h"


namespace pygodot {


py::object get_exception_value(const py::error_already_set& exception) {
	return exception.value();
}


py::object get_exception_value(const py::builtin_exception& exception) {
	exception.set_error();
	py::object type, value, trace;
	PyErr_Fetch(&type.ptr(), &value.ptr(), &trace.ptr());
	PyErr_NormalizeException(&type.ptr(), &value.ptr(), &trace.ptr());
	return value;
}


std::string format_exception_value(py::object value) {
	py::handle format_exception;
	try {
		format_exception = resolve_name("godot._internal.utils.format_exception");
	}
	catch(...) {
		format_exception = py::module_::import("traceback").attr("format_exception");
	}
	return py::str("").attr("join")(format_exception(value)).attr("removesuffix")("\n").cast<py::str>();
}


std::string get_fully_qualified_name(py::handle obj) {
	try {
		py::object name = py::getattr(obj, "__qualname__");
		if(name.is_none()) {
			name = py::getattr(obj, "__name__");
		}
		if(name.is_none()) {
			return py::str(obj);
		}
		py::object mod = py::getattr(obj, "__module__");
		if(mod.is_none() || mod.equal(py::str("builtins"))) {
			return py::str(name);
		}
		return py::str(mod + py::str(".") + name);
	}
	catch(...) {
		return py::str(obj);
	}
}


} // namespace pygodot

