#pragma once

#include <functional>

#include <pybind11/pybind11.h>

#include <gdextension_interface.h>
#include "gdextension_api_table.h"


namespace pygodot {


namespace py = pybind11;


struct extension_interface {
	static inline GDExtensionGodotVersion godot_version;
	static inline GDExtensionClassLibraryPtr library;
	static inline void* token;

#define GDEXTENSION_API(name, type) \
	static inline type name = nullptr;

	GDEXTENSION_APIS

#undef GDEXTENSION_API
};


inline std::optional<GDExtensionInitializationLevel> initialization_level;


void register_cleanup_func(std::function<void()> func);


} // namespace pygodot

