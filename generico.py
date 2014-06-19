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
from inputreader import InputReader


#=##################################################################################################

fpro = None		# Dati di fatturazione dell'azienda
fprol = []		# letture
fproc = []		# costi
fprot = []		# tariffe
fpros = []		# scaglioni
tipo_lettura = []


#=##################################################################################################
def out_results(results):
	"""
	Scrive i risultati nel file di output
	:type results: list<Output>
	:rtype: None
	:param results: Lista di Output()
	"""
	with open(output_filename, "w") as fout:
		fout.writelines([str(o) + '\n' for o in results])


#=##################################################################################################
def ricerca_indici():
	"""
	Ricerca indici valori per Quota fissa, Fogna e Depurazione
	:return: Indici (interi) di Quota fissa, Fogna e Depurazione
	:rtype : (int, int, int)
	"""
	qfissa, fogna, depur = 0, 0, 0
	for i in range(len(fprot)):
		if fprot[i].fpt_codtar[0] == 'Q':
			qfissa = i
		elif fprot[i].fpt_codtar == 'FOGNA':
			fogna = i
		elif fprot[i].fpt_codtar == 'DEPUR':
			depur = i
	return qfissa, fogna, depur


def tariffe_scaglioni_acqua():
	"""
	Tariffe e scaglioni Acqua
	:rtype: list((Fprot, int))
	:return: Lista di coppie [Fprot(), costo_scaglione]
	"""
	ta = [x for x in fprot if x.fpt_codtar[0] == 'A']
	sa = [round(x.fpt_quota * fpro.fp_periodo / 1000) if x.fpt_quota < 99999 else 99999 for x in ta]
	return zip(ta, sa)

def letture(lista_letture, tipo_lettura):
	"""

	:rtype : list
	"""
	return [x for x in lista_letture if x.fpl_garage == tipo_lettura]


def letture_casa(lista_letture):
	"""
	Letture casa (fpl_garage == '')
	:type lista_letture: object
	:return: Lista letture Casa ([Fatprol()])
	"""
	return letture(lista_letture, '')


def letture_garage(lista_letture):
	"""
	Letture garage
	:rtype : list
	:param lista_letture: lista_letture: [Fatprol, ...]
	:type lista_letture: list(Fatprol())
	:return: Lista letture Garage. ([Fatprol()])
	"""
	return letture(lista_letture, 'G')


def costo(index, numfat, qta):
	"""
	Prepara un record di Output() di costi
	:param index: Indice della tariffa
	:param numfat: Numero fattura (per l'ordinamento delle righe di output)
	:param qta: Quantità
	:rtype : Output()
	"""
	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'C'
	o.fpo_bcodart = fprot[index].fpt_bcodart_s if tipo_lettura == 'S' else fprot[index].fpt_bcodart_r
	o.fpo_costo = fprot[index].fpt_costo_tot
	o.fpo_qta = qta
	return o


def addebito_acqua(fpt, sca, mct, numfat):
	"""
	Prepara un record di Output() di addebiti
	:param fpt : Tariffa
	:param sca : Scaglione
	:param mct : Metri cubi totali
	:param numfat : Numero fattura (per l'ordinamento delle righe di output)
	:return: Output()
	:rtype : Output()
	"""
	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'C'
	o.fpo_bcodart = fpt.fpt_bcodart_s if tipo_lettura == 'S' else fpt.fpt_bcodart_r
	o.fpo_costo = fpt.fpt_costo_tot
	o.fpo_qta = sca if mct > sca else mct
	return o


def indici_valori_acqua_calda():
	"""
	Ricerca indici valori per Acqua calda (s/r)
	"""
	ac, acs = 0, 0
	for i in range(len(fproc)):
		if fproc[i].fpc_bcodart == 'ACS':
			acs = i
		elif fproc[i].fpc_bcodart == 'AC':
			ac = i
	return ac, acs


def costo_acqua_calda(qta, numfat):
	"""
	Calcola il costo dell'acqua calda
	:param qta:
	:param numfat: Numero fattura (per l'ordinamento delle righe di output)
	:return: Output()
	"""
	iac, iacs = indici_valori_acqua_calda()
	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'C'
	o.fpo_bcodart = fproc[iacs].fpc_bcodart if tipo_lettura == 'S' else fproc[iac].fpc_bcodart
	o.fpo_costo = fproc[iac].fpc_costo
	o.fpo_qta = qta
	return o


def get_numfat(bcodart):
	"""
	Decodifica il numero di fattura dal codice articolo
	:param bcodart: string - Codice articolo
	:return: Numero fattura di partenza (per l'ordinamento delle righe di output)
	"""
	numfat = {'MC': 10000, 'QAC': 1000, 'CS': 99999}
	return numfat[bcodart]


def altri_costi(fpc):
	"""
	:param fpc:
	:return: Output()
	"""
	o = Output()
	o.fpo_numfat = get_numfat(fpc.fpc_bcodart)
	o.fpo_cs = 'C'
	o.fpo_bcodart = fpc.fpc_bcodart
	o.fpo_costo = fpc.fpc_costo
	o.fpo_qta = 1
	return o


def consumo_totale_mc(lista_letture):
	"""
	Consumo totale in metri cubi
	:rtype : int
	:param lista_letture: Lista letture
	"""
	return sum([x.fpl_consumo for x in lista_letture])


def consumo_totale_mc_fredda_calda(casa):
	"""
	Consumo totale fredda e calda esclusi garage
	:rtype : int,int
	:param casa: Lista letture casa
	"""
	fredda = sum([x.fpl_consumo for x in casa if x.fpl_fc == 0])
	calda = sum([x.fpl_consumo for x in casa if x.fpl_fc == 1])
	return fredda, calda


def storno(fps, numfat):
	"""
	Calcolo dello storno
	:rtype : object
	:param fps: Fatpros() Storno
	:param numfat: Numero fattura (per l'ordinamento delle righe di output)
	:return: Output() Risultato
	"""
	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'S'
	o.fpo_qta = -1 * fps.fps_qta
	o.fpo_costo = fps.fps_costo
	o.fpo_bcodart = 'S' + fps.fps_bcodart[0:len(fps.fps_bcodart) - 1]
	return o


def compatta_storni(storni):
	"""
	Compattazione e ordinamento degli storni
	:rtype : list
	:param storni: Lista degli storni
	:return: Lista degli storni ordinati secondo il campo fps_bubicaz
	"""
	s = {}
	for fps in storni:
		k = (fps.fps_bcodart, fps.fps_costo, fps.fps_bubicaz)
		s[k] = fps.fps_qta if k not in s else s[k] + fps.fps_qta

	storni = []
	for k in s.keys():
		fps = Fatpros()
		fps.fps_bcodart = k[0]
		fps.fps_costo = k[1]
		fps.fps_bubicaz = k[2]
		fps.fps_qta = s[k]
		storni.append(fps)

	return sorted(storni, key=lambda x: x.fps_bubicaz)


#=##################################################################################################

def main():
	# Isolamento letture casa da letture garage
	casa = letture_casa(fprol)
	garage = letture_garage(fprol)

	# Calcolo consumo totale casa in metri cubi
	mc_tot = consumo_totale_mc(casa)

	# Calcolo consumo totale fredda e calda casa
	mc_f, mc_c = consumo_totale_mc_fredda_calda(casa)

	# Calcolo consumo totale garage (fredda + eventuale calda)
	mc_g = consumo_totale_mc(garage)

	results = []
	numfat = 0

	# Calcolo righe addebito acqua totale consumata
	mct = mc_tot
	for (fpt, sca) in tariffe_scaglioni_acqua():
		if mct > 0:
			results.append(addebito_acqua(fpt, sca, mct, numfat))
			mct -= sca if mct > sca else mct
			numfat += 1

	iqf, ifogna, idepur = ricerca_indici()

	# Fognatura
	results.append(costo(ifogna, numfat, mc_tot))
	numfat += 1

	# Depurazione
	results.append(costo(idepur, numfat, mc_tot))
	numfat += 1

	# Quota fissa (in realta' non e' differenziata per lettura s/r)
	results.append(costo(iqf, numfat, fpro.fp_periodo))
	numfat += 1

	# Acqua calda, se presente
	if mc_c > 0:
		results.append(costo_acqua_calda(mc_c, numfat))
		numfat += 1

	# BA	Bocche Antincendio
	# CS	Competenze servizio
	# MC	Manutenzione contatori
	# QAC	Quota Fissa acqua calda
	# SDB	Spese domiciliazione bolletta

	for fpc in fproc:
		if fpc.fpc_bcodart in ['MC', 'QAC', 'CS']:
			results.append(altri_costi(fpc))

	if fpros:
		numfat = 50000
		for fps in compatta_storni(fpros):
			results.append(storno(fps, numfat))
			numfat += 1

	out_results(results)
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
		fproc = aqua_data['Fatproc']
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
