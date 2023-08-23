import godot

from godot._internal.extension_classes import *

from . import utils

from .python_script import PythonScript


#@bind_all_methods
@register_extension_class
#@utils.log_method_calls
class PythonLanguage(godot.ScriptLanguageExtension):
	__instance = None

	@classmethod
	def get(cls):
		return cls.__instance

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		type(self).__instance = self

	@utils.dont_log_calls
	def _get_name(self) -> str:
		return 'Python'

	def _init(self) -> None:
		pass

	@utils.dont_log_calls
	def _get_type(self) -> str:
		return 'PythonScript'

	@utils.dont_log_calls
	def _get_extension(self) -> str:
		return 'py'

	def _finish(self) -> None:
		pass#raise NotImplementedError

	@utils.dont_log_calls
	def _get_reserved_words(self) -> list[str]:
		import keyword
		return keyword.kwlist + keyword.softkwlist

	@utils.dont_log_calls
	def _is_control_flow_keyword(self, keyword: str) -> bool:
		return keyword in (
			'await',
			'break',
			'continue',
			'elif',
			'else',
			'except',
			'finally',
			'for',
			'if',
			'pass',
			'raise',
			'return',
			'try',
			'while',
			'with',
			'yield',
		)

	@utils.dont_log_calls
	def _get_comment_delimiters(self) -> list[str]:
		return ['#']

	@utils.dont_log_calls
	def _get_string_delimiters(self) -> list[str]:
		return [f'{d} {d}' for d in ('"', "'", '"""', "'''")]

	def _make_template(self, template: str, class_name: str, base_class_name: str) -> godot.Script:
		global script # XXX
		script = PythonScript()
		script.set_source_code(f'# test script\n\n# {class_name} : {base_class_name}')
		return script

	def _get_built_in_templates(self, object: str) -> list[dict]:
		raise NotImplementedError

	def _is_using_templates(self) -> bool:
		return False

	def _validate(self, script: str, path: str,
			validate_functions: bool,
			validate_errors: bool,
			validate_warnings: bool,
			validate_safe_lines: bool) -> dict:
		import ast

		errors = []

		#for line_num, line in enumerate(script.splitlines()):
		for line in [script]:
			try:
				ast.parse(source = line, filename = path)

			except SyntaxError as err:
				errors.append(dict(
					#line = line_num,
					line = err.lineno,
					column = err.offset,
					message = f'{err.msg}',#: {err.text}',
				))

		return dict(
			valid = not errors,
			errors = errors,
		)

	def _validate_path(self, path: str) -> str:
		return '' # XXX ?

	def _create_script(self) -> godot.Object:
		return PythonScript()

	def _has_named_classes(self) -> bool:
		return True

	def _supports_builtin_mode(self) -> bool:
		return True

	def _supports_documentation(self) -> bool:
		return True

	def _can_inherit_from_file(self) -> bool:
		return True

	def _find_function(self, class_name: str, function_name: str) -> int:
		raise NotImplementedError

	def _make_function(self, class_name: str, function_name: str, function_args: list[str]) -> str:
		raise NotImplementedError

	def _open_in_external_editor(self, script: godot.Script, line: int, column: int) -> godot.Error:
		raise NotImplementedError

	def _overrides_external_editor(self) -> bool:
		return False

	def _complete_code(self, code: str, path: str, owner: godot.Object) -> dict:
		raise NotImplementedError

	def _lookup_code(self, code: str, symbol: str, path: str, owner: godot.Object) -> dict:
		raise NotImplementedError

	def _auto_indent_code(self, code: str, from_line: int, to_line: int) -> str:
		raise NotImplementedError

	def _add_global_constant(self, name: str, value: godot.Variant) -> None:
		raise NotImplementedError

	def _add_named_global_constant(self, name: str, value: godot.Variant) -> None:
		raise NotImplementedError

	def _remove_named_global_constant(self, name: str) -> None:
		raise NotImplementedError

	def _thread_enter(self) -> None:
		pass#raise NotImplementedError

	def _thread_exit(self) -> None:
		pass#raise NotImplementedError

	def _debug_get_error(self) -> str:
		raise NotImplementedError

	def _debug_get_stack_level_count(self) -> int:
		raise NotImplementedError

	def _debug_get_stack_level_line(self, level: int) -> int:
		raise NotImplementedError

	def _debug_get_stack_level_function(self, level: int) -> str:
		raise NotImplementedError

	def _debug_get_stack_level_locals(self, level: int, max_subitems: int, max_depth: int) -> dict:
		raise NotImplementedError

	def _debug_get_stack_level_members(self, level: int, max_subitems: int, max_depth: int) -> dict:
		raise NotImplementedError

	def _debug_get_stack_level_instance(self, level: int) -> object:
		raise NotImplementedError

	def _debug_get_globals(self, max_subitems: int, max_depth: int) -> dict:
		raise NotImplementedError

	def _debug_parse_stack_level_expression(self, level: int, expression: str, max_subitems: int, max_depth: int) -> str:
		raise NotImplementedError

	def _debug_get_current_stack_info(self) -> list[dict]:
		return []#raise NotImplementedError

	def _reload_all_scripts(self) -> None:
		for script in PythonScript.get_all_scripts():
			script.reload(True)

	def _reload_tool_script(self, script: godot.Script, soft_reload: bool) -> None:
		script.reload(soft_reload)

	def _get_recognized_extensions(self) -> list[str]:
		return ['py']

	def _get_public_functions(self) -> list[dict]:
		return []#raise NotImplementedError

	def _get_public_constants(self) -> dict:
		return {}#raise NotImplementedError

	def _get_public_annotations(self) -> list[dict]:
		return []#raise NotImplementedError

	def _profiling_start(self) -> None:
		raise NotImplementedError

	def _profiling_stop(self) -> None:
		raise NotImplementedError

	#def _profiling_get_accumulated_data(self, info_array: godot.ScriptLanguageExtensionProfilingInfo, info_max: int) -> int:
	#	raise NotImplementedError

	#def _profiling_get_frame_data(self, info_array: godot.ScriptLanguageExtensionProfilingInfo, info_max: int) -> int:
	#	raise NotImplementedError

	@utils.dont_log_calls
	def _frame(self) -> None:
		return
		raise NotImplementedError

	def _handles_global_class_type(self, type_: str) -> bool:
		return type_ in ('PythonScript')

	def _get_global_class_name(self, path: str) -> dict:
		res = godot.ResourceLoader.load(path)
		print(res, res._get_global_name())

		from .script_class_type import _most_derived_non_script_base # XXX

		if not res._get_global_name():
			return {}

		return dict(
			name = res._get_global_name(),
			base_type = _most_derived_non_script_base(res._class).__name__,
			icon_path = res._get_icon_path()
		)
		return {}#raise NotImplementedError



#print('godot.ScriptLanguageExtension')
#print(godot.ScriptLanguageExtension._get_extension._method_info)

