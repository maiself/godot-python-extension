if __name__ != 'godot':
	import sys
	import warnings

	if 'godot' in sys.modules:
		raise ImportError(
			f'godot module already imported, cannot from another name: {__name__}')

	warnings.warn(
		f'importing godot module from another name: {__name__}',
		category = RuntimeWarning,
		stacklevel = 2,
	)

	sys.modules['godot'] = sys.modules[__name__]

	__name__ = 'godot'
	__package__ = __name__
	__spec__.name = __name__


from . import _internal

from .exposition import *

from .types import CustomCallable


