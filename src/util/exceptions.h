#pragma once

#include <string>
#include <cstdlib>
#include <cstdio>

#include <pybind11/pybind11.h>

#include "extension/extension.h"
#include "util/python_utils.h"


#ifdef _MSC_VER
#  define GENERATE_TRAP() __debugbreak()
#else
#  define GENERATE_TRAP() __builtin_trap()
#endif


namespace pygodot {


inline py::object get_exception_value(const py::error_already_set& exception) {
	return exception.value();
}

inline py::object get_exception_value(const py::builtin_exception& exception) {
	exception.set_error();
	py::object type, value, trace;
	PyErr_Fetch(&type.ptr(), &value.ptr(), &trace.ptr());
	PyErr_NormalizeException(&type.ptr(), &value.ptr(), &trace.ptr());
	return value;
}


template<typename Note>
py::object add_exception_note(py::object exception_value, Note&& note) {
	if constexpr(std::is_base_of_v<py::handle, Note> || std::is_convertible_v<Note, std::string>) {
		exception_value.attr("add_note")(py::str("  ") + py::str(std::forward<Note>(note)));
	}
	else {
		exception_value.attr("add_note")(py::str("  ") + py::str(std::forward<Note>(note)()));
	}
	return exception_value;
}

template<typename... Notes>
py::object add_exception_notes(py::object exception_value, Notes&&... notes) {
	return (add_exception_note(exception_value, std::forward<Notes>(notes)), ..., exception_value);
}


inline std::string format_exception_value(py::object value) {
	py::handle format_exception;
	try {
		format_exception = resolve_name("godot._internal.utils.format_exception");
	}
	catch(...) {
		format_exception = py::module_::import("traceback").attr("format_exception");
	}
	return py::str("").attr("join")(format_exception(value)).attr("removesuffix")("\n").cast<py::str>();
}


template<typename Exception, typename... Notes>
std::string format_exception(const Exception& exception, Notes&&... notes) {
	return format_exception_value(
		add_exception_notes(get_exception_value(exception), std::forward<Notes>(notes)...)
	);
}


#define CATCH_EXCEPTIONS_AND_PRINT_ERRORS_THEN(then, ...) \
	catch(const py::error_already_set& exception) { \
		extension_interface::print_error(format_exception(exception __VA_OPT__(,) __VA_ARGS__).data(), \
			__FUNCTION__, __FILE__, __LINE__, false); \
		do { then } while(0); \
	} \
	catch(const py::builtin_exception& exception) { \
		extension_interface::print_error(format_exception(exception __VA_OPT__(,) __VA_ARGS__).data(), \
			__FUNCTION__, __FILE__, __LINE__, false); \
		do { then } while(0); \
	} \
	catch(const std::exception& exception) { \
		extension_interface::print_error(exception.what(), __FUNCTION__, __FILE__, __LINE__, false); \
		do { then } while(0); \
	}


#define CATCH_EXCEPTIONS_AND_PRINT_ERRORS(...) \
	CATCH_EXCEPTIONS_AND_PRINT_ERRORS_THEN({}, __VA_ARGS__)


#define CATCH_FATAL_EXCEPTIONS_PRINT_ERRORS_AND_CRASH(...) \
	CATCH_EXCEPTIONS_AND_PRINT_ERRORS_THEN({ std::fflush(stdout); GENERATE_TRAP(); }, __VA_ARGS__)


#define CATCH_FATAL_EXCEPTIONS_PRINT_ERRORS_AND_ABORT(...) \
	CATCH_EXCEPTIONS_AND_PRINT_ERRORS_THEN({ std::fflush(stdout); std::abort(); }, __VA_ARGS__)


inline std::string get_fully_qualified_name(py::handle obj) {
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


template<typename Arg, typename... Args>
inline auto make_type_error(py::handle received_type, Arg expected_type, Args... expected_types) {
	auto get_name = []<typename T>(T value) -> std::string{
		if constexpr(std::is_convertible_v<T, std::string>) {
			return value;
		}
		else {
			return get_fully_qualified_name(value);
		}
	};

	return py::type_error(std::string("expected a ")
		+ (sizeof...(expected_types) > 0 ? "(" : "")
		+ (
			get_name(expected_type)
			+ ...
			+ (" | " + get_name(expected_types))
			)
		+ (sizeof...(expected_types) > 0 ? ")" : "")
		+ " object, but received an instance of '"
		+ get_fully_qualified_name(received_type)
		+ "' instead"
	);
}

} // namespace pygodot


