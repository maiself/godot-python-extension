import types


class reuse_type_object_meta(type):
	__reuse_type_objects = {}

	def __new__(meta, name, bases, namespace, *,
		reuse_type_object: bool = True,
		reuse_type_object_key = None,
		**kwargs
	):
		if not reuse_type_object:
			return super().__new__(meta, name, bases, namespace, **kwargs)

		if not reuse_type_object_key:
			reuse_type_object_key = '.'.join((namespace['__module__'], namespace['__qualname__']))

		if not (cls := meta.__reuse_type_objects.get(reuse_type_object_key)):
			# create new type object
			cls = super().__new__(meta, name, bases, namespace, **kwargs)

			meta.__reuse_type_objects[reuse_type_object_key] = cls

		else:
			# reuse existing type object

			cls.__class__ = meta

			# set __classcell__
			if __classcell__ := namespace.get('__classcell__'):
				__classcell__.cell_contents = cls

			# set bases
			cls.__bases__ = types.resolve_bases(bases) or (object, )

			# implicitly convert __init_subclass__ to classmethod
			if __init_subclass__ := namespace.get('__init_subclass__'):
				if not isinstance(__init_subclass__, classmethod):
					namespace['__init_subclass__'] = classmethod(__init_subclass__)

			# set attributes
			for attr_name, attr_value in namespace.items():
				if attr_name == '__classcell__':
					continue

				setattr(cls, attr_name, attr_value)

			# call __set_name__
			for attr_name, attr_value in namespace.items():
				if __set_name__ := getattr(attr_value, '__set_name__', None):
					__set_name__(cls, attr_name)

			# call __init_subclass__
			super(cls, cls).__init_subclass__(**kwargs)

		return cls

	@classmethod
	def reset(meta, reuse_type_object_key = None):
		if reuse_type_object_key:
			return meta.__reuse_type_objects.pop(reuse_type_object_key)

		reset, meta.__reuse_type_objects = meta.__reuse_type_objects, {}

		return reset


class reuse_type_object(metaclass = reuse_type_object_meta):
	pass


