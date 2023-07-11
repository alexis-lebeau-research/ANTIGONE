# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF


import sys
import pandas as pd
import os
import time
import pulp
import numpy as np

import Gep

def pjoin(*args, **kwargs):
    return os.path.join(*args, **kwargs).replace(os.sep, '//')
    
if __name__ == '__main__':
    
    print("ANTIGONE GEP")
    
    temps_debut = time.time()
    
       
    nom_dossier_donnees = sys.argv[1]
    type_optim = sys.argv[2]   
    
    chemin_rep = pjoin("..",nom_dossier_donnees)

    chemin_sorties = pjoin("..","results","SORTIES_GEP",nom_dossier_donnees+"_"+time.strftime("_%d_%B_%Y_%Hh%Mm%Ss") +"_"+type_optim)
    os.makedirs(chemin_sorties)
    
    ###### Realisation du GEP
    
    
    df_reg_ouvertures, df_reg_fermetures = Gep.run_gep(chemin_rep,chemin_sorties,type_optim)
    
    temps_fin = time.time()
    
    print("Temps d'exécution : ", temps_fin - temps_debut)