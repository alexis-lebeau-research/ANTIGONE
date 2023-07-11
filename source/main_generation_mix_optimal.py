# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF


import sys
import time
import os
import pandas as pd

import Lecture
import GenerationMixOptimal

if __name__ == '__main__':
    temps_debut = time.time()

    nom_dossier_donnees = sys.argv[1]
    annee = int(sys.argv[2])

    donnees_entree, donnees_simulation = Lecture.lecture_generale(nom_dossier_donnees, callType='mix_optimal')

    liste_contraintes_mix = []
    chemin_fichier_contraintes_mix = os.path.dirname(os.getcwd()) + '/instances/' + nom_dossier_donnees + "/GenerationMixOptimal/contraintes_mix.csv"
    try:
        liste_contraintes_mix = Lecture.lecture_fichier_contraintes_mix(chemin_fichier_contraintes_mix, donnees_entree)
    except(pd.errors.EmptyDataError, FileNotFoundError):
        pass

    print("Calcul du mix optimal 'from scratch'.")

    mix_optimal, registre_couts, registre_annuel, registre_horaire = GenerationMixOptimal.generation_mix_optimal(donnees_entree, annee, liste_contraintes_mix)

    print("Mix optimal 'from scratch' : ", mix_optimal)

    if donnees_entree.parametres_simulation.sortie_complete:
        dossier_compte_rendu = os.path.dirname(os.getcwd()) + '/results/' + "SORTIE_GENERATION_MIX_OPTIMAL_" + nom_dossier_donnees + time.strftime("%d_%B_%Y_%Hh%Mm%Ss")
        os.mkdir(dossier_compte_rendu)

        data_frame_registre_couts = pd.DataFrame(registre_couts)
        data_frame_registre_couts.to_csv(dossier_compte_rendu + "/registre_couts.csv", sep=';')

        data_frame_registre_annuel = pd.DataFrame(registre_annuel)
        data_frame_registre_annuel.to_csv(dossier_compte_rendu + "/registre_annuel.csv", sep=';')

        for indice_meteo in range(len(registre_horaire)):
            donnees_horaires_meteo = registre_horaire[indice_meteo]
            data_frame_donnees_horaires = pd.DataFrame(donnees_horaires_meteo, index=range(8760))
            data_frame_donnees_horaires.to_csv(dossier_compte_rendu + "/registre_horaire_meteo_%d.csv"% indice_meteo, sep=';')

    temps_fin = time.time()

    print("Temps d'exécution : ", temps_fin - temps_debut)
