# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:		inputreader
#-------------------------------------------------------------------------------

__all__ = ["InputReader"]

from os.path import dirname, join
from datetime import datetime
from decimal import Decimal
from logger import Logger

logger = Logger(filename=__file__, prefix='---  ', info_level=0)


#=##############################################################################
class InputReader():
	def __init__(self, aqua_classes, file_name=None):
		if file_name is None:
			file_name = join(dirname(__file__), 'input.txt')
		self._file_name = file_name
		self._aqua_classes = aqua_classes

	@staticmethod
	def _convert(typ, value):
		if typ == 's':
			return value
		elif typ == 'i':
			return int(value)
		elif typ == 'd':
			return Decimal(value.replace(',', '.'))
		elif typ == 'dt':
			return None if int(value) == 0 else datetime.strptime(value, '%Y%m%d').date()

	def read(self):
		with open(self._file_name, 'r') as fin:
			lines = map(lambda x: x.strip('\n'), fin.readlines())
		lineslist = list(map(lambda x: x.split('\t'), lines))

		for i in range(len(lineslist)):
			lineslist[i] = list(map(lambda x: x.strip(), lineslist[i]))

		data = {}
		for line in lineslist:
			logger.prefix_info(str(line))

			if line == [''] or line[0].startswith('#'):
				continue
			key = line[0]
			values = line[1:]

			c = self._aqua_classes[key]()
			for fld, val in zip(c.fields.keys(), values):
				setattr(c, fld, self._convert(c.fields[fld]['field_type'], val))

			if key not in data:
				data[key] = []
			data[key] += [c]
		return data
