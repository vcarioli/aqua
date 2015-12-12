# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
##----------------------------------------------------------------------------------------------------------------------
##	Name:		generico
##----------------------------------------------------------------------------------------------------------------------

from os.path import basename
from decimal import Decimal
from collections import OrderedDict
from datetime import timedelta

from aquaerrors import DataMissingError, CostCodeMissingError, InvalidDataError
from inputreader import InputReader
from logger import Logger

from aquaclasses import *

##======================================================================================================================

logger = Logger(filename=__file__, log_filename=log_filename, prefix='---  ', debug_mode=False)
logger.config()

fpro = None		# Dati di fatturazione dell'azienda
fprol = []		# letture
fproc = []		# costi
fprot = []		# tariffe
fpros = []		# scaglioni

results = []
tipo_lettura = ''

##======================================================================================================================

def write_output(res):
	"""
	Scrive i risultati nel file di output
	:param res: <[Output()]>
	:return; <None>
	"""
	with open(output_filename, "w") as fout:
		fout.writelines([str(o) + '\n' for o in res])


def output_line(numfat, cs, codart, qta, costo):
	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = cs
	o.fpo_bcodart = codart
	o.fpo_costo = costo
	o.fpo_qta = qta
	return o


def scaglione(tar, mc):
	"""
	Scaglione Acqua
	:param tar: Fatprot() - Tariffa
	:param mc: int - metri cubi
	:return: Decimal()
	"""
	assert isinstance(tar, Fatprot)
	assert isinstance(mc, (int, Decimal))

	return Decimal(round(tar.fpt_quota * mc / 1000) if tar.fpt_quota < 99999 else 99999)


def costo(tar, qta, numfat):
	"""
	Prepara un record di Output() di costi
	:param tar: <Fatprot()> - Tariffa applicata
	:param numfat: <int> - Numero fattura (per l'ordinamento delle righe di output)
	:param qta: <Dec(5.3> - Quantità
	:return: Output()
	"""
	assert isinstance(tar, Fatprot)
	assert isinstance(numfat, int)
	assert isinstance(qta, (Decimal, int))

	codart = tar.fpt_bcodart_s if tipo_lettura == 'S' else tar.fpt_bcodart_r
	return output_line(numfat, 'C', codart, qta, tar.fpt_costo_tot)


def costo_acqua_calda(qta, numfat):
	"""
	Calcola il costo dell'acqua calda
	:param qta: <int> - Quantità consumata
	:param numfat: <int> - Numero fattura (per l'ordinamento delle righe di output)
	:return: <Output()>
	"""
	assert isinstance(qta, (int, Decimal))
	assert isinstance(numfat, int)

	costo, codart = None, None
	try:
		ac = [x for x in fproc if x.fpc_bcodart == 'AC'][0]
		costo = ac.fpc_costo
		if tipo_lettura == 'S':
			codart = [x for x in fproc if x.fpc_bcodart == 'ACS'][0].fpc_bcodart
		else:
			codart = ac.fpc_bcodart
	except:		# fixme:	Verificare il comportamento in caso di mancanza dei valori per costo e codart
		raise DataMissingError('', "Nei costi mancano i codici 'AC' e/o 'ACS'")

	return output_line(numfat, 'C', codart, qta, costo)


def get_numfat(bcodart):
	"""
	Decodifica il numero di fattura dal codice articolo
	:param bcodart: <string> - Codice articolo
	:return: <int> - Numero fattura di partenza (per l'ordinamento delle righe di output) <int>
	"""
	assert isinstance(bcodart, str)

	numfat = {'MC': 10000, 'QAC': 1000, 'CS': 99999}
	return numfat[bcodart]


def altri_costi():
	"""
	Produce una lista di costi aggiuntivi

	:return: <[Output()]>
	"""

	res = []
	if fproc is not None:
		costi = [
			# 'BA',		# Bocche Antincendio
			# 'SDB',	# Spese domiciliazione bolletta
			'CS',		# Competenze servizio
			'MC',		# Manutenzione contatori
			'QAC',		# Quota Fissa acqua calda
		]
		for c in fproc:
			codart = c.fpc_bcodart
			if codart in costi:
				res.append(output_line(get_numfat(codart), 'C', codart, 1, c.fpc_costo))

	if len(res) == 0:
		logger.prefix_warn("Non ci sono costi da fatturare")

	return res


def consumo_mc(letture):
	"""
	Consumo in metri cubi
	:param letture: <[Fatprol()]> - Lista letture
	:return : <Decimal()> - Consumo (mc)
	"""
	if letture:
		assert isinstance(letture[0], Fatprol)

	return Decimal(sum([x.fpl_consumo for x in letture]))


def calcolo_storno(st, numfat):
	"""
	Calcolo dello st
	:param st: <Fatpros()> - Storno
	:param numfat: <int> - Numero fattura (per l'ordinamento delle righe di output)
	:return: <Output()> Risultato
	"""
	assert isinstance(st, Fatpros)
	assert isinstance(numfat, int)

	codart = 'S' + st.fps_bcodart[0:len(st.fps_bcodart) - 1]
	return output_line(numfat, 'S', codart, -st.fps_qta, st.fps_costo)


def compatta_storni(storni):
	"""
	Compattazione e ordinamento degli storni
	:param storni: <[Fatpros()]> - Lista degli storni
	:return: <[Fatpros()]> - Lista degli storni compattati e ordinati secondo il campo fps_bgiorni
	"""
	if storni:
		assert isinstance(storni[0], Fatpros)

	s = {}
	for fps in storni:
		k = (fps.fps_bcodart, fps.fps_costo, fps.fps_bgiorni)
		s[k] = fps.fps_qta if k not in s else s[k] + fps.fps_qta

	storni = []
	for k in s.keys():
		fps = Fatpros()
		fps.fps_bcodart = k[0]
		fps.fps_costo = k[1]
		fps.fps_bgiorni = k[2]
		fps.fps_qta = s[k]
		storni.append(fps)

	return sorted(storni, key=lambda x: x.fps_bgiorni)


def calcolo_tariffe(start_date, end_date, tar):
	x = []
	for t in tar:
		if t.fpt_vigore <= end_date:
			k = ((t.fpt_vigore, t.fpt_codtar), max(t.fpt_vigore, start_date))
			if k not in x:
				x.append(k)
	x.sort()

	cons = OrderedDict()
	lx = len(x) - 1
	for i in range(lx):
		cons[x[i][0]] = (x[i + 1][1] - x[i][1]).days
	if lx >= 0:
		cons[x[lx][0]] = (end_date - x[lx][1]).days

	return cons


def giorni_tariffe():
	end_date = fpro.fp_data_let
	start_date = end_date - timedelta(days=fpro.fp_periodo)

	cons = {}

	# acqua
	for k, v in calcolo_tariffe(start_date, end_date, [x for x in fprot if x.fpt_codtar[0] == 'A']).items():
		cons[k] = v

	# depuratore
	for k, v in calcolo_tariffe(start_date, end_date, [x for x in fprot if x.fpt_codtar == 'DEPUR']).items():
		cons[k] = v

	# fogna
	for k, v in calcolo_tariffe(start_date, end_date, [x for x in fprot if x.fpt_codtar == 'FOGNA']).items():
		cons[k] = v

	# quota fissa
	for k, v in calcolo_tariffe(start_date, end_date, [x for x in fprot if x.fpt_codtar[0] == 'Q']).items():
		cons[k] = v

	return OrderedDict(sorted(cons.items(), key=lambda i: (i[0][0], i[0][1])))

##======================================================================================================================

def main():
	global results

	##	Isolamento letture casa da letture garage
	letture_casa	= [x for x in fprol if x.fpl_garage == '']
	letture_garage	= [x for x in fprol if x.fpl_garage == 'G']

	##	Consumi casa
	mc_consumo_fredda_casa		= consumo_mc([x for x in letture_casa if x.fpl_fc == 0])
	mc_consumo_calda_casa		= consumo_mc([x for x in letture_casa if x.fpl_fc == 1])

	##	Consumi garage
	mc_consumo_fredda_garage	= consumo_mc([x for x in letture_garage if x.fpl_fc == 0])
	mc_consumo_calda_garage		= consumo_mc([x for x in letture_garage if x.fpl_fc == 1])

	##---------------------------------------------------------------------------------------------
	##	Consumi totali
	##---------------------------------------------------------------------------------------------
	mc_consumo_totale_garage	= mc_consumo_fredda_garage + mc_consumo_calda_garage
	mc_consumo_totale_casa		= mc_consumo_fredda_casa + mc_consumo_calda_casa

	mc_consumo_totale_calda		= mc_consumo_calda_casa	+ mc_consumo_calda_garage
	mc_consumo_totale_fredda	= mc_consumo_fredda_casa + mc_consumo_fredda_garage

	mc_consumo_totale			= mc_consumo_totale_casa + mc_consumo_totale_garage
	##---------------------------------------------------------------------------------------------

	numfat = 0

	##	Consumi
	gt = giorni_tariffe()
	if len(gt.items()) == 0:
		ed = fpro.fp_data_let
		sd = ed - timedelta(days=fpro.fp_periodo)
		raise InvalidDataError('', 'Nessuna tariffa applicabile al periodo specificato [{sd} - {ed}].'.format(sd=sd, ed=ed))

	for k in gt.keys():
		ts = [x for x in fprot if x.fpt_vigore == k[0] and x.fpt_codtar == k[1]]
		consumo = Decimal(round(mc_consumo_totale / fpro.fp_periodo * gt[k]))

		for tar in ts:
			if tar.fpt_codtar[0] == 'A':
				if consumo > 0:
					sc = scaglione(tar, gt[k])
					qty = sc if consumo > sc else consumo
					results.append(costo(tar, qty, numfat))
					consumo -= qty
					numfat += 1
			else:
				qty = consumo if tar.fpt_costo_um == 'MC' else gt[k]
				results.append(costo(tar, qty, numfat))
				numfat += 1

	##	Acqua calda, se presente
	if mc_consumo_totale_calda > 0:
		if not fproc:
			msg = "Consumo acqua calda > 0 (mc %d) ma non sono presenti i relativi costi" % mc_consumo_totale_calda
			raise DataMissingError("Fatproc", msg)
		results.append(costo_acqua_calda(mc_consumo_totale_calda, numfat))

	##	Costi
	results += altri_costi()

	##	Storni
	if fpros:
		numfat = 50000
		for fps in compatta_storni(fpros):
			o = calcolo_storno(fps, numfat)
			results.append(o)
			numfat += 1

	##	Scrittura dei risultati
	write_output(results)

	logger.debug('main(): Results written to %s', basename(output_filename))

##======================================================================================================================
##	Inizializzazione e verifica della presenza e congruità dei dati
##======================================================================================================================

def initialize():
	"""
	Lettura dei dati dal file di input e inizializzazione delle variabili globali
	:return: None
	"""
	global aqua_data, fpro, tipo_lettura, fprol, fproc, fprot, fpros, logger

	try:
		# Lettura file dei dati in input
		logger.debug('InputReader().read(): Starting')
		aqua_data = InputReader(aqua_classes, input_filename.replace('\\', '/')).read()
		logger.debug('InputReader().read(): Done')

		# Controllo presenza dei dati dell'azienda
		if 'Fatpro' not in aqua_data:
			raise DataMissingError('', "Mancano i dati dell'azienda.")

		fpro = aqua_data['Fatpro'][0]
		tipo_lettura = fpro.fp_tipo_let

		logger.prefix_info("Utente:\t[%d/%s]", fpro.fp_aconto, fpro.fp_azienda)
		logger.prefix_info("Lettura:\t[%s/%d/%d %s]", tipo_lettura, fpro.fp_numlet_pr, fpro.fp_numlet_aa, fpro.fp_data_let)

		if fpro.fp_periodo <= 0:
			raise InvalidDataError('', 'Il periodo non può essere di 0 giorni.')

		# Controllo della presenza delle letture
		if 'Fatprol' not in aqua_data:
			raise DataMissingError('', "Mancano le letture.")

		fprol = aqua_data['Fatprol'] if 'Fatprol' in aqua_data else None

		# Controllo della presenza delle tariffe
		if 'Fatprot' not in aqua_data:
			raise DataMissingError('', "Mancano le tariffe.")

		fprot = sorted(aqua_data['Fatprot'], key=lambda t: (t.fpt_vigore, t.fpt_codtar, t.fpt_colonna))

		# Controllo della presenza dei costi
		if 'Fatproc' not in aqua_data:
			raise DataMissingError("", "Mancano i costi.")

		fproc = aqua_data['Fatproc']
		# Il codice 'CS' deve essere presente
		if len([c for c in fproc if c.fpc_bcodart == 'CS']) == 0:
			raise CostCodeMissingError("", "Mancano le Competenze di Servizio (cod. CS).")

		# Controllo della presenza degli storni
		if 'Fatpros' not in aqua_data:
			logger.prefix_warn("Non sono stati specificati storni.")
		else:
			fpros = aqua_data['Fatpros']

	except:
		logger.error("Errore durante l'inizializzazione!")
		raise

##======================================================================================================================
##	Stampe di debug
##======================================================================================================================

def csv_print_results():
	print(results[0].get_csv_hdr())
	print('\n'.join([i.get_csv_row() for i in results]))

def csv_print_data():
	for k in aqua_data.keys():
		print()
		print(aqua_data[k][0].get_csv_hdr())
		print('\n'.join([i.get_csv_row() for i in aqua_data[k]]))

def pretty_print_data():
	print()
	for k in aqua_data.keys():
		print('\n\n'.join([i.pretty_print() for i in aqua_data[k]]))

def pretty_print_results():
	print('\n\n'.join([i.pretty_print() for i in results]))

##======================================================================================================================

if __name__ == '__main__':
	try:
		logger.debug('initialize(): Starting ')
		initialize()
		logger.debug('initialize(): Done')

		logger.debug('main(): Starting')
		main()

		## Stampe di debug
		# csv_print_data()
		# csv_print_results()
		# pretty_print_data()
		# pretty_print_results()

		logger.debug('main(): Done')
	except:
		raise

##======================================================================================================================
