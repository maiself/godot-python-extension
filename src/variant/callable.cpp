#include "variant/callable.h"
#include "casting/cast_args.h"


namespace pygodot {


void func_to_callable(GDExtensionUninitializedTypePtr ptr, py::function func) {
	static GDExtensionObjectPtr object = nullptr; // XXX

	if(!object) {
		object = extension_interface::classdb_construct_object(StringName("Object")); // XXX: godot is currently requiring an object for callables

		register_cleanup_func([]() {
			extension_interface::object_destroy(object);
		});
	}

	GDExtensionCallableCustomInfo info = {
		.callable_userdata = func.ptr(),
		.object = object, // XXX

		.call_func = [](void* userdata, const GDExtensionConstVariantPtr* args,
			GDExtensionInt argument_count, GDExtensionVariantPtr res, GDExtensionCallError* error)
		{
			py::gil_scoped_acquire gil;

			auto func = py::reinterpret_borrow<py::function>(static_cast<PyObject*>(userdata));

			try {
				cast(res) = func(*cast(args, argument_count)); // XXX: cast info

				if(error) {
					error->error = GDEXTENSION_CALL_OK; // XXX
				}
				return;
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS(
				"While calling: " + get_fully_qualified_name(func))

			if(error) {
				error->error = GDEXTENSION_CALL_ERROR_INVALID_METHOD; // XXX
			}
		},

		.is_valid_func = [](void* userdata) -> GDExtensionBool {
			py::gil_scoped_acquire gil;

			try {
				auto func = py::reinterpret_borrow<py::function>(static_cast<PyObject*>(userdata));

				return py::bool_(func);
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()

			return false;
		},

		.free_func = [](void* userdata) {
			py::gil_scoped_acquire gil;

			py::handle(static_cast<PyObject*>(userdata)).dec_ref();
		},

		.hash_func = [](void* userdata) -> uint32_t {
			py::gil_scoped_acquire gil;

			try {
				auto func = py::reinterpret_borrow<py::function>(static_cast<PyObject*>(userdata));

				return py::hash(func);
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()

			return 0;
		},

		.equal_func = [](void* userdata_a, void* userdata_b) -> GDExtensionBool {
			py::gil_scoped_acquire gil;

			try {
				auto func_a = py::reinterpret_borrow<py::function>(static_cast<PyObject*>(userdata_a));
				auto func_b = py::reinterpret_borrow<py::function>(static_cast<PyObject*>(userdata_b));

				return func_a.equal(func_b);
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()

			return false;
		},

		/*.less_than_func = [](void* userdata_a, void* userdata_b) {
			py::gil_scoped_acquire gil;

			auto func_a = py::reinterpret_borrow<py::function>(static_cast<PyObject*>(userdata_a));
			auto func_b = py::reinterpret_borrow<py::function>(static_cast<PyObject*>(userdata_b));

			return 0;
		},*/

		.to_string_func = [](void *userdata, GDExtensionBool *is_valid, GDExtensionStringPtr out) {
			py::gil_scoped_acquire gil;

			auto func = py::reinterpret_borrow<py::function>(static_cast<PyObject*>(userdata));

			try {
				cast(out) = py::str(func); // XXX: cast info

				*is_valid = true;
				return;
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()

			*is_valid = false;
		}
	};

	func.inc_ref();

	extension_interface::callable_custom_create(ptr, &info);
}


} // namespace pygodot


