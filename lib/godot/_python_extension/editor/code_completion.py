import re
import pathlib
import keyword
import symtable
import weakref
import builtins

import godot


# used by godot to mark the cursor location
_cursor = '\uffff'

# any valid identifer
_ident_pattern = re.compile(rf'(?<!{_cursor})\b(?!\d)\w+\b(?!{_cursor})') # TODO: check regex pattern

# a valid identifer where the cursor is located
_current_ident_pattern = re.compile(rf'(\b(?!\d)\w+|\B){_cursor}(\w+\b|\B)') # TODO: check regex pattern


def _make_option(name: str,
			kind = godot.CodeEdit.CodeCompletionKind.KIND_PLAIN_TEXT,
			location = godot.CodeEdit.CodeCompletionLocation.LOCATION_OTHER,
		) -> godot.Dictionary:
	return godot.Dictionary(
			kind = kind,
			display = name,
			insert_text = name,
			font_color = godot.Color(),
			icon = None,
			default_value = 0,
			location = location,
			matches = [
			],
		)


def _get_all_identifiers(*, code: str | None = None, path: pathlib.Path | None = None) -> str:
	if not code:
		if not path:
			raise TypeError(f'need either `code` or `path`')

		code = path.read_text()

	def _process_namespace(namespace: symtable.SymbolTable) -> set:
		idents = set()

		for sym in namespace.get_symbols():
			idents.add(sym.get_name())

		for ns in namespace.get_children():
			idents |= _process_namespace(ns)

		return idents

	try:
		return _process_namespace(symtable.symtable(code, str(path) if path else '', 'exec'))

	except SyntaxError as exc:
		# fallback to regex if parsing fails
		return set(m[0] for m in re.finditer(_ident_pattern, code))


# TODO: integrate this deeper into bindings, will be needed in many places
class WeakCallable:
	def __init__(self, method):
		self.ref = weakref.WeakMethod(method)
		self.name = f'{method.__self__.__class__.__qualname__}.{method.__name__}'

	def __call__(self, *args, **kwargs):
		if func := self.ref():
			return func(*args, **kwargs)

	def __bool__(self):
		return bool(self.ref)

	def __eq__(self, other):
		if isinstance(other, weakref.ref):
			other = other()

		elif isinstance(other, __class__):
			other = other.ref()

		func = self.ref()

		return func == other

	def __hash__(self):
		return hash(self.ref())

	def __repr__(self):
		obj = None
		if method := self.ref():
			obj = method.__self__
		return f'<WeakCallable {self.name} of {obj!r}>'

	__str__ = __repr__


class _Completer:
	def __init__(self):
		self._godot_api_options = {}
		self._options_per_module = {}

		fs = godot.EditorInterface.get_resource_filesystem()
		fs.filesystem_changed.connect(WeakCallable(self._filesystem_changed))

	def __del__(self):
		fs = godot.EditorInterface.get_resource_filesystem()
		fs.filesystem_changed.disconnect(self._filesystem_changed)

	def _filesystem_changed(self):
		self._options_per_module = {}

	def _update_godot_api_options(self):
		if self._godot_api_options:
			return

		from godot._internal.api_info import api

		def visit(obj, path):
			match path:
				case ['classes' | 'builtin_classes', type_name]:
					self._godot_api_options[obj.name] = _make_option(obj.name,
						kind = godot.CodeEdit.CodeCompletionKind.KIND_CLASS)

				case ['classes' | 'builtin_classes', type_name, kind, name]:
					if 'name' not in obj:
						return

					match kind:
						case 'methods':
							kind = godot.CodeEdit.CodeCompletionKind.KIND_FUNCTION
						case 'properties' | 'members':
							kind = godot.CodeEdit.CodeCompletionKind.KIND_MEMBER
						case 'constants':
							kind = godot.CodeEdit.CodeCompletionKind.KIND_CONSTANT
						case 'signals':
							kind = godot.CodeEdit.CodeCompletionKind.KIND_SIGNAL
						case _:
							kind = godot.CodeEdit.CodeCompletionKind.KIND_PLAIN_TEXT

					self._godot_api_options[obj.name] = _make_option(obj.name,
						kind = kind)

				case ['global_enums', type_name]:
					self._godot_api_options[obj.name] = _make_option(obj.name,
						kind = godot.CodeEdit.CodeCompletionKind.KIND_ENUM)

				case ['global_enums', type_name, 'values', name]:
					self._godot_api_options[obj.name] = _make_option(obj.name,
						kind = godot.CodeEdit.CodeCompletionKind.KIND_CONSTANT)

		godot._internal.api_info.visit_object_with_path(api, visit, try_get_names=True)

	def _update_options_per_module(self):
		if self._options_per_module:
			return

		for path in pathlib.Path().glob('**/*.py'):
			self._options_per_module[path] = {
					ident: _make_option(ident,
						location = godot.CodeEdit.CodeCompletionLocation.LOCATION_OTHER_USER_CODE
					)
					for ident in _get_all_identifiers(path=path)
				}

	def complete(self, code: str, path: str, owner: godot.Object) -> dict:
		self._update_godot_api_options()
		self._update_options_per_module()

		local_idents = {
				ident: _make_option(ident,
					location = godot.CodeEdit.CodeCompletionLocation.LOCATION_LOCAL
				)
				for ident in _get_all_identifiers(
						code = re.sub(_current_ident_pattern, '_', code, count=1),
						path = path
					)
				if ident != '_'
			}

		idents = {}

		# TODO: builtins?
		idents.update({ident: _make_option(ident) for ident in dir(builtins)})

		# TODO: imported modules?

		for module_idents in self._options_per_module.values():
			idents.update(module_idents)

		idents.update(local_idents)

		idents.update(self._godot_api_options)

		# XXX: should keywords be filtered?
		idents = {ident: option for ident, option in idents.items() if not keyword.iskeyword(ident)}

		pre, post = '', ''

		if match_ := re.search(_current_ident_pattern, code):
			pre, post = match_.groups()

		if pre or post:
			idents = {
				ident: option
				for ident, option in idents.items()
				if ident.lower().startswith(pre.lower()) and ident.lower().endswith(post.lower())
			}

		return godot.Dictionary(
			result = godot.Error.OK,
			force = False,
			call_hint = "",
			options = [
				*idents.values()
			],
		)


_completer = _Completer()


def complete(code: str, path: str, owner: godot.Object) -> dict:
	return _completer.complete(code, path, owner)


