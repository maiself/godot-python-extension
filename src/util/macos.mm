#include "util/macos.h"

#import <Foundation/Foundation.h>


std::vector<std::string> macos::get_argv() {
	std::vector<std::string> argv;
	NSArray *argv_objc = [[NSProcessInfo processInfo] arguments];
	for (NSString *arg in argv_objc) {
		argv.push_back([arg UTF8String]);
	}
	return argv;
}
