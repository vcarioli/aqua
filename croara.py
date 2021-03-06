# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
##----------------------------------------------------------------------------------------------------------------------
##	Name:		croara
##----------------------------------------------------------------------------------------------------------------------

from collections import OrderedDict
from datetime import timedelta
from decimal import Decimal
from os.path import basename

from aquaclasses import *
from aquaerrors import DataMissingError, CostCodeMissingError, InvalidDataError
from inputreader import InputReader
from logger import Logger

##======================================================================================================================

logger = Logger(filename=__file__, log_filename=globals()['log_filename'], prefix='---  ', debug_mode=False)
logger.config()

fpro = None  # Dati di fatturazione dell'azienda
fprol = []  # letture
fproc = []  # costi
fprot = []  # tariffe
fpros = []  # scaglioni

results = []
tipo_lettura = ''

# Lettura file dei dati in input
logger.debug('InputReader().read(): Starting')
aqua_data = InputReader(aqua_classes, globals()['input_filename']).read()
logger.debug('InputReader().read(): Done')


##======================================================================================================================


def write_output(res):
	"""
	Scrive i risultati nel file di output

	:param res: <[Output()]>
	:return <None>
	"""
	with open(globals()['output_filename'], "w") as fout:
		fout.writelines([str(o) + '\n' for o in res])


def output_line(numfat, cs, codart, qta, importo):
	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = cs
	o.fpo_bcodart = codart
	o.fpo_costo = importo
	o.fpo_qta = qta
	return o


def scaglione(tar, mc):
	"""
	Scaglione Acqua

	:param tar: Fatprot() - Tariffa
	:param mc: int - metri cubi
	:return Decimal()
	"""
	assert isinstance(tar, Fatprot)
	assert isinstance(mc, (int, Decimal))

	return Decimal(round(tar.fpt_quota * mc / 1000) if tar.fpt_quota < 99999 else 99999)


def costo(tar, qta):
	"""
	Prepara un record di Output() di costi

	:param tar: <Fatprot()> - Tariffa applicata
	:param qta: <Dec(5.3> - Quantità
	:return Output()
	"""
	assert isinstance(tar, Fatprot)
	assert isinstance(qta, (Decimal, int))

	codart = tar.fpt_bcodart_s if tipo_lettura == 'S' else tar.fpt_bcodart_r
	return output_line(tar.fpt_bgiorni, 'C', codart, qta, tar.fpt_costo_tot)


def costo_acqua_calda(qta):
	"""
	Calcola il costo dell'acqua calda

	:param qta: <int> - Quantità consumata
	:return <Output()>
	"""
	assert isinstance(qta, (int, Decimal))

	codart = 'AC' if tipo_lettura == 'R' else 'ACS'
	try:
		ac = [x for x in fproc if x.fpc_bcodart == codart][0]
		importo = ac.fpc_costo
		return output_line(ac.fpc_bgiorni, 'C', codart, qta, importo)
	except:
		raise DataMissingError('', "Nei costi manca il codice '{0}'".format(codart))


def altri_costi():
	"""
	Produce una lista di costi aggiuntivi

	:return <[Output()]>
	"""

	result = [
		output_line(c.fpc_bgiorni, 'C', c.fpc_bcodart, fpro.fp_periodo_p if c.fpc_bcodart == 'AFF' else 1, c.fpc_costo)
		for c in fproc if c.fpc_bcodart not in ('AC', 'ACS')
		]

	if len(result) == 0:
		logger.prefix_warn("Non ci sono costi da fatturare")

	return result


def consumo_mc(letture):
	"""
	Consumo in metri cubi

	:param letture: <[Fatprol()]> - Lista letture
	:return <Decimal()> - Consumo (mc)
	"""
	if letture:
		assert isinstance(letture[0], Fatprol)

	return Decimal(sum([x.fpl_consumo for x in letture]))


def calcolo_storno(st):
	"""
	Calcolo dello storno

	:param st: <Fatpros()> - Storno
	:return <Output()> Risultato
	"""
	assert isinstance(st, Fatpros)

	return output_line(st.fps_bgiorni, 'S', st.fps_bcodart, -st.fps_qta, st.fps_costo)


def compatta_storni(storni):
	"""
	Compattazione e ordinamento degli storni

	:param storni: <[Fatpros()]> - Lista degli storni
	:return <[Fatpros()]> - Lista degli storni compattati
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

	return storni


def calcolo_tariffe(start_date, end_date, tar):
	x = []
	for t in tar:
		if t.fpt_vigore <= end_date:
			codart = t.fpt_bcodart_r if tipo_lettura == 'R' else t.fpt_bcodart_s
			k = ((t.fpt_vigore, t.fpt_codtar, codart), max(t.fpt_vigore, start_date))
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


def giorni_tariffe(start_date, end_date):
	consumi = dict()

	tariffe = set([x.fpt_codtar for x in fprot])

	for t in tariffe:
		for k, v in calcolo_tariffe(start_date, end_date, [x for x in fprot if x.fpt_codtar == t]).items():
			consumi[k] = v

	return consumi


##======================================================================================================================


def main():
	global results

	# Isolamento letture casa da letture garage
	letture_casa = [x for x in fprol if x.fpl_garage == '']
	letture_garage = [x for x in fprol if x.fpl_garage == 'G']

	# Consumi casa
	mc_consumo_fredda_casa = consumo_mc([x for x in letture_casa if x.fpl_fc == 0])
	mc_consumo_calda_casa = consumo_mc([x for x in letture_casa if x.fpl_fc == 1])

	# Consumi garage
	mc_consumo_fredda_garage = consumo_mc([x for x in letture_garage if x.fpl_fc == 0])
	mc_consumo_calda_garage = consumo_mc([x for x in letture_garage if x.fpl_fc == 1])

	# ----------------------------------------------------------------------------------------------
	##	Consumi totali
	# ----------------------------------------------------------------------------------------------
	mc_consumo_totale_garage = mc_consumo_fredda_garage + mc_consumo_calda_garage
	mc_consumo_totale_casa = mc_consumo_fredda_casa + mc_consumo_calda_casa

	mc_consumo_totale_calda = mc_consumo_calda_casa + mc_consumo_calda_garage
	# mc_consumo_totale_fredda = mc_consumo_fredda_casa + mc_consumo_fredda_garage

	mc_consumo_totale = mc_consumo_totale_casa + mc_consumo_totale_garage
	# ----------------------------------------------------------------------------------------------

	# Periodo di riferimento dei consumi
	end_date = fpro.fp_data_let
	start_date = end_date - timedelta(days=fpro.fp_periodo)

	# Consumi
	gt = giorni_tariffe(start_date, end_date)
	if len([gt.items()]) == 0:
		msg = 'Nessuna tariffa applicabile al periodo specificato [{0} - {1}].'.format(start_date, end_date)
		raise InvalidDataError('', msg)

	# Lista ordinata di date di inizio periodo. Serve per dare un ordinamento ai record in output
	# (nella tupla delle chiavi di 'gt' il primo elemento è la data di inizio del periodo)
	periodi = sorted(set([x[0] for x in gt.keys()]))

	for k in gt.keys():
		data_vigore = k[0]

		# Per ogni periodo di tariffazione numfat viene incrementato di 1000 * (ordinale_periodo - 1)
		# Es: 1^ periodo: numfat + 1000 * 0 = numfat, 2^ periodo = numfat + 1000 * 1 = numfat + 1000, ecc.
		# In pratica il moltiplicatore è l'indice della data di inizio periodo nella lista ordinata "periodi"
		def ordina_tariffe(o):
			o.fpo_numfat += 1000 * periodi.index(data_vigore)
			return o

		res = []
		ts = [x for x in fprot if x.fpt_vigore == data_vigore and x.fpt_codtar == k[1]]
		consumo = Decimal(round(mc_consumo_totale / fpro.fp_periodo * gt[k]))

		for tar in ts:
			qty = 0
			if tar.fpt_codtar[0] == 'A':
				if consumo > 0:
					sc = scaglione(tar, gt[k])
					qty = sc if consumo > sc else consumo
					consumo -= qty
			else:
				qty = consumo if tar.fpt_costo_um == 'MC' else gt[k]

			if qty != 0:
				res += [ordina_tariffe(costo(tar, qty))]

		results += res

	# Per non aver problemi con l'ordinamento dell'output in caso di più di due periodi di tariffazione
	# impongo l'ordinamento a numfat + 1000 * numero di scadenze
	# Es. se ci sono 2 periodi sarà: nufat + 1000 * 2 = numfat + 2000
	def ordina(o):
		o.fpo_numfat += 1000 * len(periodi)
		return o

	# Acqua calda, se presente
	try:
		if mc_consumo_totale_calda > 0:
			results += [ordina(costo_acqua_calda(mc_consumo_totale_calda))]
	except:
		msg = "Consumo acqua calda > 0 (mc {0}) ma non sono presenti i relativi costi".format(mc_consumo_totale_calda)
		raise DataMissingError("Fatproc", msg)

	# Costi
	results += [ordina(c) for c in altri_costi()]

	# Storni
	if fpros:
		results += [ordina(s) for s in [calcolo_storno(fps) for fps in compatta_storni(fpros)]]

	# Ordino i risultati rispetto fpo_numfat
	results.sort(key=lambda r: r.fpo_numfat)

	write_output(results)

	logger.debug('main(): Results written to %s', basename(globals()['output_filename']))


##======================================================================================================================
##	Inizializzazione e verifica della presenza e congruità dei dati
##======================================================================================================================


def initialize():
	"""
	Inizializzazione delle variabili globali

	:return None
	"""
	global aqua_data, fpro, tipo_lettura, fprol, fproc, fprot, fpros, logger

	try:
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

		##---------------------------------------------------------------------------------------------
		##----- Croara: depuratore e fogna non devono essere considerati ------------------------------
		##----- Filtro le tariffe per eliminare 'FOGNA' e 'DEPUR'        -----------------------------
		fprot = [f for f in fprot if f.fpt_codtar not in ['FOGNA', 'DEPUR']]
		##---------------------------------------------------------------------------------------------

		# Controllo della presenza dei costi
		if 'Fatproc' not in aqua_data:
			raise DataMissingError("", "Mancano i costi.")

		# Filtro le righe con quantità 0
		fproc = [c for c in aqua_data['Fatproc'] if c.fpc_qta != 0]
		# Il codice 'CS' deve essere presente
		if len([c for c in fproc if c.fpc_bcodart == 'CS']) == 0:
			raise CostCodeMissingError("", "Mancano le Competenze di Servizio (cod. CS).")

		# Controllo della presenza degli storni e filtro le righe con quantità 0
		if 'Fatpros' not in aqua_data:
			logger.prefix_warn("Non sono stati specificati storni.")
		else:
			fpros = [s for s in aqua_data['Fatpros'] if s.fps_qta != 0]

	except:
		logger.error("Errore durante l'inizializzazione!")
		raise


##======================================================================================================================
##	Stampe di debug
##======================================================================================================================


def csv_print_results():
	print()
	print(results[0].get_csv_hdr())
	print('\n'.join([i.get_csv_row() for i in results]))


def csv_print_data():
	for k in aqua_data.keys():
		print()
		print(aqua_data[k][0].get_csv_hdr())
		print('\n'.join([i.get_csv_row() for i in aqua_data[k]]))


def pretty_print_data():
	for k in aqua_data.keys():
		print()
		print('\n\n'.join([i.pretty_print() for i in aqua_data[k]]))


def pretty_print_results():
	print()
	print('\n\n'.join([i.pretty_print() for i in results]))


##======================================================================================================================

if __name__ == '__main__':
	try:
		logger.debug('initialize(): Starting ')
		initialize()
		logger.debug('initialize(): Done')

		logger.debug('main(): Starting')
		main()

		# Stampe di debug
		# csv_print_data()
		# print()
		# csv_print_results()
		# print();
		# print('#	TAG1, TAG2, TBA, TEC1, TEC2, CFC, DE, CDE, FO, CFO, QF')
		# pretty_print_data()
		# pretty_print_results()

		logger.debug('main(): Done')
	except:
		raise

##======================================================================================================================
