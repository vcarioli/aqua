# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
##----------------------------------------------------------------------------------------------------------------------
##	Name:		classmoduleupdater
##----------------------------------------------------------------------------------------------------------------------

from os.path import join, dirname
from sys import argv

from classdefinitionreader import ClassDefinitionReader
from classfactory import ClassFactory
from logger import Logger

__all__ = ["ClassModuleUpdater"]


##======================================================================================================================


class ClassModuleUpdater:
	def __init__(self, classdefs_fn):
		self.__classdefs_file = join(dirname(argv[0]), 'classdefs.txt') if classdefs_fn is None else classdefs_fn
		self.__out_file = join(dirname(self.__classdefs_file), 'aquaclasses.py')
		self.__classes = {}
		self.__definitions = {}

	def __write_class_module(self):
		sep = '\n\n#=##############################################################################'
		imports = [
			"# -*- Mode: Python; tab-width: 4 -*-",
			"# -*- coding: utf-8 -*-",
			"#-------------------------------------------------------------------------------",
			"# Name:		aquaclasses",
			"#-------------------------------------------------------------------------------",
			"",
			"from collections import OrderedDict",
			"from decimal import Decimal",
			"from aquabase import AquaBase",
			"__all__ = " + str(list(self.__definitions.keys()) + ['aqua_classes'])
		]

		with open(self.__out_file, 'w') as outfile:
			outfile.write('{code}\n'.format(code="\n".join(imports)))

			for k in self.__definitions.keys():
				outfile.write('{sep}\n{code}\n'.format(code="\n".join(self.__definitions[k]), sep=sep))
			outfile.write(sep)

			outfile.write('\n\naqua_classes = dict(' + ", ".join(['{key}={key}'.format(key=k) for k in self.__definitions.keys()]) + ')')

			outfile.write(sep + '\n')

	def __get_classes(self):
		classdefs = ClassDefinitionReader(self.__classdefs_file).parse()
		for k in classdefs.keys():
			factory = ClassFactory(k, classdefs[k])
			self.__definitions[k] = factory.class_definition
			self.__classes[k] = factory.get_class

		return self.__classes

	def update(self):
		if not self.__classes:
			self.__get_classes()
		self.__write_class_module()


##======================================================================================================================

logger = Logger(__file__)

if __name__ == '__main__':
	classdefs_filename	= argv[1]
	log_filename		= argv[2]

	##### Serve solo per debug quando si lancia da linea di comado #####
	logger.config(log_filename=log_filename)
	####################################################################

	ClassModuleUpdater(classdefs_filename).update()
