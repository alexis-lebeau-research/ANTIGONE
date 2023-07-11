# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import sys

import DispatchV0

def anticipation_resultats_annuels(annee_debut_anticipation, annee_fin_anticipation, donnees_entree, donnees_simulation):
    """
    Calcule les dispatchs pour les années comprises entre annee_debut_anticipation (incluse) et annee_fin_anticipation (excluse) pour chaque
    ambiance et chaque météo de donnes_entree et renvoie les résultats dans une matrice indexée par
    [ambiance][annee][meteo].

    Parametres
    ----------
    annee_debut_anticipation : int
        première année anticipée
    annee_fin_anticipation : int
        année de fin d'anticipation, non-incluse dans les années anticipées
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser

    Retours
    -------
    list
        matrice indexée par [ambiance][annee][meteo] contenant les instances de DispatchV0.ResultatAnnuel resultant des
        dispatchs sur les ambiances, années et météos correspondantes
    """

    annee_courante = donnees_simulation.annee_courante
    matrice_threads_dispatch_annuel = []
    for indice_ambiance in range(len(donnees_entree.tableau_ambiances)):
        ambiance = donnees_entree.tableau_ambiances[indice_ambiance]
        matrice_threads_dispatch_annuel_ambiance = []

        for annee_anticipee in range(annee_debut_anticipation, annee_fin_anticipation):
            liste_threads_dispatch_annuel_ambiance_annee = []

            for indice_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
                compte_unites = dict()
                for actif in donnees_entree.tous_actifs():
                    compte_unites[actif.cle] = donnees_simulation.parc.nombre_unites(actif.cle, annee_anticipee)
                meteo = ambiance[annee_courante][indice_meteo]
                thread_dispatch_annuel = DispatchV0.ThreadDispatchAnnuel(donnees_entree, compte_unites, ambiance, annee_courante, meteo, annee_anticipee)
                liste_threads_dispatch_annuel_ambiance_annee.append(thread_dispatch_annuel)
                thread_dispatch_annuel.start()

            matrice_threads_dispatch_annuel_ambiance.append(liste_threads_dispatch_annuel_ambiance_annee)

        matrice_threads_dispatch_annuel.append(matrice_threads_dispatch_annuel_ambiance)

    for indice_ambiance in range(len(donnees_entree.tableau_ambiances)):
        ambiance = donnees_entree.tableau_ambiances[indice_ambiance]
        for annee_anticipee in range(annee_debut_anticipation, annee_fin_anticipation):
            for indice_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
                matrice_threads_dispatch_annuel[indice_ambiance][annee_anticipee - annee_debut_anticipation][indice_meteo].join()

    matrice_resultats_annuels = []
    for indice_ambiance in range(len(donnees_entree.tableau_ambiances)):
        ambiance = donnees_entree.tableau_ambiances[indice_ambiance]
        matrice_resultats_annuels_ambiance = []

        for annee_anticipee in range(annee_debut_anticipation, annee_fin_anticipation):
            liste_resultats_annuels_ambiance_annee = []

            for indice_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
                resultat_annuel = matrice_threads_dispatch_annuel[indice_ambiance][annee_anticipee - annee_debut_anticipation][indice_meteo].resultat_annuel
                liste_resultats_annuels_ambiance_annee.append(resultat_annuel)

            matrice_resultats_annuels_ambiance.append(liste_resultats_annuels_ambiance_annee)

        matrice_resultats_annuels.append(matrice_resultats_annuels_ambiance)

    return matrice_resultats_annuels

def anticipation_resultats_annuels_parc_exogene(annee_debut_anticipation, annee_fin_anticipation, donnees_entree, donnees_simulation,dico_nb_unites_ambiances_test,writeLP=False,LP_name="LP"):
    """
    Calcule les dispatchs pour les années comprises entre annee_debut_anticipation (incluse) et annee_fin_anticipation (excluse) pour chaque
    ambiance et chaque météo de donnes_entree et renvoie les résultats dans une matrice indexée par
    [ambiance][annee][meteo].

    Parametres
    ----------
    annee_debut_anticipation : int
        première année anticipée
    annee_fin_anticipation : int
        année de fin d'anticipation, non-incluse dans les années anticipées
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    dico_parcs_annee_courante :
        dictionnaire contenant les objets DonneesSimulation.Parc pour chaque ambiance

    Retours
    -------
    list
        matrice indexée par [ambiance][annee][meteo] contenant les instances de DispatchV0.ResultatAnnuel resultant des
        dispatchs sur les ambiances, années et météos correspondantes
    """

    annee_courante = donnees_simulation.annee_courante
    matrice_threads_dispatch_annuel = []
    for indice_ambiance,ambiance in enumerate(donnees_entree.ambiances):
    
        matrice_threads_dispatch_annuel_ambiance = []
        
        for annee_anticipee in range(annee_debut_anticipation, annee_fin_anticipation):

            liste_threads_dispatch_annuel_ambiance_annee = []

            for indice_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
            
                compte_unites = dict()
                
                for actif in donnees_entree.tous_actifs():
                
                    compte_unites[actif.cle] = dico_nb_unites_ambiances_test[ambiance].at[annee_anticipee,actif.cle]

                donnees_dispatch = donnees_entree.ambiances[ambiance][annee_courante]["meteo_%d"%indice_meteo]
                donnees_couts_var = donnees_entree.ambiances[ambiance][annee_courante]["couts_combustibles"]
                
                thread_dispatch_annuel = DispatchV0.ThreadDispatchAnnuel(donnees_entree, compte_unites, donnees_dispatch,donnees_couts_var,annee_courante,annee_anticipee,writeLP,LP_name)
                
                liste_threads_dispatch_annuel_ambiance_annee.append(thread_dispatch_annuel)
                thread_dispatch_annuel.start()

            matrice_threads_dispatch_annuel_ambiance.append(liste_threads_dispatch_annuel_ambiance_annee)

        matrice_threads_dispatch_annuel.append(matrice_threads_dispatch_annuel_ambiance)

    for indice_ambiance,ambiance in enumerate(donnees_entree.ambiances):
        for annee_anticipee in range(annee_debut_anticipation, annee_fin_anticipation):
            for indice_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
                matrice_threads_dispatch_annuel[indice_ambiance][annee_anticipee - annee_debut_anticipation][indice_meteo].join()

    matrice_resultats_annuels = []
    for indice_ambiance,ambiance in enumerate(donnees_entree.ambiances):

        matrice_resultats_annuels_ambiance = []

        for annee_anticipee in range(annee_debut_anticipation, annee_fin_anticipation):
            liste_resultats_annuels_ambiance_annee = []

            for indice_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
                resultat_annuel = matrice_threads_dispatch_annuel[indice_ambiance][annee_anticipee - annee_debut_anticipation][indice_meteo].resultat_annuel
                liste_resultats_annuels_ambiance_annee.append(resultat_annuel)

            matrice_resultats_annuels_ambiance.append(liste_resultats_annuels_ambiance_annee)

        matrice_resultats_annuels.append(matrice_resultats_annuels_ambiance)

    return matrice_resultats_annuels



