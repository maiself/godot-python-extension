#pragma once

#include <pybind11/pybind11.h>

#include "extension/extension.h"


namespace pygodot {


namespace py = pybind11;


void func_to_callable(GDExtensionUninitializedTypePtr ptr, py::function func);


} // namespace pygodot


