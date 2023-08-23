#include "variant/string_name.h"


namespace godot {


namespace py = pybind11;


StringName::StringName() : VariantTypeBase(uninitialized) {
	construct<0>();
}


StringName::StringName(StringName&& other) : VariantTypeBase(uninitialized) {
	std::swap(data, other.data); // XXX ?
}


StringName::StringName(const StringName& other) : VariantTypeBase(uninitialized) {
	construct<1>(other);
}


StringName::StringName(const String& other) : VariantTypeBase(uninitialized) {
	construct<2>(other);
}


StringName::StringName(const char* str) : StringName(String(str)) {
}


StringName::StringName(const std::string& str) : StringName(String(str)) {
}


StringName::StringName(const py::str& str) : StringName(std::string(str)) {
}


StringName::operator std::string() const {
	return String(*this);
}


StringName::operator py::str() const {
	return std::string(*this);
}


StringName& StringName::operator=(const StringName& other) {
	this->~StringName();
	construct<1>(other);
	return *this;
}


StringName& StringName::operator=(StringName&& other) {
	std::swap(data, other.data);
	return *this;
}


/*bool StringName::operator==(const StringName& other) const {
}


bool StringName::operator!=(const StringName& other) const {
}*/


namespace string_name {
	typedef py::class_<StringName> class_def_t;
	static std::unique_ptr<class_def_t> class_def;
}


void StringName::pre_def(py::module_& module_) {
	using namespace string_name;
	class_def = std::make_unique<class_def_t>(module_, "StringName");
}


void StringName::def(py::module_& module_) {
	using namespace string_name;
	def_init_uninitialized(*class_def)
		.def(py::init())
		.def(py::init<const StringName&>())
		.def(py::init<const String&>())
		.def(py::init<const py::str&>())
		.def("__str__", [](const StringName& self) -> py::str { return self; })
	;
	class_def.reset();
}


} // namespace godot


