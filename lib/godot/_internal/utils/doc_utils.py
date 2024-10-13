import sys
import re
import types
import textwrap


_sgr = types.SimpleNamespace(
	bold = 1,
	dim = 2,
	italic = 3,
	underlined = 4,
	inverted = 7,

	not_bold = 22,
	not_dim = 22,
	not_italic = 23,
	not_underlined = 24,
	not_inverted = 27,
)


def _make_sgr(*args) -> str:
	return ';'.join((str(arg) for arg in args)).join(('\033[', 'm'))


def _remove_sgr(text: str) -> str:
	return re.sub(r'\033\[[0-9;]*m', '', text)


_replacements_for_tty = dict(
	br = '\n',

	b = _make_sgr(_sgr.bold),
	_b = _make_sgr(_sgr.not_bold),

	i = _make_sgr(_sgr.italic),
	_i = _make_sgr(_sgr.not_italic),

	code = _make_sgr(_sgr.inverted, _sgr.bold, _sgr.dim),
	_code = _make_sgr(_sgr.not_inverted, _sgr.not_bold, _sgr.not_dim),

	codeblock = _make_sgr(_sgr.bold, _sgr.dim),
	_codeblock = _make_sgr(_sgr.not_bold, _sgr.not_dim),
	codeblocks = _make_sgr(_sgr.bold, _sgr.dim),
	_codeblocks = _make_sgr(_sgr.not_bold, _sgr.not_dim),

	gdscript = f'{_make_sgr(_sgr.not_dim, _sgr.bold, _sgr.italic)}'
		+ f'  gdscript:{_make_sgr(_sgr.dim, _sgr.not_italic)}\n',
	_gdscript = _make_sgr(_sgr.not_bold, _sgr.not_dim),

	csharp = f'{_make_sgr(_sgr.not_dim, _sgr.bold, _sgr.italic)}'
		+ f'  csharp:{_make_sgr(_sgr.dim, _sgr.not_italic)}\n',
	_csharp = _make_sgr(_sgr.not_bold, _sgr.not_dim),
)


_replacements = {name: _remove_sgr(text) for name, text in _replacements_for_tty.items()}


def reformat_doc_bbcode(text: str, for_tty: None | bool = None) -> str:
	if for_tty is None:
		for_tty = sys.stdout.isatty() if sys.stdout else False

	replacements = _replacements_for_tty if for_tty else _replacements

	def replace(match_):
		groups = match_.groupdict()

		close = '_' if groups.get('close') else ''
		name = groups.get('name')
		value = groups.get('value')

		if value:
			return f'{replacements.get("b", "")}{value}{replacements.get("_b", "")}'

		if (res := replacements.get(close + name)) is not None:
			return res

		if close:
			return match_.group(0)

		return f'{replacements.get("b", "")}{name}{replacements.get("_b", "")}'

	text = re.sub(r'\[(?P<close>/)?(?P<name>[-_.\w/]+)( (?P<value>[-_.\w/]+))?\]', replace, text)
	text = text.replace('\n', '\n\n', 1)  # Separate first line from the rest by one blank line

	# TODO: Handle URLs
	# TODO: Implement word wrap if necessary

	return text
