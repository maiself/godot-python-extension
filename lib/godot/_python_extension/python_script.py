from __future__ import annotations

import pathlib
import weakref

import godot

from godot._internal.extension_classes import *
import _gdextension as gde

from . import python_language
from . import python_script_instance

from . import godot_fs_importer

from . import utils

from . import script_class_type


import sys
import importlib.abc
import re











import inspect

def get_args_dict(level: int = 0) -> dict:
	frame = inspect.currentframe().f_back
	for i in range(-level):
		frame = frame.f_back
	info = inspect.getargvalues(frame)
	assert info.varargs is None
	return {**{arg: info.locals[arg] for arg in info.args}, **info.locals[info.keywords]}


def _get_caller_filename(level: int = 0) -> str:
	frame = inspect.currentframe().f_back
	for i in range(-level):
		frame = frame.f_back
	return inspect.getframeinfo(frame).filename


_exposed = {}


def expose(cls, level=-1):
	print('\n'*10)
	#path = godot.ProjectSettings.localize_path(_get_caller_filename(-1))
	path = _get_caller_filename(level)
	_exposed[path] = cls

	cls.__class__ = script_class_type.script_class_type
	cls._script_class = cls
	print(f'expose({cls!r}) {path}')
	return cls

#godot.expose = expose

import functools

def _expose_script_class(cls_or_none: type | None = None, level=-1, **kwargs):
	if cls_or_none is None:
		return functools.partial(_expose_script_class, lavel=level, **kwargs)

	cls = cls_or_none

	path = _get_caller_filename(level)
	_exposed[path] = cls

	cls.__class__ = script_class_type.script_class_type
	cls._script_class = cls

	cls._expose_params = kwargs

	#print(f'expose({cls!r}) {path} {kwargs}')

	return cls



def expose_script_class(cls: type | None = None, name: str | None = None, as_global: bool = False, icon: str | None = None, tool: bool = False):
	if cls is None:
		return functools.partial(expose_script_class, name=name, as_global=as_global, icon=icon, tool=tool)

	class_info = godot.exposition.get_class_info(cls) # XXX

	if name:
		class_info.name = name

	if as_global:
		class_info.as_global = True

	return _expose_script_class(cls, name=name, as_global=as_global, icon=icon, tool=tool, level=-2)


godot.expose_script_class = expose_script_class # XXX




#@bind_all_methods
@register_extension_class
#@utils.log_method_calls
class PythonScript(godot.ScriptExtension):
	__scripts = weakref.WeakSet()

	@classmethod
	def get_all_scripts(cls) -> set[PythonScript]:
		return set(cls.__scripts)

	@utils.dont_log_calls
	def __repr__(self):
		return f'<PythonScript {getattr(self, "_path", "")!r}>'

	@property
	def _class(self) -> type:
		_class = self.__dict__.get('_class')

		if _class is None:
			self._reload(True) # XXX

		return self.__dict__.get('_class')


	def __init__(self, *args, path: str | None = None, **kwargs):
		super().__init__(*args, **kwargs)

		self._valid = False

		self._placeholder_fallback_enabled = False

		self._source = None
		self._path = path

		#print('\033[95;1mnew script!\033[0m')

		#print(self._path, hex(id(self)))
		#print(type(self), self.get_class())


		#if self._path is not None:
		#	self._set_source_code(pathlib.Path(self._path.removeprefix('res://')).read_text()) # XXX

		self._instances = weakref.WeakSet()


		type(self).__scripts.add(self)

	def _editor_can_reload_from_file(self) -> bool:
		return False

	def _placeholder_erased(self, placeholder: object) -> None:
		raise NotImplementedError

	def _can_instantiate(self) -> bool:
		if not self._valid:
			return False

		if godot.Engine.is_editor_hint():
			return self._is_tool()

		return True

	def _get_base_script(self) -> godot.Script:
		# _most_derived_non_script_base(self._class)
		return None
		raise NotImplementedError

	def _get_global_name(self) -> str:
		#try:
		params = getattr(self._class, '_expose_params', {})
		if params.get('as_global') or params.get('name'):
			name = params.get('name', None) or self._class.__name__
			return name
		#except Exception:
		#	return '' # XXX
		return ''
		#raise NotImplementedError


	def _get_icon_path(self): # XXX: not inherited
		try:
			params = getattr(self._class, '_expose_params', {})
			return params.get('icon', '')
		except Exception:
			return '' # XXX
		return ''
		#raise NotImplementedError


	def _inherits_script(self, script: godot.Script) -> bool:
		return script is self # XXX
		raise NotImplementedError

	def _get_instance_base_type(self) -> str:
		try:
			for cls in self._class.mro():
				if getattr(cls, '_extension_class', None) is cls or getattr(cls, '_godot_class', None) is cls:
					return cls.__name__
		except Exception:
			return '' # XXX
		return ''

	def _instance_create(self, for_object: godot.Object) -> object:
		with utils.print_exceptions_and_reraise(): # XXX: why does traceback get lost without this?
			script_class_type.set_script_class(for_object, self._class)

		self._instances.add(for_object)

		#import gc
		#insts = [obj for obj in gc.get_referrers(self._class, *self._class.__subclasses__()) if isinstance(obj, self._class)]
		#print(insts)

		#import importlib
		#importlib.reload(sys.modules['Node'])

		#_class = _exposed.get(self._path)

		#if _class is None:
		#	raise RuntimeError(f'failed to load {self._path}')

		#self.__dict__['_class'] = _class

		#for inst in insts:
		#	#inst.__class__ = _class
		#	script_class_type.set_script_class(inst, _class)

		return gde.script_instance_create(python_script_instance.PythonScriptInstanceInfo, for_object)

	def _placeholder_instance_create(self, for_object: godot.Object) -> object:
		placeholder = gde.placeholder_script_instance_create(self._get_language(), self, for_object)

		gde.placeholder_script_instance_update(placeholder, self._get_script_property_list(), {'speed': 250}) # XXX

		return placeholder

		return self._instance_create(for_object)
		raise NotImplementedError

	def _instance_has(self, object: godot.Object) -> bool:
		raise NotImplementedError

	def _has_source_code(self) -> bool:
		return self._source is not None

	def _get_source_code(self) -> str:
		return self._source or ''

	def _set_source_code(self, code: str) -> None:
		self._source = code
		self._valid = True # XXX: where to do this?

		'''code_obj = compile(self._source,
			filename = self._path,
			mode = 'exec',
			flags = 0,
			dont_inherit = True,
			optimize = -1) # XXX

		exec(code_obj)'''

	def _reload(self, keep_state: bool = False) -> godot.Error:
		self._valid = False

		if not self._path:
			return godot.Error.FAILED

		import importlib

		module_name = utils.godot_path_to_python_module_name(self._path)
		module_name = module_name.removesuffix('.__init__') # XXX

		try:
			with utils.print_exceptions_and_reraise():
				# XXX: dependant scripts?
				if module := sys.modules.get(module_name):
					importlib.reload(module) # XXX
				else:
					module = importlib.import_module(module_name) # XXX

		except Exception:
			return godot.Error.FAILED

		_class = _exposed.get(self._path)

		if _class is None:
			return godot.Error.FAILED
			#raise RuntimeError(f'failed to load {self._path}')

		self.__dict__['_class'] = _class

		self._valid = True

		for inst in set(self._instances):
			with utils.print_exceptions_and_continue():
				script_class_type.set_script_class(inst, _class)

		return godot.Error.OK

	def _get_documentation(self) -> list[dict]:
		class_info = godot.exposition.get_class_info(self._class)

		from godot._internal import type_info

		docs = inspect.getdoc(class_info.class_)
		docs = docs or ''

		brief_docs = ''

		doc_lines = docs.splitlines()
		if len(doc_lines) >= 3 and doc_lines[0] and not doc_lines[1] and doc_lines[2]:
			brief_docs = doc_lines[0]
			docs = '\n'.join(doc_lines[2:])

		if not docs:
			docs = 'There is currently no description for this class.'
		if docs:
			docs += '\n'
		docs = f'''{docs}[b]Note:[/b] Documentation support for Python scripts is not fully implemented yet.'''


		import ast


		class DefinitionFinder(ast.NodeVisitor):
			@classmethod
			def find(cls, sought_qualnames: str | list | set | None = None, *, tree: ast.AST) -> str | dict:
				find_single = isinstance(sought_qualnames, str)

				if find_single:
					sought_qualnames = {sought_qualnames}

				visitor = cls(sought_qualnames)
				visitor.visit(tree)

				if find_single:
					return visitor.found_qualnames.popitem()[1]

				else:
					return visitor.found_qualnames

			def __init__(self, sought_qualnames: set | None):
				self.stack = []

				self.sought_qualnames = sought_qualnames

				if sought_qualnames:
					self.found_qualnames = {name: None for name in self.sought_qualnames}

				else:
					self.found_qualnames = {}

			def _check_qualname(self, line_index: int):
				qualname = '.'.join(self.stack)

				if self.sought_qualnames and qualname not in self.sought_qualnames:
					return

				if self.found_qualnames.get(qualname) is not None:
					return

				self.found_qualnames[qualname] = line_index

			def visit_FunctionDef(self, node):
				self.stack.append(node.name)

				self._check_qualname(node.lineno)

				self.stack.append('<locals>')

				self.generic_visit(node)

				self.stack.pop()
				self.stack.pop()

			visit_AsyncFunctionDef = visit_FunctionDef

			def visit_ClassDef(self, node):
				self.stack.append(node.name)

				self._check_qualname(node.lineno)

				self.generic_visit(node)

				self.stack.pop()

			def visit_AnnAssign(self, node):
				if not isinstance(node.target, ast.Name):
					return

				self.stack.append(node.target.id)

				self._check_qualname(node.lineno)

				self.stack.pop()



		def _get_prop_comment(prop):
			tree = ast.parse(self._source)
			line_index = DefinitionFinder.find(f'{self._get_global_name()}.{prop.name}', tree = tree)
			defs = DefinitionFinder.find(tree = tree)
			print(defs)
			line = self._source.splitlines()[line_index - 2]

			if line.strip().startswith('##'):
				return line.strip().removeprefix('##').strip()

			return None


		return [
			dict(
				name = self._get_global_name() or f'"{self._path.removeprefix("res://")}"',
				is_script_doc = True,
				script_path = f'"{self._path.removeprefix("res://")}"',
				inherits = 'Node2D',
				brief_description = brief_docs,
				description = docs,
				methods = [
					dict(
						name = m.name,
						return_type = utils.fullname(m.info.return_value_info.python_type) if m.info.return_value_info.python_type else 'void',
						description = inspect.getdoc(m) or '',
						arguments = [
							dict(
								name = a.name,
								type = type_info.TypeInfo.from_property_info(a).doc_type_string,
							) for a in m.info.arguments_info
						],
					) for m in class_info.methods.values()
				],
				properties = [
					dict(
						name = prop.name,
						type = type_info.TypeInfo.from_property_info(prop).doc_type_string,
						description = inspect.getdoc(prop) or inspect.getcomments(prop) or _get_prop_comment(prop) or '',
					) for prop in class_info.properties.values()
				],
			)
		]

	def _has_method(self, method: str) -> bool:
		return False
		raise NotImplementedError

	def _get_method_info(self, method: str) -> dict:
		raise NotImplementedError

	def _is_tool(self) -> bool:
		params = getattr(self._class, '_expose_params', {})
		return params.get('tool', False)

	def _is_valid(self) -> bool:
		return self._valid

	@utils.dont_log_calls
	def _get_language(self) -> godot.ScriptLanguage:
		return python_language.PythonLanguage.get()

	def _has_script_signal(self, signal: str) -> bool:
		class_info = godot.exposition.get_class_info(self._class)
		return signal in class_info.signals.keys()

	def _get_script_signal_list(self) -> list[dict]:
		return [
			dict(
				name = 'test_signal',
				args = [],#[PropertyInfo(), ],
				default_args = [],
				**{'return': {}},#PropertyInfo(),
				flags = 0,
			),
		]

		#raise NotImplementedError

	@utils.dont_log_calls
	def _has_property_default_value(self, property: str) -> bool:
		return False
		raise NotImplementedError

	@utils.dont_log_calls
	def _get_property_default_value(self, property: str) -> godot.Variant:
		return None
		raise NotImplementedError

	def _update_exports(self) -> None:
		pass#raise NotImplementedError

	def _get_script_method_list(self) -> list[dict]:
		return []
		raise NotImplementedError

	def _get_script_property_list(self) -> list[dict]:
		class_info = godot.exposition.get_class_info(self._class)

		script_source_prop = dict(
			type = godot.Variant.Type.TYPE_NIL,
			name = godot.String(self.resource_path).get_file() if not self.resource_name else self.resource_name,
			hint = godot.PROPERTY_HINT_NONE,
			hint_string = self.resource_path,
			usage = godot.PROPERTY_USAGE_CATEGORY,
		)


		script_source_prop2 = dict(
			type = godot.Variant.Type.TYPE_STRING,
			name = 'script/source',
			usage = godot.PROPERTY_USAGE_NO_EDITOR | godot.PROPERTY_USAGE_INTERNAL,
		)

		return [script_source_prop, script_source_prop2] + [prop.as_dict() for prop in class_info.properties.values()]

	def _get_member_line(self, member: str) -> int:
		raise NotImplementedError

	def _get_constants(self) -> dict:
		return {}

	def _get_members(self) -> list[str]:
		return []

	@utils.dont_log_calls
	def _is_placeholder_fallback_enabled(self) -> bool:
		return self._placeholder_fallback_enabled

	def _get_rpc_config(self) -> godot.Variant:
		raise NotImplementedError


