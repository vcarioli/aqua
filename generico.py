# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:		generico
# -------------------------------------------------------------------------------
# Da fare:
#	Logging errori più intelleggibile
#	Cambio tariffa (in sospeso)
#	Gestione del garage
#-------------------------------------------------------------------------------
from collections import OrderedDict
from os.path import basename
from decimal import Decimal
from datetime import *
from math import ceil

from aquaerrors import DataMissingError
from inputreader import InputReader
from logger import Logger
from aquaclasses import Fatprot, input_filename, output_filename, log_filename, Fatprol, Output, Fatpros, aqua_classes

#=##############################################################################

logger = Logger(filename=__file__, log_filename=log_filename, prefix='---  ', debug_mode=False)
logger.config()

fpro = None		# Dati di fatturazione dell'azienda
fprol = []		# letture
fproc = []		# costi
fprot = []		# tariffe
fpros = []		# scaglioni

results = []
tipo_lettura = ''


#=##############################################################################
def write_output(res):
	"""
	Scrive i risultati nel file di output
	:param res: <[Output()]>
	:return; <None>
	"""
	with open(output_filename, "w") as fout:
		fout.writelines([str(o) + '\n' for o in res])


def ricerca_indici():
	"""
	Ricerca indici valori per Quota fissa, Fogna e Depurazione
	:return: <(int, int, int)> - Quota fissa, Fogna, Depurazione
	"""
	ix_quota_fissa, ix_fogna, ix_depuratore = None, None, None
	for i in range(len(fprot)):
		if fprot[i].fpt_codtar[0] == 'Q':
			ix_quota_fissa = i
		elif fprot[i].fpt_codtar == 'FOGNA':
			ix_fogna = i
		elif fprot[i].fpt_codtar == 'DEPUR':
			ix_depuratore = i
	return ix_quota_fissa, ix_fogna, ix_depuratore


def scaglione(tar, mc):
	"""
	Scaglione Acqua
	:param tar: Fatprot() - Tariffa
	:param mc: int - metri cubi
	:return: Decimal()
	"""
	assert isinstance(tar, Fatprot)
	assert isinstance(mc, (int, Decimal))

	return Decimal(ceil(tar.fpt_quota * mc / 1000)) if tar.fpt_quota < 99999 else 99999


def costo(tariffa, numfat, qta):
	"""
	Prepara un record di Output() di costi
	:param tariffa: <Fatprot()> - Tariffa applicata
	:param numfat: <int> - Numero fattura (per l'ordinamento delle righe di output)
	:param qta: <Dec(5.3> - Quantità
	:return: Output()
	"""
	assert isinstance(tariffa, Fatprot)
	assert isinstance(numfat, int)
	assert isinstance(qta, int)

	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'C'
	o.fpo_bcodart = tariffa.fpt_bcodart_s if tipo_lettura == 'S' else tariffa.fpt_bcodart_r
	o.fpo_costo = tariffa.fpt_costo_tot
	o.fpo_qta = qta
	return o


def addebito_acqua(tar, mc, sc, numfat):
	"""
	Prepara un record di Output() di addebiti
	:param tar : <Fatprot()> - Tariffa
	:param mc : <int> - Metri cubi totali
	:param sc : <int> - Scaglione
	:param numfat : <int> - Numero fattura (per l'ordinamento delle righe di output)
	:return : <Output()>
	"""
	assert isinstance(tar, Fatprot)
	assert isinstance(mc, (Decimal, int))
	assert isinstance(sc, (Decimal, int))
	assert isinstance(numfat, int)

	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'C'
	o.fpo_bcodart = tar.fpt_bcodart_s if tipo_lettura == 'S' else tar.fpt_bcodart_r
	o.fpo_costo = tar.fpt_costo_tot
	o.fpo_qta = sc if mc > sc else mc
	return o


def costo_acqua_calda(qta, numfat):
	"""
	Calcola il costo dell'acqua calda
	:param qta: <int> - Quantità consumata
	:param numfat: <int> - Numero fattura (per l'ordinamento delle righe di output)
	:return: <Output()>
	"""
	assert isinstance(qta, int)
	assert isinstance(numfat, int)

	# Ricerca indici valori per Acqua calda (s/r)
	iac, iacs = None, None
	for i in range(len(fproc)):
		if fproc[i].fpc_bcodart == 'AC':
			iac = i
		elif fproc[i].fpc_bcodart == 'ACS':
			iacs = i

	#
	# todo:	Verificare che il comportamento sia corretto in caso di mancanza degli indici
	#
	#	if iac is None or iacs is none:
	#		# E' un errore?
	#		# Cosa fare? (Nulla?)
	#

	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'C'
	o.fpo_bcodart = fproc[iacs if tipo_lettura == 'S' else iac].fpc_bcodart
	o.fpo_costo = fproc[iac].fpc_costo

	o.fpo_qta = qta
	return o


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
		- BA	Bocche Antincendio
		- CS	Competenze servizio
		- MC	Manutenzione contatori
		- QAC	Quota Fissa acqua calda
		- SDB	Spese domiciliazione bolletta

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
			if c.fpc_bcodart in costi:
				o = Output()
				o.fpo_numfat = get_numfat(c.fpc_bcodart)
				o.fpo_cs = 'C'
				o.fpo_bcodart = c.fpc_bcodart
				o.fpo_costo = c.fpc_costo
				o.fpo_qta = 1
				res.append(o)

	if len(res) == 0:
		logger.prefix_warn("Non ci sono costi da fatturare")

	return res


def consumo_mc(letture):
	"""
	Consumo in metri cubi
	:param letture: <[Fatprol()]> - Lista letture
	:return : <int> - Consumo (mc)
	"""
	if letture:
		assert isinstance(letture[0], Fatprol)

	return sum([x.fpl_consumo for x in letture])


def calcolo_storno(storno, numfat):
	"""
	Calcolo dello storno
	:param storno: <Fatpros()> - Storno
	:param numfat: <int> - Numero fattura (per l'ordinamento delle righe di output)
	:return: <Output()> Risultato
	"""
	assert isinstance(storno, Fatpros)
	assert isinstance(numfat, int)

	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'S'
	o.fpo_qta = -storno.fps_qta
	o.fpo_costo = storno.fps_costo
	o.fpo_bcodart = 'S' + storno.fps_bcodart[0:len(storno.fps_bcodart) - 1]
	return o


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


def giorni_tariffe_acqua():
	end_date = fpro.fp_data_let
	start_date = end_date - timedelta(days=fpro.fp_periodo)
	tar_acqua = [x for x in fprot if x.fpt_codtar[0] == 'A']

	x = list()
	for t in tar_acqua:
		if t.fpt_vigore <= end_date:
			k = ((t.fpt_vigore, t.fpt_codtar), max(t.fpt_vigore, start_date))
			if k not in x:
				x.append(k)
	x.sort()
	cons = OrderedDict()
	lx = len(x) - 1
	for i in range(lx):
		cons[x[i][0]] = (x[i + 1][1] - x[i][1]).days
	cons[x[lx][0]] = (end_date - x[lx][1]).days
	return cons


#=##############################################################################
def main():
	global results

	# Isolamento letture casa da letture garage
	letture_casa = [x for x in fprol if x.fpl_garage == '']
	letture_garage = [x for x in fprol if x.fpl_garage == 'G']

	# Consumi casa
	mc_consumo_fredda_casa = consumo_mc([x for x in letture_casa if x.fpl_fc == 0])
	mc_consumo_calda_casa = consumo_mc([x for x in letture_casa if x.fpl_fc == 1])
	mc_consumo_totale_casa = mc_consumo_fredda_casa + mc_consumo_calda_casa

	# Consumi garage
	mc_consumo_fredda_garage = consumo_mc([x for x in letture_garage if x.fpl_fc == 0])
	mc_consumo_calda_garage = consumo_mc([x for x in letture_garage if x.fpl_fc == 1])
	mc_consumo_totale_garage = mc_consumo_fredda_garage + mc_consumo_calda_garage

	mc_consumo_totale = mc_consumo_totale_casa + mc_consumo_totale_garage

	# Calcolo righe addebito acqua totale consumata
	numfat = 0

	gt = giorni_tariffe_acqua()
	for k in gt.keys():
		# ts = tariffe_scaglioni_acqua(gt, k)
		ts = [x for x in fprot if x.fpt_vigore == k[0] and x.fpt_codtar == k[1]]
		consumo = Decimal(ceil(Decimal(mc_consumo_totale) / fpro.fp_periodo * gt[k]))

		for tar in ts:
			if consumo > 0:
				sc = scaglione(tar, gt[k])
				o = addebito_acqua(tar, consumo, sc, numfat)
				results.append(o)
				consumo -= sc if consumo > sc else consumo
				numfat += 1

	ix_qfissa, ix_fogna, ix_depur = ricerca_indici()

	# Fognatura
	if ix_fogna:
		results.append(costo(fprot[ix_fogna], numfat, mc_consumo_totale))
		numfat += 1
	else:
		logger.prefix_warn("Non sono presenti costi fogna [FOGNA]")

	# Depurazione
	if ix_depur:
		results.append(costo(fprot[ix_depur], numfat, mc_consumo_totale))
		numfat += 1
	else:
		logger.prefix_warn("Non sono presenti costi depuratore [DEPUR]")

	# Quota fissa (non e' differenziata per lettura s/r)
	if ix_qfissa:
		results.append(costo(fprot[ix_qfissa], numfat, fpro.fp_periodo))
		numfat += 1
	else:
		logger.prefix_warn("Non sono presenti costi quota fissa [Qxxx]")

	# todo:	Verificare il comportamento in caso di mancanza del costo dell'acqua calda

	# Acqua calda, se presente
	if mc_consumo_calda_casa > 0:
		if not fproc:
			raise DataMissingError(
				"Fatproc",
				"Consumo acqua calda > 0 (mc %d) ma non sono presenti i relativi costi" % mc_consumo_calda_casa
			)
		results.append(costo_acqua_calda(mc_consumo_calda_casa, numfat))

	results += altri_costi()

	if fpros:
		numfat = 50000
		for fps in compatta_storni(fpros):
			o = calcolo_storno(fps, numfat)
			results.append(o)
			numfat += 1

	write_output(results)

	logger.debug('main(): Results written to %s', basename(output_filename))


#=##############################################################################
# Non modificare dopo questa linea
#=##############################################################################


#=##############################################################################
def initialize():
	"""
	Lettura dei dati dal file di input e inizializzazione delle variabili globali
	:return: None
	"""
	global aqua_data, fpro, tipo_lettura, fprol, fproc, fprot, fpros, logger

	try:
		logger.debug('InputReader().read(): Starting')
		aqua_data = InputReader(aqua_classes, input_filename.replace('\\', '/')).read()
		logger.debug('InputReader().read(): Done')

		if not 'Fatpro' in aqua_data:
			raise DataMissingError('Fatpro', "Mancano i dati dell'azienda")
		if not 'Fatprol' in aqua_data:
			raise DataMissingError('Fatprol', "Mancano le letture")
		if not 'Fatprot' in aqua_data:
			raise DataMissingError('Fatprot', "Mancano le tariffe")

		fpro = aqua_data['Fatpro'][0]
		tipo_lettura = fpro.fp_tipo_let

		fprol = aqua_data['Fatprol'] if 'Fatprol' in aqua_data else None
		if 'Fatprot' in aqua_data:
			fprot = sorted(aqua_data['Fatprot'], key=lambda t: (t.fpt_vigore, t.fpt_codtar, t.fpt_colonna))
		fproc = aqua_data['Fatproc'] if 'Fatproc' in aqua_data else None
		fpros = aqua_data['Fatpros'] if 'Fatpros' in aqua_data else None

		logger.prefix_info("Utente:\t[%d/%s]", fpro.fp_aconto, fpro.fp_azienda)
		logger.prefix_info("Lettura:\t[%s/%d/%d %s]", tipo_lettura, fpro.fp_numlet_pr, fpro.fp_numlet_aa, fpro.fp_data_let)
		if not 'Fatproc' in aqua_data:
			logger.prefix_warn("Non ci sono Costi [Fatproc]")
		if not 'Fatpros' in aqua_data:
			logger.prefix_warn("Non ci sono Storni [Fatpros]")

	except:
		logger.error("%s: Errore durante l'inizializzazione.", basename(__file__))
		raise


#=##############################################################################
def csv_print():
	for k in aqua_data.keys():
		print()
		print(aqua_data[k][0].get_csv_hdr())
		print('\n'.join([i.get_csv_row() for i in aqua_data[k]]))
	print()
	print(results[0].get_csv_hdr())
	print('\n'.join([i.get_csv_row() for i in results]))


#=##############################################################################
def pretty_print():
	print()
	for k in aqua_data.keys():
		print('\n\n'.join([i.pretty_print() for i in aqua_data[k]]))
	print('\n\n'.join([i.pretty_print() for i in results]))


#=##############################################################################
if __name__ == '__main__':
	logger.debug('initialize(): Starting ')
	initialize()
	logger.debug('initialize(): Done')

	try:
		logger.debug('main(): Starting')
		main()

		## Stampe di debug
		csv_print()
		# print('\n\n'.join([i.pretty_print() for i in results]))
		# print(results[0].get_csv_hdr())
		# print('\n'.join([i.get_csv_row() for i in results]))

		logger.debug('main(): Done')
	except:
		logger.error("Utente: %d/%s, lettura: %d/%d", fpro.fp_aconto, fpro.fp_azienda, fpro.fp_numlet_pr, fpro.fp_numlet_aa)
		raise
