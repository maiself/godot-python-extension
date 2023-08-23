#!/usr/bin/env python3

import sys
import os
import pathlib


tools_dir = pathlib.Path(__file__).parent.resolve()
project_dir = tools_dir.parent
api_info_path = project_dir / 'lib' / 'godot' / '_internal' / 'api_info.py'


if __name__ == '__main__':
	os.execl(api_info_path, *sys.argv)

