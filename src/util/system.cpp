#include <vector>
#include <string>
#include <filesystem>
#include <codecvt>
#include <locale>
#include <cstdlib>
#include <cstdio>
#include <cstring>

#ifdef UNIX_ENABLED
#include <dlfcn.h>
#include <unistd.h>
#endif

#ifdef WINDOWS_ENABLED
#include <windows.h>
#include <psapi.h>
#include <shellapi.h>
#include <processthreadsapi.h>
#endif

#include "util/system.h"


namespace pygodot {


// XXX: may skip cleanup
void system_quick_exit(int status) {
#ifdef WINDOWS_ENABLED
	TerminateProcess(GetCurrentProcess(), status);
#else
	std::quick_exit(status);
#endif
}


#ifdef UNIX_ENABLED
bool promote_lib_to_global(const char* path) {
	if(!path || strlen(path) == 0) {
		return true;
	}
	if(void* lib = dlopen(path, RTLD_GLOBAL | RTLD_NOW | RTLD_NOLOAD)) {
		dlclose(lib);
		return true;
	}
	else if(const char* err = dlerror()) {
		printf("error promoting %s to RTLD_GLOBAL via dlopen: %s\n", path, err);
	}
	return false;
}
#endif


std::filesystem::path get_executable_path() {
#ifdef LINUX_ENABLED
	char buffer[1024];
	memset(buffer, 0, sizeof(buffer));
	ssize_t len = readlink("/proc/self/exe", buffer, sizeof(buffer));
	return std::filesystem::path(buffer);
#endif
#ifdef WINDOWS_ENABLED
	WCHAR buffer[4096];
	GetModuleFileNameW(nullptr, buffer, 4096);
	return std::filesystem::path(buffer);
#endif
}

std::vector<std::string> get_argv() {
	std::vector<std::string> args;

#ifdef LINUX_ENABLED
	auto cmdline_file = fopen("/proc/self/cmdline", "r");

	while(true) {
		char* line = nullptr;
		size_t len;
		auto res = getdelim(&line, &len, 0, cmdline_file);

		if(res < 0) {
			free(line);
			break;
		}

		args.emplace_back(line, len);
		free(line);
	}

	fclose(cmdline_file);
#endif

#ifdef WINDOWS_ENABLED
	int num_args;
	LPWSTR* arg_list = CommandLineToArgvW(GetCommandLineW(), &num_args);

	if(arg_list) {
		for(int index = 0; index < num_args; index++) {
			auto* warg = arg_list[index];
			int wlen = wcslen(warg);

			int len = WideCharToMultiByte(CP_UTF8, 0, warg, wlen, nullptr, 0, nullptr, nullptr);
			std::string arg(len, 0);
			WideCharToMultiByte(CP_UTF8, 0, warg, wlen, &arg[0], len, nullptr, nullptr);

			args.emplace_back(arg);
		}
	}
#endif

	return args;
}


} // namespace pygodot

