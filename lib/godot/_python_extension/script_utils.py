import godot


def _is_script_class(cls: type) -> bool:
	if not isinstance(cls, type) or not issubclass(cls, godot.Object):
		raise TypeError(f'')
	if '_extension_class' in cls.__dict__ or '_godot_class' in cls.__dict__:
		return False
	return True


def _has_script_class_attr(cls: type, name: str) -> bool:
	for c in cls.mro():
		if not _is_script_class(cls):
			return False

		if name in c.__dict__:
			return True

	return False


def _get_script_class_attr(cls: type, name: str, default):
	for c in cls.mro():
		if not _is_script_class(c):
			return default

		if name in c.__dict__:
			return c.__dict__[name]

	return default



