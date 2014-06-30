# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:		sample_data
#-------------------------------------------------------------------------------

#=##############################################################################
from aquaclasses import *
from inputreader import InputReader
#=##############################################################################


#=##############################################################################
def main():
	sep = "##################################################################################\n"

	aqua_data = InputReader(aqua_classes, input_filename).read()

	fpro = aqua_data['Fatpro'][0]

	fprol = aqua_data['Fatprol']
	fproc = aqua_data['Fatproc']
	fprot = aqua_data['Fatprot']
	fpros = aqua_data['Fatpros'] if 'Fatpros' in aqua_data else None

	print(sep)

	print(fpro.get_input_line())
	print()
	if fproc:
		print('\n'.join([i.get_input_line() for i in fproc]))
		print()
	if fpros:
		print('\n'.join([i.get_input_line() for i in fpros]))
		print()
	if fprol:
		print('\n'.join([i.get_input_line() for i in fprol]))
		print()
	if fprot:
		print('\n'.join([i.get_input_line() for i in fprot]))
		print()

	print(sep)
	print(sep)

	print(fpro.pretty_print('fpr'))
	print('\n' + sep)
	if fproc:
		print('\n\n'.join([i.pretty_print('fpc') for i in fproc]))
		print('\n' + sep)
	if fpros:
		print('\n\n'.join([i.pretty_print('fps') for i in fpros]))
		print('\n' + sep)
	if fprol:
		print('\n\n'.join([i.pretty_print('fpl') for i in fprol]))
		print('\n' + sep)
	if fprot:
		print('\n\n'.join([i.pretty_print('fpt') for i in fprot]))
		print('\n' + sep)

	print(sep)

	print(fpro.get_csv_hdr())
	print(fpro.get_csv_row())
	print()

	if fproc:
		print(fproc[0].get_csv_hdr())
		print('\n'.join([i.get_csv_row() for i in fproc]))
		print()
	if fpros:
		print(fpros[0].get_csv_hdr())
		print('\n'.join([i.get_csv_row() for i in fpros]))
		print()
	if fprol:
		print(fprol[0].get_csv_hdr())
		print('\n'.join([i.get_csv_row() for i in fprol]))
		print()
	if fprot:
		print(fprot[0].get_csv_hdr())
		print('\n'.join([i.get_csv_row() for i in fprot]))
		print()

	print(sep)

#=##############################################################################
if __name__ == '__main__':
	main()
