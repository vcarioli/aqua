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
		self._classdefs_file = join(dirname(argv[0]), 'classdefs.txt') if classdefs_fn is None else classdefs_fn
		self._out_file = join(dirname(self._classdefs_file), 'aquaclasses.py')
		self._input_filename = input_fn
		self._output_filename = output_fn
		self._classes = {}
		self._definitions = {}

	def _write_class_module(self):
		sep = '\n\n#=##############################################################################'
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
			"from aquabase import AquaBase"
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
