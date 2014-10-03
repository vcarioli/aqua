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

AQUA_CLASSES = "aquaclasses.py"

from sys import exit, version_info as pyver
from runpy import run_path
from os.path import abspath, dirname, exists, getmtime, basename, join
from aquaerrors import NoFileError
from logger import Logger


#=##############################################################################
def get_command_line_options():
	from optparse import OptionParser, make_option

	return OptionParser(
		option_list=[
			make_option("-m", "--main", dest="main_program_filename", metavar="FILE", help="name of the main Python program"),
			make_option("-c", "--classdefs", dest="classdefs_filename", metavar="FILE", help="class definition data FILE"),
			make_option("-i", "--input", dest="input_filename", metavar="FILE", help="read data from FILE"),
			make_option("-o", "--output", dest="output_filename", metavar="FILE", help="write data to FILE"),
			make_option("-l", "--logfile", dest="log_filename", metavar="FILE", help="write data to FILE")
		]
	).parse_args()

#=##############################################################################


base_path = dirname(__file__)
(options, args) = get_command_line_options()
log_filename = abspath(join(base_path, 'aqua.log') if options.log_filename is None else options.log_filename)

logger = Logger(log_filename=log_filename, filename=__file__, prefix='---  ', debug_mode=False)
logger.config()


#=##############################################################################
def start_logging():
	logger.center_info('Begin Session [Python v{v0}.{v1}.{v2}]'.format(v0=pyver[0], v1=pyver[1], v2=pyver[2]))


#=##############################################################################
def stop_logging(ret_code):
	logger.center_info('End Session (Exit Code: %d)' % ret_code)


#=##############################################################################
def check_command_line_options(opts):
	if not exists(abspath(opts.main_program_filename)):
		raise NoFileError(opts.main_program_filename)
	if not exists(abspath(opts.classdefs_filename)):
		raise NoFileError(opts.classdefs_filename)
	if not exists(abspath(opts.input_filename)):
		raise NoFileError(opts.input_filename)

	try:
		outf = open(abspath(opts.output_filename), 'w')
		outf.close()

	except IOError:
		raise NoFileError(opts.output_filename, "can't open for output")


#=##############################################################################
def main():
	main_program_filename	= abspath(options.main_program_filename)
	classdefs_filename		= abspath(options.classdefs_filename)
	input_filename			= abspath(options.input_filename)
	output_filename			= abspath(options.output_filename)

	logger.info('Working directory:      [%s]' % base_path)
	logger.info('Log file name:          [%s]', basename(log_filename))
	logger.info('Input file name:        [%s]', basename(input_filename))
	logger.info('Output file name:       [%s]', basename(output_filename))
	logger.info('Class definitions file: [%s]', basename(classdefs_filename))

	aquaclasses_py = join(base_path, AQUA_CLASSES)
	if not exists(aquaclasses_py) or getmtime(aquaclasses_py) < getmtime(classdefs_filename):
		from classmoduleupdater import ClassModuleUpdater
		ClassModuleUpdater(classdefs_filename, input_filename, output_filename, log_filename).update()
		logger.info('Recreated class file:   [%s]', AQUA_CLASSES)

	logger.center_info()

	logger.debug('%s: Starting', basename(main_program_filename))
	run_path(main_program_filename, run_name='__main__')
	logger.debug('%s: Done', basename(main_program_filename))


#=##############################################################################
if __name__ == '__main__':
	start_logging()

	exit_code = 0
	try:
		check_command_line_options(options)
		main()
	except Exception as ex:
		logger.exception(ex)
		exit_code = 1

	stop_logging(exit_code)
	exit(exit_code)
