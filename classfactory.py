# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:		classfactory
#-------------------------------------------------------------------------------

__all__ = ["ClassModuleUpdater", "AssignmentError"]

import sys
import logging
import os.path

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
				'i': ["_set_int", "_chk_int", "_get_int", "_out_int"],
				's': ["_set_str", "_chk_str", "_get_str", "_get_str"],
				'dt': ["_set_date", "_chk_date", "_get_date", "_get_date"],
				'd': ["_set_dec", "_chk_dec", "_get_dec", "_out_dec"]
		}
		fields = OrderedDict()
		for fld in [x.strip('\r') for x in self._spec[1:]]:
			try:
				d = fld.split(',')
				typ = d[1]
				l = d[2].split('.')
				field_len = int(l[0])
				dec_len = int(l[1] if len(l) > 1 else 0)

				key = d[0].lower().replace('-', '_')
				if typ not in funcs.keys():
					raise UnknownFieldTypeError(key, typ)

				fields[key] = dict(
					field_type=typ,
					field_len=field_len,
					dec_len=dec_len,
					set=funcs[typ][0],
					chk=funcs[typ][1],
					get=funcs[typ][2],
					out=funcs[typ][3]
				)
			except:
				logging.error("classfactory.py: _create_fields_dict(self): error decoding [{0}][{1}]".format(self._spec[0], fld))
				raise
		return fields

	# _set_int(), _chk_int(), _get_int(), _out_int()
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
			raise OverflowError(
				'{0} max length is {1}: trying to assign value [{2}]'.format(field_name, field_len, value)
			)

	def _get_int(self, field_name, sign='+'):
		d = self.fields[field_name]
		field_len = d['field_len']
		return '{:0={s}{w}n}'.format(getattr(self, field_name), s=sign, w=(field_len + len(sign)))

	def _out_int(self, field_name):
		return self._get_int(field_name, sign='')

	# _set_dec(), _chk_dec(), _get_dec(), _out_dec()
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
			raise OverflowError(
				'{0} integer part length is {1}: trying to assign value [{2}]'.format(field_name, field_len, value)
			)
		if len(v) > 1 and len(v[1]) > dec_len:
			raise OverflowError(
				'{0} fractional part length is {1}: trying to assign value [{2}]'.format(field_name, dec_len, value)
			)

	def _get_dec(self, field_name, dec_sep='', sign='+'):
		d = self.fields[field_name]
		field_len, dec_len = d['field_len'], d['dec_len']
		return '{:0={s}{w}.{p}f}'.format(float(getattr(self, field_name)), s=sign, w=field_len + dec_len + 1 + len(sign), p=dec_len).replace('.', dec_sep)

	def _out_dec(self, field_name):
		return self._get_dec(field_name, dec_sep=',', sign='')

	# _set_date(), _chk_date(), _get_date()
	def _set_date(self, field_name, value):
		if type(value) is str:
			value = None if value.rstrip(' ') == '' or value.rstrip('0') == '' else datetime.strptime(value, '%Y%m%d').date()
		elif type(value) is datetime:
			value = value.date()
		self._chk_date(field_name, value)
		setattr(self, '_' + field_name, value)

	@staticmethod
	def _chk_date(field_name, value):
		if type(value) not in [type(None), date]:
			raise AssignmentError(field_name, 'trying to assign value [{0}] of type {1} to a date field'.format(value, type(value)))

	def _get_date(self, field_name):
		dt = getattr(self, field_name)
		return dt.strftime('%Y%m%d') if dt is not None else '        '

	# _set_str(), _chk_str(), _get_str()
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

	def _get_str(self, field_name):
		field_len = self.fields[field_name]['field_len']
		return '{: <{w}.{w}s}'.format(getattr(self, field_name), w=field_len)

	@property
	def input_line(self):
		return '{: <8.8s}\t'.format(self.__class__.__name__) + '\t'.join([eval('self.' + self.fields[k]['out'] + '(k)') for k in self.fields.keys()])

	def pretty_print(self, prefix=''):
		fmts = {'i': '{val}', 'd': '{val}', 's': '"{val}"', 'dt': '"{val}"'}
		s = prefix + ('# ' if prefix == '' else ' = ') + self.__class__.__name__ + '()'
		prefix += '' if prefix == '' else '.'
		for k in self.fields.keys():
			funcs = {
				'i': 'self.' + k,
				'd': 'self.' + k,
				's': 'self.' + self.fields[k]['out'] + '(k)',
				'dt': 'self.' + self.fields[k]['out'] + '(k)'
			}
			t = self.fields[k]['field_type']
			s += ('\n{pfx}{name} = ' + fmts[t]).format(name=k, pfx=prefix, val=eval(funcs[t]))
		return s

	@property
	def csv_header(self):
		return ','.join(self.fields.keys())

	@property
	def csv(self):
		fmts = {'i': '{0}', 'd': '{0}', 's': '"{0}"', 'dt': '"{0}"'}
		return ','.join([fmts[self.fields[k]['field_type']].format(eval('self.' + k)) for k in self.fields.keys()])


#=##################################################################################################
class ClassFactory(AquaBase):
	def __init__(self, classname, spec):
		AquaBase.__init__(self, classname, spec)
		if classname is None or len(classname.strip()) == 0:
			raise ArgumentError("classname", "can't be None or empty")
		if spec is None or len(spec) == 0 or type(spec) is not list:
			raise ArgumentError("spec", "can't be None or empty and must be a list object")
		self._spec = [classname] + spec
		self._class_name = self._spec[0]
		self.fields = AquaBase(classname, spec)._create_fields_dict()

	@property
	def class_definition(self):
		types = {'i': "int()", 's': "str()", 'dt': "None", 'd': "Decimal('0.{0}')"}
		c = []

		# <<< class --------------------------------------------------------------------------------
		c += ["class {0}(AquaBase):".format(self._class_name)]

		# <<< __init__ -----------------------------------------------------------------------------
		c += ["	def __init__(self):"]

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
	def __init__(self, classdefs_fn, input_fn, output_fn):
		self._classdefs_file = os.path.join(os.path.dirname(sys.argv[0]), 'classdefs.txt') if classdefs_fn is None else classdefs_fn
		self._out_file = os.path.join(os.path.dirname(self._classdefs_file), 'aquaclasses.py')
		self._input_filename = input_fn
		self._output_filename = output_fn
		self._classes = {}
		self._definitions = {}

	def _write_class_module(self):
		sep = '\n\n#=##################################################################################################'
		imports = [
			"# -*- Mode: Python; tab-width: 4 -*-",
			"# -*- coding: utf-8 -*-",
			"#-------------------------------------------------------------------------------",
			"# Name:		aquaclasses",
			"#-------------------------------------------------------------------------------",
			"",
			"__all__ = " + str(list(self._definitions.keys()) + ['aqua_classes', 'input_filename', 'output_filename']),
			"",
			"from collections import OrderedDict",
			"from decimal import Decimal",
			"from classfactory import AquaBase",
			sep,
			'class AssignmentError(Exception):',
			'	"""An error from assigning a wrong type or value to a field."""',
			'',
			'	def __init__(self, fieldname, message):',
			'		self.fieldname, self.msg = fieldname, message',
			'',
			'	def __str__(self):',
			'		return "field {0}: {1}".format(self.fieldname, self.msg)'
		]

		with open(self._out_file, 'w') as outfile:
			outfile.write('{code}\n'.format(code="\n".join(imports)))

			for k in self._definitions.keys():
				outfile.write('{sep}\n{code}\n'.format(code="\n".join(self._definitions[k]), sep=sep))
			outfile.write(sep)

			outfile.write('\n\naqua_classes = dict(' + ", ".join(['{key}={key}'.format(key=k) for k in self._definitions.keys()]) + ')')

			outfile.write('\n\ninput_filename = "' + self._input_filename + '"')
			outfile.write('\noutput_filename = "' + self._output_filename + '"')

			outfile.write(sep + '\n')

	def get_classes(self):
		classdefs = ClassDefinitionReader(self._classdefs_file).parse()
		for k in classdefs.keys():
			factory = ClassFactory(k, classdefs[k])
			self._definitions[k] = factory.class_definition
			self._classes[k] = factory.get_class

		return self._classes

	def update(self):
		if not self._classes:
			self.get_classes()
		self._write_class_module()
		logging.info('{0} recreated'.format(self._out_file))


#=##################################################################################################
#=##################################################################################################

if __name__ == '__main__':
	classdefs_filename	= sys.argv[1]
	input_filename		= sys.argv[2]
	output_filename		= sys.argv[3]

	##### Serve solo per debug quando si lancia da linea di comado #####
	log_filename = sys.argv[4]
	logging.basicConfig(filename=log_filename, format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG)
	####################################################################

	ClassModuleUpdater(classdefs_filename, input_filename, output_filename).update()
