# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:		classmoduleupdater
#-------------------------------------------------------------------------------

from os.path import join, dirname
from classdefinitionreader import ClassDefinitionReader
from classfactory import ClassFactory

__all__ = ["ClassModuleUpdater"]


#=##############################################################################
class ClassModuleUpdater():
	def __init__(self, classdefs_fn, input_fn, output_fn):
		self.__classdefs_file = join(dirname(argv[0]), 'classdefs.txt') if classdefs_fn is None else classdefs_fn
		self.__out_file = join(dirname(self.__classdefs_file), 'aquaclasses.py')
		self.__input_filename = input_fn
		self.__output_filename = output_fn
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
			"__all__ = " + str(list(self.__definitions.keys()) + ['aqua_classes', 'input_filename', 'output_filename']),
			"",
			"from collections import OrderedDict",
			"from decimal import Decimal",
			"from aquabase import AquaBase"
		]

		with open(self.__out_file, 'w') as outfile:
			outfile.write('{code}\n'.format(code="\n".join(imports)))

			for k in self.__definitions.keys():
				outfile.write('{sep}\n{code}\n'.format(code="\n".join(self.__definitions[k]), sep=sep))
			outfile.write(sep)

			outfile.write('\n\naqua_classes = dict(' + ", ".join(['{key}={key}'.format(key=k) for k in self.__definitions.keys()]) + ')')

			outfile.write('\n\ninput_filename = "' + self.__input_filename + '"')
			outfile.write('\noutput_filename = "' + self.__output_filename + '"')

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


#=##############################################################################

from sys import argv
from logger import Logger
logger = Logger(__file__)

if __name__ == '__main__':
	classdefs_filename	= argv[1]
	input_filename		= argv[2]
	output_filename		= argv[3]

	##### Serve solo per debug quando si lancia da linea di comado #####
	logger.config(log_filename=argv[4])
	####################################################################

	ClassModuleUpdater(classdefs_filename, input_filename, output_filename).update()
