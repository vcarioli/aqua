# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
##----------------------------------------------------------------------------------------------------------------------
##	Name:		classfactory
##----------------------------------------------------------------------------------------------------------------------

from aquabase import AquaBase
from aquaerrors import ArgumentError

__all__ = ["ClassFactory"]


##======================================================================================================================


class ClassFactory(AquaBase):
	def __init__(self, classname, spec):
		super().__init__()
		if classname is None or len(classname.strip()) == 0:
			raise ArgumentError("classname", "can't be None or empty")
		if spec is None or len(spec) == 0 or type(spec) is not list:
			raise ArgumentError("_spec", "can't be None or empty and must be a list object")
		self._spec = [classname] + spec
		self.class_name = self._spec[0]
		self.fields = self.create_fields_dict(classname, spec)

	@property
	def class_definition(self):
		types = {'i': "int()", 's': "str()", 'dt': "None", 'd': "Decimal('0.{0}')"}
		c = []

		# <<< class --------------------------------------------------------------------------------
		c += ["class {0}(AquaBase):".format(self.class_name)]

		# <<< __init__ -----------------------------------------------------------------------------
		c += ["	def __init__(self):"]
		c += ["		super().__init__()"]

		for key in self.fields.keys():
			field = self.fields[key]
			typ = field['field_type']
			c += ["		self._{0} = {1}".format(key, types[typ].format('0' * field['dec_len']))]

		c += ["		self.fields = OrderedDict(["]
		i, n = 0, len(self.fields)
		for k in self.fields.keys():
			i += 1
			c += ["			('{0}', {1}){2}".format(k, str(self.fields[k]), "," if i < n else "")]
		c += ["		])", ""]

		# >>> __init__ -----------------------------------------------------------------------------

		# _get_XXX, set_XXX, xxx = property(...)
		for key in self.fields.keys():
			c += [
				"	def _get_{0}(self):".format(key),
				"		return self._{0}".format(key),
				"",
				"	def _set_{0}(self, value):".format(key),
				"		self.{0}('{1}', value)".format(self.fields[key]['set'], key),
				"",
				"	{0} = property(_get_{0}, _set_{0})".format(key),
				""
			]

		# __str__()
		c += [
			"	def __str__(self):",
			"		return	" + ' + \\\n\t\t\t\t'.join(["self.{0}('{1}')".format(self.fields[k]['get'], k) for k in self.fields.keys()]),
			""
		]

		# __repr__()
		c += [
			"	def __repr__(self):",
			"		s = ['\t{0}:\t<{1}>\\n'.format(x, getattr(self, x)) for x in self.fields.keys()]",
			"		return '<class: {0}>\\n'.format(self.__class__.__name__) + ''.join(s)"
		]

		# >>> class --------------------------------------------------------------------------------
		return c

	@property
	def get_class(self):
		c = self.class_definition
		exec('\n'.join(c))
		return locals()[self.class_name]
