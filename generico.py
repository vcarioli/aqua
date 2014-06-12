# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:		main_program
#-------------------------------------------------------------------------------
# Da fare:
#   Logging errori più intelleggibile
#	Compattazione degli storni
#	Cambio tariffa (in sospeso)
#	Gestione del garage
#-------------------------------------------------------------------------------

import logging
from aquaclasses import *


#=##################################################################################################

fpro = None
tipo_lettura = None

fprol = None
fproc = None
fprot = None
fpros = None

#=##################################################################################################

def out_results(results):
	with open(output_filename, "w") as fout:
		fout.writelines([str(o) + '\n' for o in results])
	logging.info('Results written to ' + output_filename)

#=##################################################################################################

def ricerca_indici():
	"""Ricerca indici valori per Quota fissa, Fogna e Depurazione"""
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
	"""Tariffe e scaglioni Acqua"""
	ta = [x for x in fprot if x.fpt_codtar[0] == 'A']
	sa = [round(x.fpt_quota * fpro.fp_periodo / 1000) if x.fpt_quota < 99999 else 99999 for x in ta]
	return zip(ta, sa)

def letture_casa_garage():
	"""Isolamento letture casa da letture garage"""
	casa = [x for x in fprol if x.fpl_garage == '']
	garage = [x for x in fprol if x.fpl_garage == 'G']
	return casa, garage

def costo(index, numfat, qta):
	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'C'
	o.fpo_bcodart = fprot[index].fpt_bcodart_s if tipo_lettura == 'S' else fprot[index].fpt_bcodart_r
	o.fpo_costo = fprot[index].fpt_costo_tot
	o.fpo_qta = qta
	return o

def addebito_acqua(fpt, sca, mct, numfat):
	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'C'
	o.fpo_bcodart = fpt.fpt_bcodart_s if tipo_lettura == 'S' else fpt.fpt_bcodart_r
	o.fpo_costo = fpt.fpt_costo_tot
	o.fpo_qta = sca if mct > sca else mct
	return o

def indici_valori_acqua_calda():
	"""Ricerca indici valori per Acqua calda (s/r)"""
	ac, acs = 0, 0
	for i in range(len(fproc)):
		if fproc[i].fpc_bcodart == 'ACS':
			acs = i
		elif fproc[i].fpc_bcodart == 'AC':
			ac = i
	return ac, acs

def costo_acqua_calda(qta, numfat):
	iAc, iAcs = indici_valori_acqua_calda()
	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'C'
	o.fpo_bcodart = fproc[iAcs].fpc_bcodart if tipo_lettura == 'S' else fproc[iAc].fpc_bcodart
	o.fpo_costo = fproc[iAc].fpc_costo
	o.fpo_qta = qta
	return o

def get_numfat(bcodart):
	numfat = {'MC': 10000, 'QAC': 1000, 'CS': 99999}
	return numfat[bcodart]

def altri_costi(fpc):
	o = Output()
	o.fpo_numfat = get_numfat(fpc.fpc_bcodart)
	o.fpo_cs = 'C'
	o.fpo_bcodart = fpc.fpc_bcodart
	o.fpo_costo = fpc.fpc_costo
	o.fpo_qta = 1
	return o

def consumo_totale_mc(casa):
	"""Consumo totale in metri cubi esclusi garage"""
	return sum([x.fpl_consumo for x in casa])

def consumo_totale_mc_fredda_calda(casa):
	"""Consumo totale fredda e calda esclusi garage"""
	fredda = sum([x.fpl_consumo for x in casa if x.fpl_fc == 0])
	calda = sum([x.fpl_consumo for x in casa if x.fpl_fc == 1])
	return fredda, calda

def consumo_totale_mc_garage(garage):
	"""Consumo totale garage (fredda + eventuale calda)"""
	return sum([x.fpl_consumo for x in garage])

def storno(fps, numfat):
	o = Output()
	o.fpo_numfat = numfat
	o.fpo_cs = 'S'
	o.fpo_qta = -1 * fps.fps_qta
	o.fpo_costo = fps.fps_costo
	o.fpo_bcodart = 'S' + fps.fps_bcodart[0:len(fps.fps_bcodart)-1]
	return o

def compatta_storni(fpros):
	s = {}
	for fps in fpros:
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

	return sorted(storni, key=lambda x:x.fps_bubicaz)

#=##################################################################################################

def main():
	# Isolamento letture casa da letture garage
	casa, garage = letture_casa_garage()

	# Calcolo consumo totale in metri cubi esclusi garage
	Mc_Tot = consumo_totale_mc(casa)

	# Calcolo consumo totale fredda e calda esclusi garage
	Mc_F, Mc_C = consumo_totale_mc_fredda_calda(casa)

	# Calcolo consumo totale garage (fredda + eventuale calda)
	Mc_G = consumo_totale_mc_garage(garage)

	results = []
	numfat = 0

	# Calcolo righe addebito acqua totale consumata
	mct = Mc_Tot
	for (fpt, sca) in tariffe_scaglioni_acqua():
		if mct > 0:
			results.append(addebito_acqua(fpt, sca, mct, numfat))
			mct -= sca if mct > sca else mct
			numfat += 1

	iQf, iFogna, iDepur = ricerca_indici()

	# Fognatura
	results.append(costo(iFogna, numfat, Mc_Tot))
	numfat += 1

	# Depurazione
	results.append(costo(iDepur, numfat, Mc_Tot))
	numfat += 1

	# Quota fissa (in realta' non e' differenziata per lettura s/r)
	results.append(costo(iQf, numfat, fpro.fp_periodo))
	numfat += 1

	# Acqua calda, se presente
	if Mc_C > 0:
		results.append(costo_acqua_calda(Mc_C, numfat))
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

#=##################################################################################################

if __name__ == '__main__':
	try:
		fpro = aqua_data['Fatpro'][0]
		tipo_lettura = fpro.fp_tipo_let

		fprol = aqua_data['Fatprol']
		fproc = aqua_data['Fatproc']
		fprot = aqua_data['Fatprot']
		fpros = aqua_data['Fatpros'] if 'Fatpros' in aqua_data else None

		main()
	except:
		logging.error('Azienda: {0}, lettura: {1}/{2}, utente: {3}'.format(fpro.fp_azienda, fpro.fp_numlet_pr, fpro.fp_numlet_aa, fpro.fp_aconto))
		raise
