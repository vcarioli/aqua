# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:		aqua_launcher
# -------------------------------------------------------------------------------
"""uso:
	python aqua_launcher.py -m main_program.py -i input.txt -o output.txt -c classdefs.txt -l aqualog.log

	Prima di lanciare il "main" contenuto in main_program.py questo launcher esamina i parametri
	della linea di comando, si occupa di rigenerare le classi-dati eventualmente modificate, e di
	caricare i dati in strutture che saranno poi rese visibili a partire dal file main_program.

	Nel file main_program.py saranno visibili le seguenti variabili globali:
		base_path               directory di avvio in cui risiedono gli script del sistema aqua
		main_program_filename   path assoluto di main_program.py
		classdefs_filename		path assoluto di classdefs.txt
		input_filename			path assoluto di input.txt
		output_filename			path assoluto di output.txt
		log_filename			path assoluto di aqualog.log
		aqua_classes			è un dictionary che ha come chiave il nome del file e come valore
								il costruttore della classe: fatpro = aqua_classes['Fatpro']().
								E' utilizzato internamente durante la decodifica dei dati di input.
								In main_program.py e negli altri script è meglio utilizzare il
								costruttore esplicito importando il modulo aquaclasses che viene
								generato automaticamente a partire da classdefs.txt.
								Si potrà così scrivere:
									import aquaclasses
									fatpro = aquaclasses.Fatpro()
								oppure:
									from aquaclasses import *
									fatpro = Fatpro()
								e "vedere" nell'editor i suggerimenti relativi ai campi della classe
		aqua_data				è un dictionary che ha come chiave il nome del file e come valore
								una lista di istanze di classe letti dal file input.txt indicato
								sulla linea di comando
"""

import sys
import logging
import runpy

from os.path import abspath, dirname, exists, getmtime, join as pjoin

from classfactory import ClassModuleUpdater
from inputreader import InputReader


#=##################################################################################################
class AquaClassesGenerationError(Exception):
	"""Error generating the file aquaclasses.py."""

	def __str__(self):
		return 'Error during generation of "aquaclasses.py"'


#=##################################################################################################
class NoFileError(Exception):
	"""An error from referencing a file that does not exists"""

	def __init__(self, filename, message=None):
		self.argname, self.msg = filename, message if message else "does not exist"

	def __str__(self):
		return 'argument {0}: {1}'.format(self.argname, self.msg)


#=##################################################################################################
def get_command_line_options():
	from optparse import OptionParser, make_option

	return OptionParser(
		option_list = [
			make_option("-m", "--main", dest="main_program_filename", metavar="FILE", help="name of the main Python program"),
			make_option("-c", "--classdefs", dest="classdefs_filename", metavar="FILE", help="class definition data FILE"),
			make_option("-i", "--input", dest="input_filename", metavar="FILE", help="read data from FILE"),
			make_option("-o", "--output", dest="output_filename", metavar="FILE", help="write data to FILE"),
			make_option("-l", "--logfile", dest="log_filename", metavar="FILE", help="write data to FILE")
			]
		).parse_args()

#=##################################################################################################


base_path = dirname(abspath(sys.argv[0]))
(options, args) = get_command_line_options()
log_filename = abspath(pjoin(base_path, 'aqua.log') if options.log_filename is None else options.log_filename)


#=##################################################################################################
def start_logging():
	logging.basicConfig(filename=log_filename, format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG)
	logging.info('--------------------------------------------------------------- begin session')


#=##################################################################################################
def stop_logging(exit_code):
	logging.info('--------------------------------------------------- end session (exit code {0})'.format(exit_code))


#=##################################################################################################
def check_command_line_options(options):
	if not exists(abspath(options.main_program_filename)):
		raise NoFileError(options.main_program_filename)
	if not exists(abspath(options.classdefs_filename)):
		raise NoFileError(options.classdefs_filename)
	if not exists(abspath(options.input_filename)):
		raise NoFileError(options.input_filename)

	try:
		outf = open(abspath(options.output_filename), 'w')
		outf.close()

	except IOError:
		raise NoFileError(options.output_filename, "can't open for output")


#=##################################################################################################
def main():
	main_program_filename	= abspath(options.main_program_filename)
	classdefs_filename		= abspath(options.classdefs_filename)
	input_filename			= abspath(options.input_filename)
	output_filename			= abspath(options.output_filename)

	aquaclasses_py = pjoin(base_path, 'aquaclasses.py')
	if not exists(aquaclasses_py) or getmtime(aquaclasses_py) < getmtime(classdefs_filename):
		from subprocess import check_call

		args = [
			sys.executable,
			pjoin(base_path, 'classfactory.py'),
			classdefs_filename,
			input_filename,
			output_filename,
			log_filename
		]
		check_call(args, shell=False)

	logging.info('Executing %s', main_program_filename)
	runpy.run_path(main_program_filename, run_name='__main__')


#=##################################################################################################
if __name__ == '__main__':
	start_logging()

	exit_code = 0
	try:
		check_command_line_options(options)
		main()
	except Exception as ex:
		logging.exception(ex)
		exit_code = 1

	stop_logging(exit_code)
	sys.exit(exit_code)
