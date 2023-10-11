import functools

import godot


'''
This module contains extra utility functions added to the `godot` module for use from Python.
These utilities may or may not be the same as those available in GDScript.
'''


__all__ = (
	'load',
	'preload',
	'call_deferred',
)


load = godot.ResourceLoader.load
preload = godot.ResourceLoader.load # XXX: doesn't actually preload yet, needs detection in `PythonScript`


def call_deferred(func, *args, **kwargs):
	godot.Callable(functools.partial(func, *args, **kwargs)).call_deferred()


