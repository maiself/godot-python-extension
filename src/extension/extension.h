#pragma once

#include <functional>

#include <pybind11/pybind11.h>

#include <gdextension_interface.h>
#include "gdextension_api_table.h"

#include "util/enum_types.h"


DECLARE_ENUM_TYPE_CASTER(GDExtensionVariantType, "GDExtensionVariantType")
DECLARE_ENUM_TYPE_CASTER(GDExtensionVariantOperator, "GDExtensionVariantOperator")
DECLARE_ENUM_TYPE_CASTER(GDExtensionCallErrorType, "GDExtensionCallErrorType")
DECLARE_ENUM_TYPE_CASTER(GDExtensionClassMethodFlags, "GDExtensionClassMethodFlags")
DECLARE_ENUM_TYPE_CASTER(GDExtensionClassMethodArgumentMetadata, "GDExtensionClassMethodArgumentMetadata")
DECLARE_ENUM_TYPE_CASTER(GDExtensionInitializationLevel, "GDExtensionInitializationLevel")


namespace pygodot {


namespace py = pybind11;


struct extension_interface {
	static inline GDExtensionGodotVersion godot_version;
	static inline GDExtensionClassLibraryPtr library;
	static inline void* token;

	// Runtime value of `GDEXTENSION_VARIANT_TYPE_VARIANT_MAX` from the currently loaded Godot version
	static inline GDExtensionVariantType variant_type_variant_max = {};

#define GDEXTENSION_API(name, type) \
	static inline type name = nullptr;

	GDEXTENSION_APIS

#undef GDEXTENSION_API
};


inline std::optional<GDExtensionInitializationLevel> initialization_level;


inline uint32_t version_to_uint(const GDExtensionGodotVersion& version) {
	return (version.major << 16) + (version.minor << 8) + version.patch;
}

inline bool godot_version_is_at_least(const GDExtensionGodotVersion& version) {
	return (version_to_uint(extension_interface::godot_version) >= version_to_uint(version));
}

inline bool godot_version_is_at_least(uint32_t major, uint32_t minor, uint32_t patch = 0) {
	return godot_version_is_at_least({.major = major, .minor = minor, .patch = patch, .string = nullptr});
}


void register_cleanup_func(std::function<void()> func);


} // namespace pygodot

