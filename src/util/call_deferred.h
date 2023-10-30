#pragma once

#include <functional>

#include "extension/extension.h"


namespace pygodot {


class deferred_call_t {
	std::function<void()> func;

	template<typename Func>
	deferred_call_t(Func&& func) : func(std::forward<Func>(func)) {
	}

	void operator()() {
		if(func) {
			func();
		}
	}

	template<typename Func>
	friend deferred_call_t& call_deferred(Func&& func);

public:
	void cancel() {
		func = decltype(func)();
	}
};


template<typename Func>
static deferred_call_t& call_deferred(Func&& func) {
	auto* ptr = new deferred_call_t(std::forward<Func>(func));

	GDExtensionCallableCustomInfo info = {
		.callable_userdata = ptr,

		.call_func = [](void* userdata, const GDExtensionConstVariantPtr* args,
			GDExtensionInt argument_count, GDExtensionVariantPtr res, GDExtensionCallError* error)
		{
			auto* ptr = static_cast<deferred_call_t*>(userdata);
			auto& func = *ptr;

			try {
				func();
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
		},

		.free_func = [](void* userdata) {
			auto* ptr = static_cast<deferred_call_t*>(userdata);

			try {
				delete ptr;
			}
			CATCH_EXCEPTIONS_AND_PRINT_ERRORS()
		},
	};

	Callable callable{uninitialized};
	extension_interface::callable_custom_create(uninitialized(callable), &info);

	resolve_name("godot.Callable.call_deferred")(&callable);

	return *ptr;
}


} // namespace pygodot

