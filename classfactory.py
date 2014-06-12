# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:		classfactory
#-------------------------------------------------------------------------------

__all__ = ["ClassModuleUpdater", "AssignmentError"]

import sys
import logging
from os.path import dirname, exists, getmtime, join as pjoin

from collections import OrderedDict
from datetime import datetime, date
from decimal import Decimal


#=##################################################################################################
class ArgumentError(Exception):
	"""
	An error from creating or using an argument (optional or positional).
	"""

	def __init__(self, argument, message):
		self.argname, self.msg = argument, argument + ": " + message

	def __str__(self):
		return 'argument {0}: {1}'.format(self.argname, self.msg)


#=##################################################################################################
class AssignmentError(Exception):
	"""An error from assigning a wrong type or value to a field."""

	def __init__(self, fieldname, message):
		self.fieldname, self.msg = fieldname, message

	def __str__(self):
		return 'field {0}: {1}'.format(self.fieldname, self.msg)


#=##################################################################################################
class UnknownFieldTypeError(Exception):
	"""An error from creating or using an argument (optional or positional)."""

	def __init__(self, field_name, field_type):
		self.fieldname, self.fieldtype = field_name, field_type

	def __str__(self):
		return 'field {0}: "{1}" unknown field type'.format(self.fieldname, self.fieldtype)


#=##################################################################################################
class AquaBase():
	def __init__(self, classname, spec):
		self._spec = [classname] + spec
		self.fields = self._create_fields_dict()

	def _create_fields_dict(self):
		funcs = {
				'i':	["_set_int",	"_chk_int",		"_out_int"],
				's':	["_set_str",	"_chk_str",		"_out_str"],
				'dt':	["_set_date",	"_chk_date",	"_out_date"],
				'd':	["_set_dec",	"_chk_dec",		"_out_dec"]
				}
		fields = OrderedDict()
		for fld in self._spec[1:]:
			d = fld.split(',')
			typ = d[1]
			l = d[2].split('.')
			field_len = int(l[0])
			dec_len = int(l[1] if len(l) > 1 else 0)

			key = d[0].lower().replace('-', '_')
			if typ not in funcs.keys():
				raise UnknownFieldTypeError(key, typ)

			fields[key] = dict(
							field_type = typ,
							field_len = field_len,
							dec_len = dec_len,
							set = funcs[typ][0],
							chk = funcs[typ][1],
							out = funcs[typ][2],
							)
		return fields

	# _set_int(), _chk_int(), _out_int()
	def _set_int(self, field_name, value):
		value = str(value)
		self._chk_int(field_name, value)
		setattr(self, '_' + field_name, int(value))

	def _chk_int(self, field_name, value):
		d = self.fields[field_name]
		field_len, dec_len = d['field_len'], d['dec_len']
		if dec_len != 0:
			raise AssignmentError(field_name, 'int fields can not have decimals')
		if len(str(value).strip('-+')) > field_len:
			raise OverflowError('{0} max length is {1}: trying to assign value [{2}]'.format(field_name, field_len, value))

	def _out_int(self, field_name):
		d = self.fields[field_name]
		field_len = d['field_len']
		return '{:0=+{w}n}'.format(getattr(self, field_name), w=(field_len + 1))

	# _set_dec(), _chk_dec(), _out_dec()
	def _set_dec(self, field_name, value):
		v = str(value).replace(',', '.').split('.')
		if len(v) > 1:
			dec_len = self.fields[field_name]['dec_len']
			v[1] = v[1][:dec_len]
			value = Decimal('.'.join(v))
		self._chk_dec(field_name, value)
		setattr(self, '_' + field_name, Decimal(value))

	def _chk_dec(self, field_name, value):
		d = self.fields[field_name]
		field_len, dec_len = d['field_len'], d['dec_len']
		v = str(value).replace('+', '').replace('-', '').split('.')
		if len(v[0]) > field_len:
			raise OverflowError('{0} integer part length is {1}: trying to assign value [{2}]'.format(field_name, field_len, value))
		if len(v) > 1 and len(v[1]) > dec_len:
			raise OverflowError('{0} fractional part length is {1}: trying to assign value [{2}]'.format(field_name, dec_len, value))

	def _out_dec(self, field_name):
		d = self.fields[field_name]
		field_len, dec_len = d['field_len'], d['dec_len']
		return '{:0=+{w}.{p}f}'.format(float(getattr(self, field_name)), w=field_len + dec_len + 2, p=dec_len).replace('.', '')

	# _set_date(), _chk_date(), _out_date()
	def _set_date(self, field_name, value):
		if type(value) is str:
			value = datetime.strptime(value, '%Y%m%d').date()
		if type(value) is datetime:
			value = value.date()
		self._chk_date(field_name, value)
		setattr(self, '_' + field_name, value)

	def _chk_date(self, field_name, value):
		if type(value) not in [type(None), date]:
			raise AssignmentError(field_name, 'trying to assign value [{0}] of type {1} to a date field'.format(value, type(value)))

	def _out_date(self, field_name):
		dt = getattr(self, field_name)
		return dt.strftime('%Y%m%d') if dt is not None else '        '

	# _set_str(), _chk_str(), _out_str()
	def _set_str(self, field_name, value):
		value = value.rstrip()
		self._chk_str(field_name, value)
		setattr(self, '_' + field_name, value)

	def _chk_str(self, field_name, value):
		d = self.fields[field_name]
		field_len, dec_len = d['field_len'], d['dec_len']
		if dec_len != 0:
			raise AssignmentError(field_name, 'string fields can not have decimals')
		if len(str(value)) > field_len:
			raise OverflowError('{0} max length is {1}: trying to assign value [{2}]'.format(field_name, field_len, value))

	def _out_str(self, field_name):
		field_len = self.fields[field_name]['field_len']
		return '{: <{w}.{w}s}'.format(getattr(self, field_name), w=field_len)


#=##################################################################################################
class ClassFactory(AquaBase):
	def __init__(self, classname, spec):
		super().__init__(classname, spec)
		if classname is None or len(classname.strip()) == 0:
			raise ArgumentError("classname", "can't be None or empty")
		if spec is None or len(spec) == 0 or type(spec) is not list:
			raise ArgumentError("spec", "can't be None or empty and must be a list object")
		self._spec = [classname] + spec
		self._class_name = self._spec[0]
		if sys.version_info.major > 2:
			self.fields = super(ClassFactory, self)._create_fields_dict()
		else:
			self.fields = AquaBase(classname, spec)._create_fields_dict()

	@property
	def get_class_definition(self):
		types = { 'i': "int()", 's': "str()", 'dt': "None", 'd': "Decimal('0.{0}')" }
		c = []

		# <<< class --------------------------------------------------------------------------------
		c +=["class {0}(AquaBase):".format(self._class_name)]

		# <<< __init__ -----------------------------------------------------------------------------
		c +=["	def __init__(self):"]

		for key in self.fields.keys():
			field = self.fields[key]
			typ = field['field_type']
			c += ["		self._{0} = {1}".format(key, types[typ].format('0' * field['dec_len']))	]

		c += [
			"		self.fields = " + str(self.fields),
			""
			]
		# >>> __init__ -----------------------------------------------------------------------------

		# _get_XXX, set_XXX, xxx = property(...)
		for key in self.fields.keys():
			c += [
				"	def _get_{0}(self):".format(key),
				"		return self._{0}".format(key),

				"	def _set_{0}(self, value):".format(key),
				"		self.{0}('{1}', value)".format(self.fields[key]['set'], key),

				"	{0} = property(_get_{0}, _set_{0})".format(key),
				""
				]

		# __str__()
		c += [
			"	def __str__(self):",
			"		return " + ' + '.join(["self.{0}('{1}')".format(self.fields[k]['out'], k) for k in self.fields.keys()]),
			""
			]

		# __repr__()
		c += [
			"	def __repr__(self):",
			"		s = ['\t{0}:\t<{1}>\\n'.format(x, getattr(self, x)) for x in self.fields.keys()]",
			"		return '<class: {0}>\\n'.format(self.__class__.__name__) + ''.join(s)",
			""
			]

		# >>> class --------------------------------------------------------------------------------
		return c

	@property
	def get_class(self):
		c = self.get_class_definition
		exec('\n'.join(c))
		return locals()[self._class_name]


#=##################################################################################################
class ClassDefinitionReader():
	def __init__(self, file_name):
		self._file_name = file_name

	def _read(self):
		with open(self._file_name, 'r') as fin:
			lines = map(lambda x: x.strip('\n'), fin.readlines())

		return list(filter(lambda x: not (x.startswith('#') or x.strip() == ''), lines))

	def parse(self):
		lines = self._read()

		classdefs = {}
		for line in [x.split('\t') for x in lines]:
			if line[0] not in classdefs:
				classdefs[line[0]] = []
			classdefs[line[0]] += [line[1]]
		return classdefs


#=##################################################################################################
class ClassModuleUpdater():
	def __init__(self, classdef_file_name):
		self._classdefs_file = pjoin(dirname(sys.argv[0]), 'classdefs.txt') if classdef_file_name is None else classdef_file_name
		self._out_file = pjoin(dirname(self._classdefs_file), 'aquaclasses.py')
		self._classes = {}
		self._definitions = {}

	def _write_class_module(self):
		sep = '\n\n#=##################################################################################################'
		imports =	[
					"# -*- Mode: Python; tab-width: 4 -*-",
					"# -*- coding: utf-8 -*-",
					"#-------------------------------------------------------------------------------",
					"# Name:		aquaclasses",
					"#-------------------------------------------------------------------------------",
					"",
					"__all__ = " + str(list(self._definitions.keys())),
					"",
					"from collections import OrderedDict",
					"from datetime import datetime, date",
					"from decimal import Decimal",
					"from classfactory import AquaBase",
					"",
					sep,
					'class AssignmentError(Exception):',
					'	"""An error from assigning a wrong type or value to a field."""',
					'',
					'	def __init__(self, fieldname, message):',
					'		self.fieldname, self.msg = fieldname, message',
					'',
					'	def __str__(self):',
					'		return "field {0}: {1}".format(self.fieldname, self.msg)',
					''
					]

		with open(self._out_file, 'w') as outfile:
			outfile.write('{code}\n'.format(code="\n".join(imports)))

			for k in self._definitions.keys():
				outfile.write('{sep}\n{code}\n'.format(code="\n".join(self._definitions[k]), sep=sep))

	def get_classes(self):
		classdefs = ClassDefinitionReader(self._classdefs_file).parse()
		for k in classdefs.keys():
			factory = ClassFactory(k, classdefs[k])
			self._definitions[k] = factory.get_class_definition
			self._classes[k] = factory.get_class

		return self._classes

	def _update(self):
		if not exists(self._out_file) or getmtime(self._out_file) < getmtime(self._classdefs_file):
			if not self._classes:
				self.get_classes()
			self._write_class_module()
			logging.info('{0} recreated'.format(self._out_file))


#=##################################################################################################
#=##################################################################################################


def main():
	logging.basicConfig(filename=sys.argv[2], format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG)
	ClassModuleUpdater(sys.argv[1])._update()


if __name__ == '__main__':
	main()
