#include <string>

#include <pybind11/pytypes.h>


#include "variant/string.h"
#include "variant/string_name.h"


namespace godot {


namespace py = pybind11;


String::String() : VariantTypeBase(uninitialized) {
	construct<0>();
}


String::String(String&& other) : VariantTypeBase(uninitialized) {
	std::swap(data, other.data); // XXX ?
}


String::String(const String& other) : VariantTypeBase(uninitialized) {
	construct<1>(other);
}


String::String(const StringName& other) : VariantTypeBase(uninitialized) {
	construct<2>(other);
}


String::String(const char* str) : VariantTypeBase(uninitialized) {
	extension_interface::string_new_with_utf8_chars(uninitialized(this), str);
}


String::String(const std::string& str) : VariantTypeBase(uninitialized) {
	extension_interface::string_new_with_utf8_chars_and_len(uninitialized(this), str.data(), str.size());
}


String::String(const py::str& str) : String(std::string(str)) {
}


String& String::operator=(const String& other) {
	this->~String();
	construct<1>(other);
	return *this;
}


String& String::operator=(String&& other) {
	std::swap(data, other.data);
	return *this;
}


String::operator std::string() const {
	size_t length = extension_interface::string_to_utf8_chars(*this, nullptr, 0);
	auto buffer = std::make_unique<char[]>(length+1);
	extension_interface::string_to_utf8_chars(*this, buffer.get(), length);
	buffer[length] = '\0';
	return buffer.get();
}


String::operator py::str() const {
	std::string str = *this;
	return str;
}


namespace string {
	typedef py::class_<String> class_def_t;
	std::unique_ptr<class_def_t> class_def;
}


void String::pre_def(py::module_& module_) {
	using namespace string;
	class_def = std::make_unique<class_def_t>(module_, "String");
}


static PyObject *dispatcher(PyObject *self, PyObject *args_in, PyObject *kwargs_in) {
	return py::none().release().ptr();
}

void String::def(py::module_& module_) {
	using namespace string;
	def_init_uninitialized(*class_def)
		.def(py::init())
		.def(py::init<const String&>())
		.def(py::init<const StringName&>())
		.def(py::init<const py::str&>())
		.def("__str__", [](const String& self) -> py::str { return self; })
	;
	class_def.reset();
}


} // namespace godot


