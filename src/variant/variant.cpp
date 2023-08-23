#include "variant/variant.h"
#include "variant/string.h"


namespace godot {


namespace py = pybind11;


namespace variant {
	typedef py::class_<Variant> class_def_t;
	static std::unique_ptr<class_def_t> class_def;
}


void Variant::pre_def(py::module_& module_) {
	using namespace variant;
	class_def = std::make_unique<class_def_t>(module_, "Variant");
}


void Variant::def(py::module_& module_) {
	using namespace variant;
	def_init_uninitialized(*class_def)
		.def(py::init())
		//.def(py::init<const Variant&>())
		//.def(py::init<const String&>())
		//.def(py::init<const py::str&>())
		.def("__str__", [](const Variant& self) -> py::str {
			String res;
			extension_interface::variant_stringify(self, res);
			return res;
		})
	;
	class_def.reset();
}


} // namespace godot


