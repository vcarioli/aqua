# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:		inputreader
#-------------------------------------------------------------------------------
from os.path import dirname
from datetime import datetime
from decimal import Decimal
import sys
import logging


__all__ = ["InputReader"]


#=##################################################################################################
class InputReader():
	def __init__(self, aqua_classes, file_name=None):
		if file_name is None:
			file_name = dirname(sys.argv[0]) + '\\' + 'input.txt'
		self._file_name = file_name
		self._aqua_classes = aqua_classes

	def _convert(self, field, typ, value):
		if typ == 's':
			return value
		elif typ == 'i':
			return int(value)
		elif typ == 'd':
			return Decimal(value.replace(',', '.'))
		elif typ == 'dt':
			return None if int(value) == 0 else datetime.strptime(value, '%Y%m%d').date()

	def read(self):
		lines = []
		with open(self._file_name, 'r') as fin:
			lines = map(lambda x: x.strip('\n'), fin.readlines())
		lineslist = list(map(lambda x: x.split('\t'), lines))

		for i in range(len(lineslist)):
			lineslist[i] = list(map(lambda x: x.strip(), lineslist[i]))

		data = {}
		for line in lineslist:
			logging.info('Reading line {0}'.format(str(line)))
			key = line[0]
			values = line[1:]

			c = self._aqua_classes[key]()
			for fld, val in zip(c.fields.keys(), values):
				setattr(c, fld, self._convert(fld, c.fields[fld]['field_type'], val))

			if key not in data:
				data[key] = []
			data[key] += [c]
		return data
