#pragma once

#include <unordered_map>
#include <type_traits>
#include <typeindex>

#include <pybind11/pybind11.h>
#include <pybind11/pytypes.h>
#include <pybind11/stl.h>


namespace pygodot {

namespace py = pybind11;


namespace detail {

inline std::unordered_map<std::type_index, py::handle> bound_enum_type_handles;


template<typename EnumType, typename DerivedEnum>
class enum_base {
private:
	using UnderlyingType = typename std::underlying_type<EnumType>::type;

	const py::handle& scope;
	py::str name;
	py::list members;
	py::list docs;

	py::object enum_type;

	DerivedEnum& derived_ref() {
		return static_cast<DerivedEnum&>(*this);
	}

public:
	enum_base(const py::handle& scope, const char* name) : scope(scope), name(name) {
	}

	auto& value(const char* name, EnumType value, const char* doc = nullptr) {
		members.append(std::make_tuple(name, static_cast<UnderlyingType>(value)));
		if(doc) {
			docs.append(std::make_tuple(name, doc));
		}
		return derived_ref();
	}

	auto& finalize() {
		auto enum_module = py::module_::import("enum");
		auto enum_meta_type = enum_module.attr(DerivedEnum::base_type_name);

		enum_type = enum_meta_type(name, members);

		enum_type.attr("__module__") = scope.attr("__name__");

		for(auto doc : docs) {
			enum_type[doc[py::int_(0)]].attr("__doc__") = doc[py::int_(1)];
		}

		scope.attr(name) = enum_type;

		bound_enum_type_handles[std::type_index(typeid(EnumType))] = enum_type;

		return derived_ref();
	}

	auto& export_values() {
		finalize();

		for(auto member : members) {
			py::str member_name = member[py::int_(0)];
			scope.attr(member_name) = enum_type[member_name];
		}

		return derived_ref();
	}

	size_t size() const {
		return members.size();
	}
};


} // namespace detail


template<typename EnumType>
class int_enum : public detail::enum_base<EnumType, int_enum<EnumType>> {
	static constexpr char base_type_name[] = "IntEnum";
	friend detail::enum_base<EnumType, int_enum<EnumType>>;
public:
	using detail::enum_base<EnumType, int_enum<EnumType>>::enum_base;
};


template<typename EnumType>
class int_flag : public detail::enum_base<EnumType, int_flag<EnumType>> {
	static constexpr char base_type_name[] = "IntFlag";
	friend detail::enum_base<EnumType, int_flag<EnumType>>;
public:
	using detail::enum_base<EnumType, int_flag<EnumType>>::enum_base;
};


namespace detail {

template<typename EnumType>
class enum_type_caster_base {
private:
	using UnderlyingType = typename std::underlying_type<EnumType>::type;

public:
	static py::handle cast(EnumType src, py::return_value_policy policy, py::handle parent) {
		auto enum_type_handle = bound_enum_type_handles.at(std::type_index(typeid(EnumType)));

		return enum_type_handle(static_cast<UnderlyingType>(src)).release();
	}

	static std::optional<EnumType> load(py::handle src, bool convert) {
		auto enum_type_handle = bound_enum_type_handles.at(std::type_index(typeid(EnumType)));

		if(!py::isinstance(src, enum_type_handle)) {
			return std::nullopt;
		}

		pybind11::detail::type_caster<UnderlyingType> underlying_caster;

		if(!underlying_caster.load(src.attr("value"), convert)) {
			return std::nullopt;
		}

		return static_cast<EnumType>(static_cast<UnderlyingType>(underlying_caster));
	}
};


} // namespace detail

} // namespace pygodot


#define DECLARE_ENUM_TYPE_CASTER(EnumType, EnumTypeName) \
	namespace pybind11::detail { \
		template<> \
		class type_caster<EnumType> : pygodot::detail::enum_type_caster_base<EnumType> { \
		public: \
			PYBIND11_TYPE_CASTER(EnumType, const_name(EnumTypeName)); \
			\
			using pygodot::detail::enum_type_caster_base<EnumType>::cast; \
			\
			bool load(handle src, bool convert) { \
				if(auto res = pygodot::detail::enum_type_caster_base<EnumType>::load(src, convert)) { \
					value = *res; \
					return true; \
				} \
				return false; \
			} \
		}; \
	} // namespace pybind11::detail


