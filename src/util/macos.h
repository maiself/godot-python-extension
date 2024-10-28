#ifndef MACOS_H
#define MACOS_H

#include <vector>
#include <string>
#include <filesystem>

namespace macos {

// get the full argv passed to the main process
std::vector<std::string> get_argv();

}

#endif //MACOS_H
