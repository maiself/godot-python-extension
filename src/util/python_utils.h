#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/pytypes.h>
#include <pybind11/stl.h>


namespace pygodot {


namespace py = pybind11;


typedef std::optional<py::function> nullable_py_function;


py::object resolve_name(py::str name);


class resolved_name : public py::object {
public:
	resolved_name(py::str name);
	~resolved_name();

	void reset();
};


bool issubclass(py::handle cls, py::handle class_or_tuple);


template<typename Func, typename... Args>
decltype(auto) call_without_gil(Func&& func, Args&&... args) {
	//py::gil_scoped_release released_gil; // XXX: slows things down a bit
	return std::forward<Func>(func)(std::forward<Args>(args)...);
}


} // namespace pygodot

