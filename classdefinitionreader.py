# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
##----------------------------------------------------------------------------------------------------------------------
##	Name:		classdefinitionreader
##----------------------------------------------------------------------------------------------------------------------

__all__ = ["ClassDefinitionReader"]

##======================================================================================================================

class ClassDefinitionReader():
	def __init__(self, file_name):
		self._file_name = file_name

	def __read(self):
		with open(self._file_name, 'r') as fin:
			lines = map(lambda x: x.strip('\n'), fin.readlines())

		return list(filter(lambda x: not (x.startswith('#') or x.strip() == ''), lines))

	def parse(self):
		lines = self.__read()

		classdefs = {}
		for line in [x.split('\t') for x in lines]:
			if line[0] not in classdefs:
				classdefs[line[0]] = []
#			print(line)
			classdefs[line[0]] += [line[1]]
		return classdefs
