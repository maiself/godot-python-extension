#!/usr/bin/env python3

import pathlib
import re
import types
import itertools

tools_dir = pathlib.Path(__file__).parent.resolve()
project_dir = tools_dir.parent
lib_dir = project_dir / 'lib'


def get_all_defs():
	for path in sorted(lib_dir.glob('**/*.py')):
		module = str(path.relative_to(lib_dir)).removesuffix('.py').replace('/', '.')

		qualname_parts = []

		for line in path.read_text().splitlines():
			if match := re.match(r'^(?P<indent>\s*)(?P<type>def|class)\s+(?P<name>\w+)', line):
				def_ = types.SimpleNamespace(module=module, **match.groupdict())

				qualname_parts = [*qualname_parts[:len(def_.indent)], def_.name]
				def_.qualname = '.'.join(qualname_parts)

				del def_.indent

				def_.fullname = '.'.join((def_.module, def_.qualname))

				yield def_


def common_prefix(a, b):
	i = 0
	for i, (x, y) in enumerate(itertools.chain(zip(a, b), [(0, 1)] )):
		if x != y:
			break
	return a[:i]


def main():
	previous = []

	mod_level = 0
	type_ = 'mod'

	only_top_level_defs = False

	for def_ in get_all_defs():
		parts = def_.fullname.split('.')

		if only_top_level_defs and def_.type == 'def' and def_.name != def_.qualname:
			type_ = 'def'
			continue

		prefix = common_prefix(parts, previous)
		rest = parts[len(prefix):]

		if len(prefix) < mod_level:
			type_ = 'mod'
			mod_level = len(prefix)

		prefix = '.'.join(prefix)

		if prefix:
			prefix += '.'

		for i, part in enumerate(rest):

			if i == len(rest) - 1:
				type_ = 'def' if def_.type == 'def' else 'cls'

			elif type_ == 'mod':
				mod_level += 1

			match type_:
				case 'mod':
					sgr = (91, 1)
				case 'cls':
					sgr = (92, 1)
				case 'def':
					sgr = (95, 1)

			print(f'\033[2m{prefix}\033[0;{";".join(str(x) for x in sgr)}m{part}\033[0m')

			prefix += f'{part}.'

		previous = parts



if __name__ == '__main__':
	main()

