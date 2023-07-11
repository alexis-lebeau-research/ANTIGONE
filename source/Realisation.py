# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import sys

import DispatchV0



def realisation_annee_courante(donnees_entree, donnees_simulation):
    """
    Effectue les dispatchs correspondant aux météos de l'ambiance réalisée à l'année courante et renvoie la liste des
    résultats annuels correspondants.

    Paramètres
    ----------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser

    Retours
    -------
    list
        liste des instances de DispatchV0.ResultatAnnuel correspondant aux météos de l'ambiance réalisée à l'année
        courante
    """

    annee_courante = donnees_simulation.annee_courante

    # calcul des résultats annuels pour toutes les météos de l'ambiance réalisée
    liste_threads_dispatch_annuel = []
    for indice_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
    
        compte_unites = dict()
        for actif in donnees_entree.tous_actifs():
            compte_unites[actif.cle] = donnees_simulation.parc.nombre_unites(actif.cle, annee_courante)
        

        donnees_dispatch = donnees_entree.realisation["meteo_%d"%indice_meteo]
        donnees_couts_var = donnees_entree.realisation["couts_combustibles"]

        thread_dispatch_annuel = DispatchV0.ThreadDispatchAnnuel(donnees_entree, compte_unites, donnees_dispatch,donnees_couts_var, annee_courante,annee_courante)
        

        liste_threads_dispatch_annuel.append(thread_dispatch_annuel)
        thread_dispatch_annuel.start()

    for indice_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
        liste_threads_dispatch_annuel[indice_meteo].join()

    liste_resultats_annuels = []
    for indice_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
        liste_resultats_annuels.append(liste_threads_dispatch_annuel[indice_meteo].resultat_annuel)

    return liste_resultats_annuels
