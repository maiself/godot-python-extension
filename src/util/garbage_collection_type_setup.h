#pragma once

#include <vector>
#include <functional>

#include <pybind11/pybind11.h>


namespace pygodot {


namespace py = pybind11;


template<typename type_>
class garbage_collection_type_setup {
	using type = type_;

	static inline std::vector<std::function<PyObject*&(type&)>> pointer_getters;
	static inline std::vector<std::function<void(type&)>> member_clearers;

public:
	template<typename C, typename D>
	garbage_collection_type_setup& collect(D C::*pm) {
        static_assert(std::is_same_v<C, type> || std::is_base_of_v<C, type>);

		pointer_getters.push_back([pm](type& self) -> PyObject*& {
			return (self.*pm).ptr();
		});

		member_clearers.push_back([pm](type& self) {
			self.*pm = py::none();
		});

		return *this;
	}

	operator py::custom_type_setup::callback() {
		return [](PyHeapTypeObject* heap_type) {
			auto* ht_type = &heap_type->ht_type;

			ht_type->tp_flags |= Py_TPFLAGS_HAVE_GC;

			ht_type->tp_traverse = [](PyObject* self_base, visitproc visit, void* arg) {
				type& self = py::cast<type&>(py::handle(self_base));

				for(auto& getter : pointer_getters) {
					Py_VISIT(getter(self));
				}

				return 0;
			};

			ht_type->tp_clear = [](PyObject* self_base) {
				type& self = py::cast<type&>(py::handle(self_base));

				for(auto& clearer : member_clearers) {
					clearer(self);
				}

				return 0;
			};
		};
	}
};


} // namespace pygodot


