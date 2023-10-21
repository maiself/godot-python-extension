#include <cstdlib>
#include <cstdio>
#include <cstring>

#ifdef UNIX_ENABLED
#include <dlfcn.h>
#endif

#ifdef WINDOWS_ENABLED
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


} // namespace pygodot

