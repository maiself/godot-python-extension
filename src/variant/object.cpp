#include "variant/object.h"
#include "util/call_deferred.h"


/* TODO: add explanation to how this all works

  • python reference counting <-> godot reference counting
    ...

  • python object <-> godot object initialization process
    ...

*/


// TODO: some sort of debug / logging / tests


//#define REFCOUNT_DEBUG

#ifndef REFCOUNT_DEBUG
#define DEBUG_REFCOUNT_FUNC(obj, name, call_args, notes)
#else

#include <iostream>
#include <pybind11/stl.h>

#define DEBUG_REFCOUNT_FUNC(obj, name, call_args, notes) \
	pygodot::object::refcount_debug::scoped_refcount_debug _scoped_refcount_debug(obj, name, \
		std::make_tuple call_args, std::make_tuple notes);

namespace pygodot::object::refcount_debug {
	class scoped_refcount_debug {
		static inline int call_level = 0;

		template<typename Sep>
		static void write_list(Sep&& sep) {
		}

		template<typename Sep, typename Arg, typename... Args>
		static void write_list(Sep&& sep, Arg&& arg, Args&&... args) {
			std::cout << std::forward<Arg>(arg);
			((std::cout << std::forward<Sep>(sep) << std::forward<Args>(args)), ...);
		}
	public:
		template<typename... CallArgs, typename... Notes>
		scoped_refcount_debug(godot::Object* obj, const std::string& name,
			std::tuple<CallArgs...> call_args, std::tuple<Notes...> notes)
		{
			for(int i = 0; i < call_level; i++) {
				std::cout << "  ";
			}
			call_level++;

			std::cout << name << "(";
			std::apply(write_list<const char*, CallArgs...>, std::tuple_cat(std::make_tuple(", "), call_args));
			std::cout << ")";

			if(obj) {
				std::cout << " ; obj = " << obj;
			}

			if(sizeof...(Notes)) {
				std::cout << " ; ";
			}
			std::apply(write_list<const char*, Notes...>, std::tuple_cat(std::make_tuple(" ; "), notes));

			if(obj && obj->is_reference_counted()) {
				std::cout << " ; refcount = " << obj->get_reference_count();
			}

			std::cout << "\n";
		}

		~scoped_refcount_debug() {
			call_level--;
		}
	};
} // namespace pygodot::object::refcount_debug

#endif


namespace godot {


namespace py = pybind11;


class _ObjectAccessor {
	Object& obj;

public:
	static Object* create(GDExtensionObjectPtr ptr) {
		return new Object(ptr);
	}

	_ObjectAccessor(Object& obj) : obj(obj) {}

	void free() {
		obj._free();
	}

	bool reference(bool reference) {
		return obj._reference(reference);
	}

	int traverse(PyObject* self_base, visitproc visit, void* arg) {
		return obj._traverse(self_base, visit, arg);
	}

	void clear(PyObject* self_base) {
		obj._clear(self_base);
	}

	py::handle handle() {
		return obj._handle;
	}
};


/*Object::Object() : VariantTypeBase(uninitialized) {
	construct<0>();
}*/


static Object* _object_currently_binding = nullptr;


void Object::_free() {
	DEBUG_REFCOUNT_FUNC(this, "Object::_free", (), ())

	if(!Py_IsInitialized()) {
		// XXX: singletons may still have bindings associated even after shutdown
		return;
	}

	if(!_ptr) {
		return;
	}
	_ptr = nullptr;

	py::gil_scoped_acquire gil;

	if(!is_reference_counted()) {
		_handle.dec_ref();
	}
}


bool Object::_reference(bool reference) {
	DEBUG_REFCOUNT_FUNC(this, "Object::_reference", (reference), ())

	if(!_ptr) {
		return true;
	}

	if(!Py_IsInitialized()) {
		// XXX: singletons may still have bindings associated even after shutdown
		return true;
	}

	py::gil_scoped_acquire gil;

	if(reference) {
		_handle.inc_ref();
	}
	else {
		// fast release for special case
		if(Py_REFCNT(_handle.ptr()) == 2 && get_reference_count() == 1) {
			DEBUG_REFCOUNT_FUNC(this, "call_deferred", ("..."), ("scheduled"))

			call_deferred([this, obj = py::reinterpret_borrow<py::object>(_handle)]() mutable {
				DEBUG_REFCOUNT_FUNC(this, "call_deferred", ("..."), ("called"))

				py::gil_scoped_acquire gil;

				if(_ptr && Py_REFCNT(_handle.ptr()) == 2 && get_reference_count() == 1) {
					if(unreference()) {
						_destroy();
					}
				}

				obj = py::object();
			});
		}

		_handle.dec_ref();
	}

	return true;
}


int Object::_traverse(PyObject* self_base, visitproc visit, void* arg) {
	DEBUG_REFCOUNT_FUNC(this, "Object::_traverse", (self_base, visit, arg), ())

	if(!is_reference_counted()) {
		return 0;
	}

	if(!_ptr) {
		return 0;
	}

	if(get_reference_count() == 1) {
		Py_VISIT(self_base);
	}

	return 0;
}


void Object::_clear(PyObject* self_base) {
	DEBUG_REFCOUNT_FUNC(this, "Object::_clear", (self_base), ())

	if(is_reference_counted()) {
		if(!_ptr) {
			return;
		}

		if(unreference()) {
			_destroy();
		}
	}
}


void Object::_destroy() {
	DEBUG_REFCOUNT_FUNC(this, "Object::_destroy", (), ())

	if(!_ptr) {
		return;
	}

	auto* ptr = _ptr;
	_ptr = nullptr;

	extension_interface::object_destroy(ptr);
}


static GDExtensionInstanceBindingCallbacks _binding_callbacks = {
	.create_callback = [](void* token, void* object) -> void* {
		DEBUG_REFCOUNT_FUNC(nullptr, "create_callback", (token, object), ())

		// only called for builtin classes
		// called via object_get_instance_binding
		return _ObjectAccessor::create(reinterpret_cast<GDExtensionObjectPtr>(object));
	},

	.free_callback = [](void* token, void* object, void* binding) -> void {
		DEBUG_REFCOUNT_FUNC(nullptr, "free_callback", (token, object, binding), ())

		if(!binding) {
			return;
		}

		_ObjectAccessor(*reinterpret_cast<Object*>(binding)).free();
	},

	.reference_callback = [](void* token, void* binding, GDExtensionBool reference) -> GDExtensionBool {
		DEBUG_REFCOUNT_FUNC(nullptr, "reference_callback", (token, binding, (bool)reference), ())

		if(!binding) {
			return true;
		}

		return _ObjectAccessor(*reinterpret_cast<Object*>(binding)).reference(reference);
	}
};


Object::Object(GDExtensionObjectPtr ptr) : _ptr(ptr) {
	DEBUG_REFCOUNT_FUNC(this, "Object::Object", (ptr), ())
}


Object::Object(const py::str& class_name, const py::str& base_class_name) {
	DEBUG_REFCOUNT_FUNC(this, "Object::Object", (class_name, base_class_name), ())

	_ptr = extension_interface::classdb_construct_object(StringName(base_class_name));
	if(!_ptr) {
		throw std::runtime_error("unable to construct godot object of type " + std::string(base_class_name));
	}

	if(!class_name.equal(base_class_name)) {
		extension_interface::object_set_instance(_ptr, StringName(class_name),
			reinterpret_cast<GDExtensionClassInstancePtr>(this));
	}

	extension_interface::object_set_instance_binding(_ptr, extension_interface::token,
		this, &_binding_callbacks);
}


Object::~Object() {
	DEBUG_REFCOUNT_FUNC(this, "Object::~Object", (), ())

	if(!Py_IsInitialized()) {
		return;
	}

	if(is_reference_counted()) {
		_ptr = nullptr;
	}
	else {
		_destroy();
	}
}


StringName Object::get_class_name() const {
	return py::type::handle_of(_handle).attr("__name__").cast<py::str>();
}


bool Object::is_reference_counted() const {
	return _is_reference_counted;
}

size_t Object::get_reference_count() const {
	if(!_ptr) {
		return 0;
	}

	//static py::handle _get_reference_count = resolve_name("godot.RefCounted.get_reference_count"); // XXX
	//return _get_reference_count(_handle).cast<size_t>();

	static auto* method_ptr = extension_interface::classdb_get_method_bind(
		StringName("RefCounted"), StringName("get_reference_count"), 3905245786);

	GDExtensionInt res;

	extension_interface::object_method_bind_ptrcall(method_ptr, _ptr, nullptr, (GDExtensionTypePtr)&res);

	return res;
}


bool Object::init_ref() {
	DEBUG_REFCOUNT_FUNC(this, "Object::init_ref", (), ())

	//static py::handle _init_ref = resolve_name("godot.RefCounted.init_ref"); // XXX
	//return _init_ref(_handle).cast<bool>();

	static auto* method_ptr = extension_interface::classdb_get_method_bind(
		StringName("RefCounted"), StringName("init_ref"), 2240911060);

	GDExtensionBool res;

	extension_interface::object_method_bind_ptrcall(method_ptr, _ptr, nullptr, (GDExtensionTypePtr)&res);

	return res;
}

bool Object::reference() {
	DEBUG_REFCOUNT_FUNC(this, "Object::reference", (), ())

	//static py::handle _reference = resolve_name("godot.RefCounted.reference"); // XXX
	//return _reference(_handle).cast<bool>();

	static auto* method_ptr = extension_interface::classdb_get_method_bind(
		StringName("RefCounted"), StringName("reference"), 2240911060);

	GDExtensionBool res;

	extension_interface::object_method_bind_ptrcall(method_ptr, _ptr, nullptr, (GDExtensionTypePtr)&res);

	return res;
}

bool Object::unreference() {
	DEBUG_REFCOUNT_FUNC(this, "Object::unreference", (), ())

	//static py::handle _unreference = resolve_name("godot.RefCounted.unreference"); // XXX
	//return _unreference(_handle).cast<bool>();

	static auto* method_ptr = extension_interface::classdb_get_method_bind(
		StringName("RefCounted"), StringName("unreference"), 2240911060);

	GDExtensionBool res;

	extension_interface::object_method_bind_ptrcall(method_ptr, _ptr, nullptr, (GDExtensionTypePtr)&res);

	return res;
}


py::object Object::get_bound_instance(GDExtensionObjectPtr obj) {
	DEBUG_REFCOUNT_FUNC(nullptr, "Object::get_bound_instance", (obj), ())

	if(!obj) {
		return py::none();
	}

	if(!Py_IsInitialized()) {
		throw std::runtime_error("cannot bind instance after interpreter finalization");
	}

	auto try_get_binding = [obj](GDExtensionInstanceBindingCallbacks* binding_callbacks = nullptr) {
			return reinterpret_cast<Object*>(
				extension_interface::object_get_instance_binding(
					obj, extension_interface::token, binding_callbacks));
		};

	// try to get exsisting binding
	if(Object* res = try_get_binding()) {
		return py::reinterpret_borrow<py::object>(res->_handle);
	}

	// get python class type matching godot class
	StringName class_name{uninitialized};
	extension_interface::object_get_class_name(obj, extension_interface::library, uninitialized(class_name));

	py::gil_scoped_acquire gil;

	py::object cls = py::module_::import("godot").attr(class_name);

	// godot.__getattr__ may have caused new bindings, for example singletons, so try again
	if(Object* res = try_get_binding()) {
		return py::reinterpret_borrow<py::object>(res->_handle);
	}

	// create binding
	Object* res = try_get_binding(&_binding_callbacks);

	try {
		_object_currently_binding = res;

		py::object self = cls(); // XXX: check reentrance, especially wrt _object_currently_binding

		_object_currently_binding = nullptr;

		return self;
	}
	catch(...) {
		_object_currently_binding = nullptr;
		throw;
	}
}


namespace object {
	typedef py::class_<Object> class_def_t;
	static std::unique_ptr<class_def_t> class_def;
}


static void setup_godot_python_type(PyHeapTypeObject* heap_type) {
	auto* type = &heap_type->ht_type;

	type->tp_flags |= Py_TPFLAGS_HAVE_GC;

	type->tp_traverse = [](PyObject* self_base, visitproc visit, void* arg) -> int {
		auto& self = py::cast<Object&>(py::handle(self_base));

		auto res = _ObjectAccessor(self).traverse(self_base, visit, arg);
		if(res != 0) {
			return res;
		}

		return py::detail::pybind11_traverse(self_base, visit, arg);
	};

	type->tp_clear = [](PyObject* self_base) {
		auto& self = py::cast<Object&>(py::handle(self_base));

		_ObjectAccessor(self).clear(self_base);

		return py::detail::pybind11_clear(self_base);
	};
}


void Object::pre_def(py::module_& module_) {
	using namespace object;
	class_def = std::make_unique<class_def_t>(module_, "Object",
		py::dynamic_attr(),
		py::custom_type_setup(setup_godot_python_type)
	);
}


void Object::def(py::module_& module_) {
	using namespace object;
	(*class_def)
		.def(py::init([]() { return _object_currently_binding; }))
		.def(py::init([](const py::str& class_name, const py::str& base_class_name) {
			return new Object(class_name, base_class_name);
		}))
	;

	auto& cls = *class_def;

	py::function __init__ = cls.attr("__init__");
	py::delattr(cls, "__init__");

	cls.attr("__init__") = py::cpp_function(
		[__init__](py::object& self) {
			DEBUG_REFCOUNT_FUNC(nullptr, "__init__", (self.ptr()), ())

			if(self.is_none()) {
				throw py::type_error("cannot init object None");
			}

			if(_object_currently_binding) {
				__init__(self);
				_object_currently_binding = nullptr;
			}
			else {
				py::type cls = py::type::of(self);
				py::list mro = cls.attr("mro")();

				py::object most_derived_non_extension_class = py::type::of<Object>();
				py::object most_derived_extension_class = py::none();

				for(py::handle type : mro) {
					if(py::getattr(type, "_godot_class", py::none()).equal(type)) { // XXX
						if(PyType_IsSubtype(reinterpret_cast<PyTypeObject*>(type.ptr()),
							reinterpret_cast<PyTypeObject*>(most_derived_non_extension_class.ptr()))
						)
						{
							most_derived_non_extension_class = type.cast<py::type>();
						}
					}

					if(py::getattr(type, "_extension_class", py::none()).equal(type)) { // XXX
						if(most_derived_extension_class.is_none()
								|| PyType_IsSubtype(reinterpret_cast<PyTypeObject*>(type.ptr()),
									reinterpret_cast<PyTypeObject*>(most_derived_extension_class.ptr())
							)
						)
						{
							most_derived_extension_class = type.cast<py::type>();
						}
					}
				}

				py::str base_class_name = most_derived_non_extension_class.attr("__name__");
				py::str class_name = (most_derived_extension_class.is_none()
					? base_class_name
					: most_derived_extension_class.attr("__name__")
				);

				__init__(self, class_name, base_class_name);
			}

			auto& self_object = py::cast<Object&>(self);

			self_object._handle = self;

			static py::handle RefCounted = resolve_name("godot.RefCounted");
			self_object._is_reference_counted = py::isinstance(self, RefCounted); // XXX

			if(self_object.is_reference_counted()) {
				Py_SET_REFCNT(self.ptr(),
					Py_REFCNT(self.ptr())
					+ std::min<size_t>(self_object.get_reference_count(), 2) // XXX: godot implementation detail?
				);

				self_object.init_ref(); // XXX
			}
			else {
				DEBUG_REFCOUNT_FUNC(&self_object, "__init__", (self.ptr()), ("not ref counted"))

				self.inc_ref(); // XXX: godot needs ref
			}
		},
		py::is_method(cls),
		py::name("Object.__init__")
	);

	class_def.reset();
}


} // namespace godot


