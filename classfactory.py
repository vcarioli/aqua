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
		self.__spec__ = [classname] + spec
		self.__fields__ = self.__create_fields_dict__()

	def __create_fields_dict__(self):
		funcs = {
				'i': ["__set_int__", "__chk_int__", "__get_int__", "__out_int__"],
				's': ["__set_str__", "__chk_str__", "__get_str__", "__get_str__"],
				'dt': ["__set_date__", "__chk_date", "__get_date__", "__get_date__"],
				'd': ["__set_dec__", "__chk_dec__", "__get_dec__", "__out_dec__"]
		}
		fields = OrderedDict()
		for fld in [x.strip('\r') for x in self.__spec__[1:]]:
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
				logging.error("classfactory.py: __create_fields_dict__(self): error decoding [{0}][{1}]".format(self.__spec__[0], fld))
				raise
		return fields

	# __set_int__(), __chk_int__(), __get_int__(), __out_int__()
	def __set_int__(self, field_name, value):
		value = str(value)
		self.__chk_int__(field_name, value)
		setattr(self, '__' + field_name + '__', int(value))

	def __chk_int__(self, field_name, value):
		d = self.__fields__[field_name]
		field_len, dec_len = d['field_len'], d['dec_len']
		if dec_len != 0:
			raise AssignmentError(field_name, 'int __fields__ can not have decimals')
		if len(str(value).strip('-+')) > field_len:
			raise OverflowError(
				'{0} max length is {1}: trying to assign value [{2}]'.format(field_name, field_len, value)
			)

	def __get_int__(self, field_name, sign='+'):
		d = self.__fields__[field_name]
		field_len = d['field_len']
		return '{:0={s}{w}n}'.format(getattr(self, field_name), s=sign, w=(field_len + len(sign)))

	def __out_int__(self, field_name):
		return self.__get_int__(field_name, sign='')

	# __set_dec__(), __chk_dec__(), __get_dec__(), __out_dec__()
	def __set_dec__(self, field_name, value):
		v = str(value).replace(',', '.').split('.')
		if len(v) > 1:
			dec_len = self.__fields__[field_name]['dec_len']
			v[1] = v[1][:dec_len]
			value = Decimal('.'.join(v))
		self.__chk_dec__(field_name, value)
		setattr(self, '__' + field_name + '__', Decimal(value))

	def __chk_dec__(self, field_name, value):
		d = self.__fields__[field_name]
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

	def __get_dec__(self, field_name, dec_sep='', sign='+'):
		d = self.__fields__[field_name]
		field_len, dec_len = d['field_len'], d['dec_len']
		return '{:0={s}{w}.{p}f}'.format(float(getattr(self, field_name)), s=sign, w=field_len + dec_len + 1 + len(sign), p=dec_len).replace('.', dec_sep)

	def __out_dec__(self, field_name):
		return self.__get_dec__(field_name, dec_sep=',', sign='')

	# __set_date__(), __chk_date__(), __get_date__()
	def __set_date__(self, field_name, value):
		if type(value) is str:
			value = None if value.rstrip(' ') == '' or value.rstrip('0') == '' else datetime.strptime(value, '%Y%m%d').date()
		elif type(value) is datetime:
			value = value.date()
		self.__chk_date__(field_name, value)
		setattr(self, '__' + field_name + '__', value)

	@staticmethod
	def __chk_date__(field_name, value):
		if type(value) not in [type(None), date]:
			raise AssignmentError(field_name, 'trying to assign value [{0}] of type {1} to a date field'.format(value, type(value)))

	def __get_date__(self, field_name):
		dt = getattr(self, field_name)
		return dt.strftime('%Y%m%d') if dt is not None else '        '

	# __set_str__(), __chk_str__(), __get_str__()
	def __set_str__(self, field_name, value):
		value = value.rstrip()
		self.__chk_str__(field_name, value)
		setattr(self, '__' + field_name + '__', value)

	def __chk_str__(self, field_name, value):
		d = self.__fields__[field_name]
		field_len, dec_len = d['field_len'], d['dec_len']
		if dec_len != 0:
			raise AssignmentError(field_name, 'string __fields__ can not have decimals')
		if len(str(value)) > field_len:
			raise OverflowError('{0} max length is {1}: trying to assign value [{2}]'.format(field_name, field_len, value))

	def __get_str__(self, field_name):
		field_len = self.__fields__[field_name]['field_len']
		return '{: <{w}.{w}s}'.format(getattr(self, field_name), w=field_len)

	def get_input_line(self):
		return '{: <8.8s}\t'.format(self.__class__.__name__) + '\t'.join([eval('self.' + self.__fields__[k]['out'] + '(k)') for k in self.__fields__.keys()])

	def pretty_print(self, prefix=''):
		fmts = {'i': '{val}', 'd': '{val}', 's': '"{val}"', 'dt': '"{val}"'}
		s = prefix + ('# ' if prefix == '' else ' = ') + self.__class__.__name__ + '()'
		prefix += '' if prefix == '' else '.'
		for k in self.__fields__.keys():
			funcs = {
				'i': 'self.' + k,
				'd': 'self.' + k,
				's': 'self.' + self.__fields__[k]['out'] + '(k)',
				'dt': 'self.' + self.__fields__[k]['out'] + '(k)'
			}
			t = self.__fields__[k]['field_type']
			s += ('\n{pfx}{name} = ' + fmts[t]).format(name=k, pfx=prefix, val=eval(funcs[t]))
		return s

	def get_csv_hdr(self, sep='\t'):
		"""
		Ritorna una riga con i nomi dei campi
		:param sep: Separatore da utilizzare (default = tab)
		:return: string
		"""
		return sep.join(self.__fields__.keys())

	def get_csv_row(self, sep='\t', delim='"'):
		"""
		Ritorna una riga con i valori dei campi
		:param sep:		Carattere da utilizzare per separare i campi (default tab)
		:param delim:	Caratteri da utilizzare per delimitare date e stringhe (default '"')
						Se si specifica una stringa vuota ('') non sarà utilizzato il delimitatore
						Se si specificano due (o più) caratteri, il primo sarà utilizzato per
						il delimitatore di sinistra e il secondo per quello di destra (quelli dopo
						il secondo saranno ignorati)
		:return: string
		"""
		ldelim = delim[0] if len(delim) > 0 else delim
		rdelim = delim[1] if len(delim) > 1 else ldelim
		fmts = dict(i='{0}', d='{0}', s=ldelim + '{0}' + rdelim, dt=ldelim + '{0}' + rdelim)

		return sep.join([fmts[self.__fields__[k]['field_type']].format(eval('self.' + k)) for k in self.__fields__.keys()])


#=##################################################################################################
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
