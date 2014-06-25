# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:		main_program
# -------------------------------------------------------------------------------
# Da fare:
#   Logging errori più intelleggibile
#	Cambio tariffa (in sospeso)
#	Gestione del garage
#-------------------------------------------------------------------------------

import logging
from aquaclasses import *
from decimal import Decimal
from inputreader import InputReader


#=##################################################################################################

fpro = None		# Dati di fatturazione dell'azienda
fprol = []		# letture
fproc = []		# costi
fprot = []		# tariffe
fpros = []		# scaglioni
tipo_lettura = []


#=##################################################################################################
def write_output(results):
	"""
	Scrive i risultati nel file di output
	:param results: <[Output()]>
	:return; <None>
	"""
	with open(output_filename, "w") as fout:
		fout.writelines([str(o) + '\n' for o in results])


#=##################################################################################################
def ricerca_indici():
	"""
	Ricerca indici valori per Quota fissa, Fogna e Depurazione
	:return: <(int, int, int)> - Quota fissa, Fogna, Depurazione
	"""
	ix_quota_fissa, ix_fogna, ix_depuratore = 0, 0, 0
	for i in range(len(fprot)):
		if fprot[i].fpt_codtar[0] == 'Q':
			ix_quota_fissa = i
		elif fprot[i].fpt_codtar == 'FOGNA':
			ix_fogna = i
		elif fprot[i].fpt_codtar == 'DEPUR':
			ix_depuratore = i
	return ix_quota_fissa, ix_fogna, ix_depuratore


def tariffe_scaglioni_acqua():
	"""
	Tariffe e scaglioni Acqua
	:return: <[(Fatprot(), Dec(5.2))]> - Lista di coppie Fatprot(), costo_scaglione
	"""
	ta = [x for x in fprot if x.fpt_codtar[0] == 'A']
	sa = [Decimal(round(x.fpt_quota * fpro.fp_periodo / 1000)) if x.fpt_quota < 99999 else 99999 for x in ta]
	return zip(ta, sa)


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


def addebito_acqua(tariffa, scaglione, mc_totali, numfat):
	"""
	Prepara un record di Output() di addebiti
	:param tariffa : <Fatprot()> - Tariffa
	:param scaglione : <Dec(5.2)> - Scaglione
	:param mc_totali : <int> - Metri cubi totali
	:param numfat : <int> - Numero fattura (per l'ordinamento delle righe di output)
	:return : <Output()>
	"""
	assert isinstance(tariffa, Fatprot)
	assert isinstance(scaglione, (int, Decimal))
	assert isinstance(mc_totali, (int, Decimal))
	assert isinstance(numfat, int)

	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'C'
	o.fpo_bcodart = tariffa.fpt_bcodart_s if tipo_lettura == 'S' else tariffa.fpt_bcodart_r
	o.fpo_costo = tariffa.fpt_costo_tot
	o.fpo_qta = scaglione if mc_totali > scaglione else mc_totali
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
	iac, iacs = 0, 0
	for i in range(len(fproc)):
		if fproc[i].fpc_bcodart == 'AC':
			iac = i
		elif fproc[i].fpc_bcodart == 'ACS':
			iacs = i

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
	costi = [
		# 'BA',		# Bocche Antincendio
		# 'SDB',	# Spese domiciliazione bolletta
		'CS',		# Competenze servizio
		'MC',		# Manutenzione contatori
		'QAC',		# Quota Fissa acqua calda
	]
	results = []
	for c in fproc:
		if c.fpc_bcodart in costi:
			o = Output()
			o.fpo_numfat = get_numfat(c.fpc_bcodart)
			o.fpo_cs = 'C'
			o.fpo_bcodart = c.fpc_bcodart
			o.fpo_costo = c.fpc_costo
			o.fpo_qta = 1
			results.append(o)

	return results


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
	o.fpo_qta = -1 * storno.fps_qta
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


#=##################################################################################################

def main():
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

	results = []
	numfat = 0

	# Calcolo righe addebito acqua totale consumata
	consumo = mc_consumo_totale
	for (tariffa, scaglione) in tariffe_scaglioni_acqua():
		if consumo > 0:
			results.append(addebito_acqua(tariffa, scaglione, consumo, numfat))
			consumo -= scaglione if consumo > scaglione else consumo
			numfat += 1

	ix_qfissa, ix_fogna, ix_depur = ricerca_indici()

	# Fognatura
	results.append(costo(fprot[ix_fogna], numfat, mc_consumo_totale_casa))
	numfat += 1

	# Depurazione
	results.append(costo(fprot[ix_depur], numfat, mc_consumo_totale_casa))
	numfat += 1

	# Quota fissa (non e' differenziata per lettura s/r)
	results.append(costo(fprot[ix_qfissa], numfat, fpro.fp_periodo))
	numfat += 1

	# Acqua calda, se presente
	if mc_consumo_calda_casa > 0:
		results.append(costo_acqua_calda(mc_consumo_calda_casa, numfat))
		numfat += 1

	results += altri_costi()

	if fpros:
		numfat = 50000
		for fps in compatta_storni(fpros):
			results.append(calcolo_storno(fps, numfat))
			numfat += 1

	write_output(results)

#	print('\n\n'.join([i.pretty_print() for i in results]))
#	print(results[0].get_csv_hdr())
#	print('\n'.join([i.get_csv_row() for i in results]))

	logging.info('generico.py: main(): Results written to ' + output_filename)


#=##################################################################################################
# Non modificare dopo questa linea
#=##################################################################################################


#=##################################################################################################
def initialize():
	"""
	Lettura dei dati dal file di input e inizializzazione delle variabili globali
	:return: None
	"""
	global aqua_data, fpro, tipo_lettura, fprol, fproc, fprot, fpros

	try:
		aqua_data = InputReader(aqua_classes, input_filename).read()

		fpro = aqua_data['Fatpro'][0]
		tipo_lettura = fpro.fp_tipo_let

		fprol = aqua_data['Fatprol']
		fproc = aqua_data['Fatproc'] if 'Fatproc' in aqua_data else None
		fprot = aqua_data['Fatprot']
		fpros = aqua_data['Fatpros'] if 'Fatpros' in aqua_data else None

	except:
		logging.error("Errore durante l'inizializzazione.")
		raise


#=##################################################################################################
if __name__ == '__main__':
	logging.info('generico.py: starting initialize()')
	initialize()
	logging.info('generico.py: initialize() done')

	try:
		logging.info('generico.py: starting main()')
		main()
		logging.info('generico.py: main() done')
	except:
		logging.error(
			'Azienda: {0}, lettura: {1}/{2}, utente: {3}'.format(
				fpro.fp_azienda,
				fpro.fp_numlet_pr,
				fpro.fp_numlet_aa,
				fpro.fp_aconto
			)
		)
		raise
