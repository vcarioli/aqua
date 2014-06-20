__author__ = 'valerio'

# =##################################################################################################
from aquaclasses import *
from inputreader import InputReader
# =##################################################################################################


# =##################################################################################################
def main():
	sep = "##################################################################################\n"

	aqua_data = InputReader(aqua_classes, input_filename).read()

	fpro = aqua_data['Fatpro'][0]
	tipo_lettura = fpro.fp_tipo_let

	fprol = aqua_data['Fatprol']
	fproc = aqua_data['Fatproc']
	fprot = aqua_data['Fatprot']
	fpros = aqua_data['Fatpros'] if 'Fatpros' in aqua_data else None

	print(sep)

	print(fpro.input_line)
	print()
	for i in fproc: print(i.input_line)
	print()
	for i in fpros: print(i.input_line)
	print()
	for i in fprol: print(i.input_line)
	print()
	for i in fprot: print(i.input_line)
	print()

	print(sep)
	print(sep)

	print(fpro.pretty_print('fpr'))
	print('\n' + sep)
	for i in fproc: print(i.pretty_print('fpc')); print()
	print(sep)
	for i in fpros: print(i.pretty_print('fps')); print()
	print(sep)
	for i in fprol: print(i.pretty_print('fpl')); print()
	print(sep)
	for i in fprot: print(i.pretty_print('fpt')); print()
	print(sep)

	print(sep)

	print(fpro.csv_header)
	print(fpro.csv)
	print()
	print(fprot[0].csv_header)
	for i in fproc: print(i.csv)
	print()
	print(fpros[0].csv_header)
	for i in fpros: print(i.csv)
	print()
	print(fprol[0].csv_header)
	for i in fprol: print(i.csv)
	print()
	print(fprot[0].csv_header)
	for i in fprot: print(i.csv)
	print()

	print(sep)

# =##################################################################################################
if __name__ == '__main__':
	main()
