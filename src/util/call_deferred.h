#pragma once

#include <functional>

#include "extension/extension.h"


namespace pygodot {


template<typename Func>
static void call_deferred(Func&& func) {
	auto* ptr = new std::function<void()>(std::forward<Func>(func));

	GDExtensionCallableCustomInfo info = {
		.callable_userdata = ptr,

		.call_func = [](void* userdata, const GDExtensionConstVariantPtr* args,
			GDExtensionInt argument_count, GDExtensionVariantPtr res, GDExtensionCallError* error)
		{
			auto* ptr = static_cast<std::function<void()>*>(userdata);
			auto& func = *ptr;

			try {
				func();
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
		},

		.free_func = [](void* userdata) {
			auto* ptr = static_cast<std::function<void()>*>(userdata);

			try {
				delete ptr;
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
		},
	};

	Callable callable{uninitialized};
	extension_interface::callable_custom_create(uninitialized(callable), &info);

	resolve_name("godot.Callable.call_deferred")(&callable);
}


} // namespace pygodot

