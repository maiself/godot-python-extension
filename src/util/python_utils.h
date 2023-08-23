#pragma once

#include <pybind11/pybind11.h>


namespace pygodot {


namespace py = pybind11;


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

