# project

project = 'godot-python-extension'
copyright = '2023, Mai Lavelle'
author = 'Mai Lavelle'


# general

extensions = ['myst_parser']

exclude_patterns = [
	'.*',
	'*build/**',
]


# html

html_theme = 'furo'
html_static_path = ['_static']

html_logo = '_static/python-script.png'
html_title = 'godot-python documentation'

html_css_files = [
	'custom.css',
]

