# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF


import sys
import pandas as pd
import os
import time

import Lecture
import GenerationMixCible


if __name__ == '__main__':
    temps_debut = time.time()

    nom_dossier_donnees = sys.argv[1]
    type_optim = sys.argv[2]

    taux_actualisation = 0.00

    donnees_entree, donnees_simulation = Lecture.lecture_generale(nom_dossier_donnees, callType='mix_cible')

    dossier_compte_rendu = os.path.dirname(os.getcwd()) + '/results/' + "SORTIE_GENERATION_MIX_CIBLE_" + nom_dossier_donnees + time.strftime("_%d_%B_%Y_%Hh%Mm%Ss" +"_"+type_optim )
    os.makedirs(dossier_compte_rendu)
    
    donnees_entree.output_path = dossier_compte_rendu
        
    liste_contraintes_trajectoire = []
    chemin_fichier_contraintes_trajectoire = os.path.dirname(os.getcwd()) + '/instances/' + nom_dossier_donnees +"/GenerationMixCible/contraintes_trajectoire.csv"
    try:
        liste_contraintes_trajectoire = Lecture.lecture_fichier_contraintes_trajectoire(chemin_fichier_contraintes_trajectoire, donnees_entree)
    except(pd.errors.EmptyDataError, FileNotFoundError):
        pass

        
    chemin_co2_quota = os.path.dirname(os.getcwd()) + '/instances/' + nom_dossier_donnees +"/GenerationMixCible/co2_quota.csv"
    
    df_co2_quota = pd.read_csv(chemin_co2_quota,sep=";",index_col=0)
        
    print("Calcul de la trajectoire optimisée.")

    mix_cible, registre_couts, registre_annuel, registre_horaire,probleme_genration_mix_cible = GenerationMixCible.generation_mix_cible(donnees_entree, donnees_simulation, liste_contraintes_trajectoire, type_optim,df_co2_quota,taux_actualisation)

        
    # rérécriture du fichier de mix cible
    nombre_annees = donnees_entree.parametres_simulation.horizon_simulation #+ donnees_entree.parametres_simulation.horizon_prevision
    data_frame_mix_cible = pd.DataFrame(columns=range(nombre_annees))
    for cle_actif, trajectoire_cible in mix_cible.items():
        data_frame_mix_cible.loc[cle_actif] = trajectoire_cible

    chemin_fichier_mix_cible = os.path.dirname(os.getcwd()) + '/instances/' + nom_dossier_donnees +"/AppelsOffres/mix_cible.csv"

    try:
        data_frame_mix_cible.to_csv(chemin_fichier_mix_cible, sep=';')
        print("Réécriture du fichier de mix cible.")
    except FileNotFoundError:
        pass



    if donnees_entree.parametres_simulation.sortie_complete:




        data_frame_registre_couts = pd.DataFrame(registre_couts)
        data_frame_registre_couts.to_csv(dossier_compte_rendu + "/registre_couts.csv", sep=';')

        data_frame_registre_annuel = pd.DataFrame(registre_annuel, index=range(nombre_annees))
        data_frame_registre_annuel.to_csv(dossier_compte_rendu + "/registre_annuel.csv", sep=';')

        for annee in range(len(registre_horaire)):
            liste_donnees_horaires_annee = registre_horaire[annee]
            for indice_meteo in range(len(liste_donnees_horaires_annee)):
                donnees_horaires_annee_meteo = liste_donnees_horaires_annee[indice_meteo]
                data_frame_donnees_horaires = pd.DataFrame(donnees_horaires_annee_meteo, index=range(8760))
                data_frame_donnees_horaires.to_csv(dossier_compte_rendu + "/registre_horaire_annee_%d_meteo_%d.csv"%(annee, indice_meteo), sep=';')

    temps_fin = time.time()

    print("Temps d'exécution : ", temps_fin - temps_debut)