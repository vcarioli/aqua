# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:		aquabase
#-------------------------------------------------------------------------------

from collections import OrderedDict
from datetime import datetime, date
from decimal import Decimal

from aquaerrors import AssignmentError, UnknownFieldTypeError
from logger import Logger


logger = Logger(filename=__file__)


#=##############################################################################
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
				logger.error("__create_fields_dict__(self): error decoding [{0}][{1}]".format(self.__spec__[0], fld))
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

		return sep.join(
			[fmts[self.__fields__[k]['field_type']].format(eval('self.' + k)) for k in self.__fields__.keys()])