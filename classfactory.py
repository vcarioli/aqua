# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:		classfactory
#-------------------------------------------------------------------------------

from aquabase import AquaBase
from aquaerrors import ArgumentError

__all__ = ["ClassFactory"]


#=##############################################################################
class ClassFactory(AquaBase):
	def __init__(self, classname, spec):
		AquaBase.__init__(self, classname, spec)
		if classname is None or len(classname.strip()) == 0:
			raise ArgumentError("classname", "can't be None or empty")
		if spec is None or len(spec) == 0 or type(spec) is not list:
			raise ArgumentError("__spec__", "can't be None or empty and must be a list object")
		self.__spec__ = [classname] + spec
		self.class_name = self.__spec__[0]
		self.__fields__ = AquaBase(classname, spec).__create_fields_dict__()

	@property
	def class_definition(self):
		types = {'i': "int()", 's': "str()", 'dt': "None", 'd': "Decimal('0.{0}')"}
		c = []

		# <<< class --------------------------------------------------------------------------------
		c += ["class {0}(AquaBase):".format(self.class_name)]

		# <<< __init__ -----------------------------------------------------------------------------
		c += ["	def __init__(self):"]

		for key in self.__fields__.keys():
			field = self.__fields__[key]
			typ = field['field_type']
			c += ["		self.__{0}__ = {1}".format(key, types[typ].format('0' * field['dec_len']))]

		c += ["		self.__fields__ = OrderedDict(["]
		i, n = 0, len(self.__fields__)
		for k in self.__fields__.keys():
			i += 1
			c += ["			('{0}', {1}){2}".format(k, str(self.__fields__[k]), "," if i < n else "")]
		c += ["		])", ""]

		# >>> __init__ -----------------------------------------------------------------------------

		# _get_XXX, set_XXX, xxx = property(...)
		for key in self.__fields__.keys():
			c += [
				"	def __get_{0}__(self):".format(key),
				"		return self.__{0}__".format(key),
				"",
				"	def __set_{0}__(self, value):".format(key),
				"		self.{0}('{1}', value)".format(self.__fields__[key]['set'], key),
				"",
				"	{0} = property(__get_{0}__, __set_{0}__)".format(key),
				""
			]

		# __str__()
		c += [
			"	def __str__(self):",
			"		return	" + ' + \\\n\t\t\t\t'.join(["self.{0}('{1}')".format(self.__fields__[k]['get'], k) for k in self.__fields__.keys()]),
			""
		]

		# __repr__()
		c += [
			"	def __repr__(self):",
			"		s = ['\t{0}:\t<{1}>\\n'.format(x, getattr(self, x)) for x in self.__fields__.keys()]",
			"		return '<class: {0}>\\n'.format(self.__class__.__name__) + ''.join(s)"
		]

		# >>> class --------------------------------------------------------------------------------
		return c

	@property
	def get_class(self):
		c = self.class_definition
		exec('\n'.join(c))
		return locals()[self.class_name]
