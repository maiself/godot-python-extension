#pragma once

#include <array>


namespace pygodot {


template<typename T, size_t N = 16>
class stable_vector {
	using element_storage_t = std::array<std::byte, sizeof(T)>;

	alignas(T) element_storage_t _storage[N];

	T* _data = nullptr;
	size_t _size = 0;
	size_t _capacity = 0;

	stable_vector() = delete;
	stable_vector(const stable_vector&) = delete;
	stable_vector(stable_vector&&) = delete;

public:
	stable_vector(size_t capacity) : _capacity(capacity) {
		_data = (_capacity > N)
			? reinterpret_cast<T*>(::new element_storage_t[_capacity])
			: reinterpret_cast<T*>(_storage)
		;
	}

	~stable_vector() {
		while(_size) {
			pop_back();
		}
		if(_data && _data != reinterpret_cast<T*>(_storage)) {
			::delete[] reinterpret_cast<element_storage_t*>(_data);
		}
	}

	template<typename... Args>
	T& emplace_back(Args&&... args) {
		if(_size >= _capacity) {
			throw std::length_error("cannot emplace element, size would exceed capacity");
		}
		::new(_data + _size) T(std::forward<Args>(args)...);
		return *(_data + (_size++));
	}

	void pop_back() {
		(_data + (--_size))->~T();
	}

	T* data() const {
		return _data;
	}

	size_t size() const {
		return _size;
	}

	size_t capacity() const {
		return _capacity;
	}
};


} // namespace pygodot

