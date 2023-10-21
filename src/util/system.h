#pragma once

#include <vector>
#include <string>
#include <filesystem>
#include <codecvt>
#include <locale>


namespace pygodot {


// XXX: may skip cleanup
void system_quick_exit(int status);


#ifdef UNIX_ENABLED
bool promote_lib_to_global(const char* path);
#endif


// get the path to the main process binary (not the extension)
std::filesystem::path get_executable_path();

// get the full argv passed to the main process
std::vector<std::string> get_argv();


} // namespace pygodot

