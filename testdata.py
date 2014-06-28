# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:		testdata
#-------------------------------------------------------------------------------

from aquaclasses import *

##################################################################################

fpr = Fatpro()
fpr.fp_azienda = "SERRA               "
fpr.fp_numlet_aa = 10
fpr.fp_numlet_pr = 2758
fpr.fp_aconto = 11793
fpr.fp_fatt_comp = "N"
fpr.fp_fatturare = " "
fpr.fp_bc_funz = "            "
fpr.fp_bc_fredda = "            "
fpr.fp_bc_calda = "            "
fpr.fp_bc_garage = "            "
fpr.fp_uso_acqua = "D"
fpr.fp_tar_acqua = "AR03 "
fpr.fp_tar_qf = "QR03 "
fpr.fp_fogna = "FOGNA"
fpr.fp_depur = "DEPUR"
fpr.fp_garage = "N"
fpr.fp_data_let = "20100927"
fpr.fp_tipo_let = "R"
fpr.fp_periodo = 192

#=##############################################################################

fpc = Fatproc()
fpc.fpc_bcodart = "AC   "
fpc.fpc_qta = 1.000
fpc.fpc_costo = 5.164600

fpc = Fatproc()
fpc.fpc_bcodart = "ACS  "
fpc.fpc_qta = 1.000
fpc.fpc_costo = 5.164600

fpc = Fatproc()
fpc.fpc_bcodart = "CS   "
fpc.fpc_qta = 1.000
fpc.fpc_costo = 5.000000

#=##############################################################################

fps = Fatpros()
fps.fps_bcodart = "DES  "
fps.fps_qta = 34.000
fps.fps_costo = 0.412445
fps.fps_bubicaz = "7   "

fps = Fatpros()
fps.fps_bcodart = "FOS  "
fps.fps_qta = 34.000
fps.fps_costo = 0.153073
fps.fps_bubicaz = "6   "

fps = Fatpros()
fps.fps_bcodart = "TAG1S"
fps.fps_qta = 12.000
fps.fps_costo = 0.184102
fps.fps_bubicaz = "1   "

fps = Fatpros()
fps.fps_bcodart = "TAG2S"
fps.fps_qta = 11.000
fps.fps_costo = 0.396411
fps.fps_bubicaz = "2   "

fps = Fatpros()
fps.fps_bcodart = "TBAS "
fps.fps_qta = 11.000
fps.fps_costo = 0.668236
fps.fps_bubicaz = "3   "

#=##############################################################################

fpl = Fatprol()
fpl.fpl_gruppo = 1
fpl.fpl_garage = " "
fpl.fpl_fc = 0
fpl.fpl_progr = 1
fpl.fpl_codprc = "U"
fpl.fpl_costo = 0.00
fpl.fpl_cons_iniz = 0
fpl.fpl_cifre = 4
fpl.fpl_data_sost = "        "
fpl.fpl_numeri = 1325
fpl.fpl_cambio_ct = " "
fpl.fpl_data_let_p = "20100617"
fpl.fpl_tipo_let_p = "S"
fpl.fpl_numeri_p = 1282
fpl.fpl_data_let_r = "20100319"
fpl.fpl_numeri_r = 1282
fpl.fpl_periodo_c = 192
fpl.fpl_consumo = 43

fpl = Fatprol()
fpl.fpl_gruppo = 1
fpl.fpl_garage = " "
fpl.fpl_fc = 1
fpl.fpl_progr = 1
fpl.fpl_codprc = "U"
fpl.fpl_costo = 0.00
fpl.fpl_cons_iniz = 0
fpl.fpl_cifre = 4
fpl.fpl_data_sost = "        "
fpl.fpl_numeri = 1576
fpl.fpl_cambio_ct = " "
fpl.fpl_data_let_p = "20100617"
fpl.fpl_tipo_let_p = "S"
fpl.fpl_numeri_p = 1552
fpl.fpl_data_let_r = "20100319"
fpl.fpl_numeri_r = 1552
fpl.fpl_periodo_c = 192
fpl.fpl_consumo = 24

#=##############################################################################

fpt = Fatprot()
fpt.fpt_vigore = "20090101"
fpt.fpt_codtar = "AR03 "
fpt.fpt_colonna = 1
fpt.fpt_bcodart_s = "TAG1S"
fpt.fpt_bcodart_r = "TAG1 "
fpt.fpt_quota = 128.80
fpt.fpt_quota_um = "LT"
fpt.fpt_costo_imp = 0.167365
fpt.fpt_costo_piva = 10.00
fpt.fpt_costo_iva = 0.016737
fpt.fpt_costo_tot = 0.184102
fpt.fpt_costo_um = "MC"

fpt = Fatprot()
fpt.fpt_vigore = "20090101"
fpt.fpt_codtar = "AR03 "
fpt.fpt_colonna = 2
fpt.fpt_bcodart_s = "TAG2S"
fpt.fpt_bcodart_r = "TAG2 "
fpt.fpt_quota = 123.30
fpt.fpt_quota_um = "LT"
fpt.fpt_costo_imp = 0.360374
fpt.fpt_costo_piva = 10.00
fpt.fpt_costo_iva = 0.036037
fpt.fpt_costo_tot = 0.396411
fpt.fpt_costo_um = "MC"

fpt = Fatprot()
fpt.fpt_vigore = "20090101"
fpt.fpt_codtar = "AR03 "
fpt.fpt_colonna = 3
fpt.fpt_bcodart_s = "TBAS "
fpt.fpt_bcodart_r = "TBA  "
fpt.fpt_quota = 123.20
fpt.fpt_quota_um = "LT"
fpt.fpt_costo_imp = 0.607487
fpt.fpt_costo_piva = 10.00
fpt.fpt_costo_iva = 0.060749
fpt.fpt_costo_tot = 0.668236
fpt.fpt_costo_um = "MC"

fpt = Fatprot()
fpt.fpt_vigore = "20090101"
fpt.fpt_codtar = "AR03 "
fpt.fpt_colonna = 4
fpt.fpt_bcodart_s = "TEC1S"
fpt.fpt_bcodart_r = "TEC1 "
fpt.fpt_quota = 169.90
fpt.fpt_quota_um = "LT"
fpt.fpt_costo_imp = 1.400308
fpt.fpt_costo_piva = 10.00
fpt.fpt_costo_iva = 0.140031
fpt.fpt_costo_tot = 1.540339
fpt.fpt_costo_um = "MC"

fpt = Fatprot()
fpt.fpt_vigore = "20090101"
fpt.fpt_codtar = "AR03 "
fpt.fpt_colonna = 5
fpt.fpt_bcodart_s = "TEC2S"
fpt.fpt_bcodart_r = "TEC2 "
fpt.fpt_quota = 99999.00
fpt.fpt_quota_um = "LT"
fpt.fpt_costo_imp = 2.059273
fpt.fpt_costo_piva = 10.00
fpt.fpt_costo_iva = 0.205927
fpt.fpt_costo_tot = 2.265200
fpt.fpt_costo_um = "MC"

fpt = Fatprot()
fpt.fpt_vigore = "20090101"
fpt.fpt_codtar = "DEPUR"
fpt.fpt_colonna = 1
fpt.fpt_bcodart_s = "DES  "
fpt.fpt_bcodart_r = "DE   "
fpt.fpt_quota = 99999.00
fpt.fpt_quota_um = "LT"
fpt.fpt_costo_imp = 0.374950
fpt.fpt_costo_piva = 10.00
fpt.fpt_costo_iva = 0.037495
fpt.fpt_costo_tot = 0.412445
fpt.fpt_costo_um = "MC"

fpt = Fatprot()
fpt.fpt_vigore = "20090101"
fpt.fpt_codtar = "FOGNA"
fpt.fpt_colonna = 1
fpt.fpt_bcodart_s = "FOS  "
fpt.fpt_bcodart_r = "FO   "
fpt.fpt_quota = 99999.00
fpt.fpt_quota_um = "LT"
fpt.fpt_costo_imp = 0.139157
fpt.fpt_costo_piva = 10.00
fpt.fpt_costo_iva = 0.013916
fpt.fpt_costo_tot = 0.153073
fpt.fpt_costo_um = "MC"

fpt = Fatprot()
fpt.fpt_vigore = "20090101"
fpt.fpt_codtar = "QR03 "
fpt.fpt_colonna = 1
fpt.fpt_bcodart_s = "QF   "
fpt.fpt_bcodart_r = "QF   "
fpt.fpt_quota = 3287.67
fpt.fpt_quota_um = "LT"
fpt.fpt_costo_imp = 0.031598
fpt.fpt_costo_piva = 10.00
fpt.fpt_costo_iva = 0.003160
fpt.fpt_costo_tot = 0.034758
fpt.fpt_costo_um = "GG"

#=##############################################################################
