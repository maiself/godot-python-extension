#!/usr/bin/env python3

import sys
import os
import textwrap


def main():
	print(textwrap.dedent(f'''
		{sys.platform = }
		{sys.version = }

		{os.getcwd() = }

		{sys.orig_argv = }
		{sys.argv = }

		{sys._base_executable = }
		{sys.executable = }

		{sys.base_prefix = }
		{sys.prefix = }

		{sys.base_exec_prefix = }
		{sys.exec_prefix = }

		{sys.platlibdir = }

		{sys.pycache_prefix = }

		sys.path = [
		  {""",
		  """.join(repr(x) for x in sys.path)}
		]

	''').strip())


if __name__ == '__main__':
	main()


