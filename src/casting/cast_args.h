#pragma once

#include <span>

#include "casting/cast.h"
#include "casting/cast_info.h"
#include "util/stable_vector.h"


namespace pygodot {


// intermediate cast_t from variant**
template<VariantPointerArgs T>
struct cast_t<T> {
	T args;
	size_t argument_count;

	cast_t(T args, size_t argument_count)
		: args(args)
		, argument_count(argument_count)
	{
	}

	cast_t() = delete;
	cast_t(const cast_t&) = delete;
	cast_t(cast_t&&) = delete;

	operator py::args() const {
		// NOTE: casting to python loses const as python has no concept

		py::args res(py::tuple{argument_count});

		for(size_t i = 0; i < argument_count; i++) {
			py::object arg = cast(args[i]);
			res[i] = arg;
		}

		return res;
	}
};


// intermediate cast_t from variant value**
template<VariantValuePointerArgs T>
struct cast_t<T> {
	T args;
	std::span<const cast_info_t> cast_types;

	cast_t(T args, std::span<const cast_info_t> cast_types)
		: args(args)
		, cast_types(cast_types)
	{
	}

	cast_t() = delete;
	cast_t(const cast_t&) = delete;
	cast_t(cast_t&&) = delete;

	operator py::args() const {
		// NOTE: casting to python loses const as python has no concept

		py::args res(py::tuple{cast_types.size()});

		for(size_t i = 0; i < cast_types.size(); i++) {
			//py::object arg = cast_t<std::remove_const_t<std::remove_pointer_t<T>>>(args[i], cast_types[i]);
			py::object arg = cast(args[i], cast_types[i]);
			res[i] = arg;
		}

		return res;
	}
};


// intermediate cast_t from py::args
template<PythonArgs T>
struct cast_t<T> {
	using arg_cast_t = decltype(cast(std::declval<py::handle>(), std::declval<GDExtensionVariantType>()));

	stable_vector<arg_cast_t> cast_args;
	stable_vector<GDExtensionConstTypePtr> value_pointers;

	cast_t(T& args, std::span<const cast_info_t> variant_types)
		: cast_args(variant_types.size()), value_pointers(variant_types.size())
	{
		if(args.size() != variant_types.size()) {
			throw std::runtime_error("args size mismatch");
		}

		const auto* variant_type = variant_types.data();

		for(auto& arg : args) {
			value_pointers.emplace_back() = cast_args.emplace_back(arg, (variant_type++)->variant_type);
		}
	}

	cast_t(T& args) // XXX
		: cast_args(args.size()), value_pointers(args.size())
	{
		for(auto& arg : args) {
			value_pointers.emplace_back() = cast_args.emplace_back(arg, variant_type_to_enum_value<Variant>);
		}
	}

	cast_t() = delete;
	cast_t(const cast_t&) = delete;
	cast_t(cast_t&&) = delete;

	GDExtensionConstTypePtr* data() const {
		return const_cast<GDExtensionConstTypePtr*>(value_pointers.data());
	}

	size_t size() const {
		return value_pointers.size();
	}

	operator GDExtensionTypePtr*() const {
		return const_cast<GDExtensionTypePtr*>(data());
	}

	operator GDExtensionConstVariantPtr*() const { // XXX
		return reinterpret_cast<GDExtensionConstVariantPtr*>(data());
	}

	/*operator GDExtensionConstTypePtr*() const {
		return data();
	}*/
};



// variant * args or const variant* args
template<VariantPointerArgs T, typename... Args>
py::args cast(T value, Args&&... args) {
	return cast_t<T>(value, std::forward<Args>(args)...);
}



// variant value* args or const variant value* args
template<VariantValuePointerArgs T, typename... Args>
py::args cast(T value, Args&&... args) {
	return cast_t<T>(value, std::forward<Args>(args)...);
}



//  py::args or const py::args
template<PythonArgs T, typename... Args>
auto cast(T& value, Args&&... args) {
	return cast_t<std::add_const_t<T>>(value, std::forward<Args>(args)...);
}



} // namespace pygodot


