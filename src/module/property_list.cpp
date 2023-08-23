#include "extension/extension.h"
#include "module/property_list.h"


namespace pygodot {


PropertyList::PropertyList(py::object prop_sequence) : _original_prop_sequence(prop_sequence) {
	static py::handle Mapping = resolve_name("collections.abc.Mapping");

	auto get_item_or_default = []<typename T>(py::handle obj, py::str key, T&& default_) -> T {
		try {
			return py::cast<T>(obj[key]);
		}
		catch(const py::error_already_set&) {
			return std::forward<T>(default_);
		}
	};

	for(py::handle prop : _original_prop_sequence) {
		if(py::isinstance(prop, py::type::of<PyGDExtensionPropertyInfo>())) {
			_prop_info_list.append(prop);
		}
		else if(py::isinstance(prop, Mapping)) {
			PyGDExtensionPropertyInfo info = {
				.type = get_item_or_default.template operator()<GDExtensionVariantType>(
					prop, "type", GDEXTENSION_VARIANT_TYPE_NIL),
				.name = get_item_or_default.template operator()<py::str>(
					prop, "name", ""),
				.class_name = get_item_or_default.template operator()<py::str>(
					prop, "class_name", ""),
				.hint = get_item_or_default.template operator()<uint32_t>(
					prop, "hint", 0),
				.hint_string = get_item_or_default.template operator()<py::str>(
					prop, "hint_string", ""),
				.usage = get_item_or_default.template operator()<uint32_t>(
					prop, "usage", 0),
			};

			_prop_info_list.append(info);
		}
		else {
			throw py::type_error("property must be a PropertyInfo or mapping instance");
		}
	}

	_list_ptr = std::make_unique<GDExtensionPropertyInfo[]>(std::max<size_t>(py::len(_prop_info_list) + 1, 2));

	size_t i = 1;
	for(py::handle prop : _prop_info_list) {
		_list_ptr[i++] = py::cast<PyGDExtensionPropertyInfo&>(prop);
	}

	*reinterpret_cast<PropertyList**>(&_list_ptr[0]) = this;
}


PropertyList* PropertyList::get_from_pointer(const GDExtensionPropertyInfo* list_ptr) {
	if(!list_ptr) {
		return nullptr;
	}

	return const_cast<PropertyList*>(reinterpret_cast<const PropertyList*>(list_ptr - 1));
}


PropertyList::operator const GDExtensionPropertyInfo*() const {
	return &_list_ptr[1];
}


size_t PropertyList::size() const {
	return py::len(_prop_info_list);
}


PropertyList::operator py::object() const {
	return _original_prop_sequence;
}


} // namespace pygodot


