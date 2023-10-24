#!/usr/bin/env python3

import sys
import pathlib
import importlib.resources
import types
import json
import re
import textwrap


# NOTE: This file intentionally avoids importing from any other local modules.
# This allows it to be ran as a tool from the development directory outside of Godot.


import _json # XXX: ensure fast decoding


# builtin_classes : variant types
# classes : object types


raise_not_found = {}


class ListWithNames(list):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		#self._cache = {}

	# XXX: unsure of the performance impact of this method, only used by _find_broken_properties below?
	if __name__ == '__main__':
		def __contains__(self, value):
			if isinstance(value, str):
				return self.get(value) is not None
				#return True

			if super().__contains__(value):
				return True

	def __getattr__(self, name):
		return self.get(name, default = raise_not_found)

	def get(self, name: str, *, key: str = 'name', default=None):
		# TODO: cache

		#if item := self._cache.get((name, key)):
		#	return item

		for item in self:
			if hasattr(item, key) and name == getattr(item, key):
				#self._cache[(name, key)] = item
				return item
			elif isinstance(item, dict) and key in item and name == item[key]:
				#self._cache[(name, key)] = item
				return item

		if default is raise_not_found:
			raise ValueError(f'{self.__class__.__name__!r} object has no item with key {key!r} matching {name!r}')

		#self._cache[(name, key)] = default # XXX
		return default


class Namespace(dict):
	def __setattr__(self, key, value):
		self[key] = value

	def __hasattr__(self, key):
		return key in self

	def __getattr__(self, key):
		if key not in self:
			raise AttributeError(f'{self.__class__.__name__!r} object has no attribute {key!r}')
		value = self[key]
		if isinstance(value, list):
			return ListWithNames(value)
		return value

	def get(self, name: str, default=None):
		res = super().get(name, default)

		if res is raise_not_found:
			raise ValueError(f'{self.__class__.__name__!r} object has no item matching {name!r}')

		if isinstance(res, list):
			return ListWithNames(res)
		return res


class ObjectPath(list):
	def __init__(self, path: str | list | None = None):
		if isinstance(path, str):
			self.extend(int(part) if part.isdecimal() else part for part in path.split('.'))

		elif isinstance(path, (list, types.GeneratorType)):
			self.extend(path)

		elif isinstance(path, types.NoneType):
			pass

		else:
			raise TypeError(f'unexpected type: {type(path)}')

	def __str__(self):
		return '.'.join(str(part) for part in self)

	def __hash__(self):
		return hash(tuple(self))

	def __add__(self, part: str | int):
		return type(self)([*self, part])

	def __getitem__(self, index):
		res = super().__getitem__(index)
		return type(self)(res) if isinstance(res, list) else res

	def without_indices(self):
		return type(self)(part for part in self if not isinstance(part, int))

	def split_name(self):
		if self:
			return (type(self)(self[:-1]), self[-1])
		raise ValueError('object path has no elements')


def get_via_path(root_obj, path):
	if not path:
		return root_obj

	obj = root_obj

	for part in ObjectPath(path):
		if obj is None:
			raise ValueError()

		if isinstance(part, int):
			if part < 0 or part >= len(obj):
				raise ValueError()

			obj = obj[part]

		else:
			if isinstance(obj, list):
				item = None
				found = False

				for x in obj:
					if getattr(x, 'name') == part:
						item = x
						found = True
						break

				if not found:
					raise ValueError()

				obj = item

			elif isinstance(obj, dict):
				if part not in obj:
					raise ValueError()

				obj = obj.get(part)

			else:
				if not hasattr(obj, part):
					raise ValueError()

				obj = getattr(obj, part)

	return obj


def visit_object(obj, func, types_ = ()):
	if not types_ or isinstance(obj, types_):
		func(obj)

	if isinstance(obj, (Namespace, dict)):
		for key, value in obj.items():
			visit_object(value, func, types_)
		
	elif isinstance(obj, list):
		for value in obj:
			visit_object(value, func, types_)


def visit_object_with_path(obj, func, types_ = (), *, path: ObjectPath = None, try_get_names = False):
	if path is None:
		path = ObjectPath()

	if not types_ or isinstance(obj, types_):
		func(obj, path)

	if isinstance(obj, (Namespace, dict)):
		for key, value in obj.items():
			visit_object_with_path(value, func, types_, path = path + key, try_get_names = try_get_names)
		
	elif isinstance(obj, list):
		for index, value in enumerate(obj):
			if try_get_names:
				if isinstance(value, types.SimpleNamespace) and hasattr(value, 'name'):
					index = value.name

				elif isinstance(value, dict) and 'name' in value:
					index = value['name']

			visit_object_with_path(value, func, types_, path = path + index, try_get_names = try_get_names)


def pretty_string(obj, *, max_depth: int | None = None):
	tab = '\t'

	if max_depth is not None:
		max_depth -= 1
	
	if isinstance(obj, (dict, Namespace)):
		res = ''

		last_was_list = False
		for i, (key, val) in enumerate(obj.items()):
			if i > 0:
				res += '\n'

			if last_was_list:
				res += '\n'

			res += f'{key}:'

			if isinstance(val, (dict, list)):
				if max_depth is not None and max_depth < 0:
					res += ' [...]' if isinstance(val, list) else ' {...}'
					last_was_list = False
				else:
					res += f'\n{textwrap.indent(pretty_string(val, max_depth=max_depth), tab)}'
					last_was_list = True

			else:
				res += f' {pretty_string(val, max_depth=max_depth)}'
				last_was_list = False

		return res

	elif isinstance(obj, (list)):
		if not obj:
			return ''
		if isinstance(obj[0], (list, dict)):
			return '\n\n'.join(pretty_string(val, max_depth=max_depth) for val in obj)
		else:
			return '\n'.join(pretty_string(val, max_depth=max_depth) for val in obj)

	else:
		return repr(obj)


def load_api_data(data: bytes | str | None = None) -> Namespace:
	global api

	if data is None:
		if __package__:
			package = importlib.resources.files(__package__)
		else:
			package = pathlib.Path(__file__).parent

		data = package.joinpath('extension_api.json').read_text()

	elif isinstance(data, bytes):
		data = data.decode()

	elif not isinstance(data, str):
		raise TypeError(
			f'expected `data` to be `bytes`, `str` or `None`, received {type(data)!r}')

	api = json.loads(data,
		object_hook = lambda obj: Namespace(**obj))

	return api


def __getattr__(name):
	if name == 'api':
		return load_api_data()

	raise AttributeError(
		f'module {__name__!r} has no attribute {name!r}')


def _get_api():
	'''Return the loaded api object. To be used by this module to trigger api load when accessing.'''
	return sys.modules[__name__].api


def get_api_entry_to_type_mapping():
	entry_types = Namespace()

	def visit(obj, path: ObjectPath):
		if not path or len(path) == 1 or isinstance(path[-1], int):
			return

		path, name = path.without_indices().split_name()

		entry = entry_types.setdefault(path, Namespace())

		entry[name] = dict if isinstance(obj, Namespace) else type(obj)

	visit_object_with_path(load_api_data(), visit, path=ObjectPath('api'))

	return entry_types


def display_api_layout():
	entry_type_mapping = get_api_entry_to_type_mapping() 

	for path, info in entry_type_mapping.items():
		if len(path) > 1:
			print(f'\033[92;2m{path[:-1]}.\033[0;92;1m{path[-1]}\033[0m')
		else:
			print(f'\033[92;1m{path}\033[0m')

		for key, type_ in info.items():
			if type_ in (list, dict):
				print(f'\t\033[96;1m{key}\033[0m: \033[95;1m{type_.__name__}\033[0m')
			else:
				print(f'\t\033[96;1m{key}\033[0m: \033[94m{type_.__name__}\033[0m')
		print()



def _find_broken_properties():
	had_missing = False

	for class_ in _get_api().classes:
		if had_missing:
			print()
			had_missing = False

		methods = class_.get('methods', [])

		for method in methods:
			if method.name.startswith('_') and not method.get('is_virtual'):
				print(f'missing \033[95mmethod\033[0m for {class_.name}.{method.name}')
				had_missing = True

		base = class_.name
		while base:
			base = _get_api().classes.get(base)

			methods.extend(base.get('methods', []))

			base = base.get('inherits')

		for method in methods:
			if method.get('is_hidden') and not method.name.endswith(' '):
				method.name += ' '

		for prop in class_.get('properties', []):
			missing_setter = bool(prop.get('setter') and prop.setter not in methods)
			missing_getter = bool(prop.get('getter') and prop.getter not in methods)

			if not missing_setter and not missing_getter:
				continue

			if missing_setter:
				print(f'missing \033[91msetter\033[0m for {class_.name}.{prop.name}: {prop.setter}')
			if missing_getter:
				print(f'missing \033[92mgetter\033[0m for {class_.name}.{prop.name}: {prop.getter}')

			print()

			had_missing = False


def main():
	match sys.argv[1:]:
		case ['--display-api-layout']:
			display_api_layout()

		case ['--max-depth', max_depth, obj_path] | [*max_depth, obj_path] if not obj_path.startswith('-'):
			if isinstance(max_depth, list):
				if len(max_depth) != 0:
					print(f'unexpected arguments')
					sys.exit(1)

				max_depth = None
			else:
				max_depth = int(max_depth)

				if max_depth <= 0:
					print(f'max depth must be greater than zero')
					sys.exit(1)

			try:
				obj = get_via_path(_get_api(), obj_path)

			except ValueError:
				print(f'could not find object at api path {obj_path!r}')
				sys.exit(1)

			print(pretty_string(obj, max_depth=max_depth))

		case ['--find-broken-properties']:
			_find_broken_properties()

		case ['--help'] | _:
			print(f'''usage: {pathlib.Path(sys.argv[0]).name} [--display-api-layout] [--max-depth MAX_DEPTH] [API_OBJECT_PATH]''')
			sys.exit(1)


if __name__ == '__main__':
	main()




