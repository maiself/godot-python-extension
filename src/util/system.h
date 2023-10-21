#pragma once


namespace pygodot {


// XXX: may skip cleanup
void system_quick_exit(int status);


#ifdef UNIX_ENABLED
bool promote_lib_to_global(const char* path);
#endif


} // namespace pygodot

