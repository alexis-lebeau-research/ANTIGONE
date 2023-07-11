# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import statistics as stat
import sys

from DonneesEntree import *


def calcul_revenu_annuel_hors_contrat(actif, resultat_annuel, donnees_entree):
    """
    Calcule le revenu hors contrat d'une unité de l'actif pour les données annuelles et le résultat annuel donnés.

    Paramètres
    ----------
    actif : DonneesEntree.Actif
        type d'actif auquel appartient l'unité dont on veut calculer le revenu
    resultat_annuel : DispatchV0.ResultatAnnuel
        resultat de dispatch à utiliser
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser

    Retours
    -------
    float
        revenu annuel hors contrat
    """

    annee_courante = resultat_annuel.annee_courante
    annee = resultat_annuel.annee
    df_cv = resultat_annuel.df_cv
    donnees_couts_var = resultat_annuel.donnees_couts_var
    

    cout_variable_actif = 0
    if actif.categorie == "Pilotable":
        cout_variable_actif = df_cv.at[actif.cle,"CV"]
    elif actif.categorie == "ENR":
        cout_variable_actif = actif.cout_variable
    elif actif.categorie == "Stockage":
        cout_variable_actif = actif.cout_variable

    revenu_annuel = np.sum((resultat_annuel.cout_marginal - cout_variable_actif) * resultat_annuel.production_unitaire(actif.cle)) - actif.cout_fixe_maintenance


    if actif.categorie == "Stockage":
        nombre_unites_actif = max(1, resultat_annuel.compte_unites[actif.cle])
        revenu_annuel += - np.sum(resultat_annuel.cout_marginal * resultat_annuel.charge[actif.cle] / nombre_unites_actif)

    if actif.categorie == "ENR":
        revenu_annuel += donnees_couts_var.at["prix_certificats_verts","Annee_%d"%annee] * np.sum(resultat_annuel.production_unitaire(actif.cle))
        if donnees_entree.parametres_simulation.certificats_verts_au_productible:
            nombre_unites_actif = max(1, resultat_annuel.compte_unites[actif.cle])
            revenu_annuel += np.sum(resultat_annuel.ecretement[actif.cle]) * donnees_couts_var.at["prix_certificats_verts","Annee_%d"%annee] / nombre_unites_actif
            
    return revenu_annuel


def calcul_revenu_annuel(unite, annee, resultat_annuel, donnees_entree):
    """
    Calcule le revenu de l'unité pour l'année, les données annuelles et le résultat annuel donnés.

    Paramètres
    ----------
    unite : DonneesSimulation.Unite
        unité dont on veut calculer le revenu
    annee : int
        année à laquelle on veut calculer le revenu
    resultat_annuel : DispatchV0.ResultatAnnuel
        resultat de dispatch à utiliser, il devrait correspondre à l'année données
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser

    Retours
    -------
    float
        revenu annuel
    """

    if not (unite.annee_ouverture <= annee < unite.annee_fermeture):

        return 0

    if not (unite.contrat):
        # si l'unité n'a pas de contrat, le revenu est calculé normalement
        return calcul_revenu_annuel_hors_contrat(unite.actif, resultat_annuel, donnees_entree)
    else:
        return unite.contrat.calcul_revenu_annuel(unite.actif, annee, resultat_annuel, donnees_entree)


def calcul_matrice_revenus_annuels(unite, matrice_resultats_annuels, annee_debut, annee_fin, donnees_entree, donnees_simulation):
    """
    Renvoie une matrice indexée par [ambiance][année][météo] des revenus annuels de l'unité correspondant
    aux resultats annuels de matrice_resultats_annuels pour les années entre annee_debut et annee_fin.

    Si annee_fin se situe au delà de la période couverte par matrice_resultats_annuels,
    le revenu des années supplémentaires sera calculé à partir des résultats de la dernière année fournie.

    Paramètres
    ----------
    unite : DonneesSimulation.Unite
        unité dont on veut calculer les revenus
    matrice_resultats_annuels : list
        matrice indexée par [ambiance][année][météo] contenant les resultats de dispatchs à utiliser
    annee_debut : int
        première année pour laquelle on veut connaître le revenu, on suppose qu'elle coïncide avec l'année 0 de
        matrice_resultats_annuels
    annee_fin : int
        dernière année, non incluse pour le calcul
    donnees_entree : DonneesEntree.DonneesEntree
        données de simulation à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser

    Retours
    -------
    list
        matrice de revenus annuels indexée par [ambiance][année][météo]
    """
    
    matrice_revenus_annuels = []
    for indice_ambiance in range(len(matrice_resultats_annuels)):
        matrice_revenus_annuels_ambiance = []
        resultats_annuels_ambiance = matrice_resultats_annuels[indice_ambiance]
        for annee in range(annee_debut, annee_fin):
        
            liste_revenus_annuels_ambiance_annee = []
            
            if(annee - annee_debut < len(resultats_annuels_ambiance)):

                resultats_annuels_ambiance_annee = resultats_annuels_ambiance[annee - annee_debut]
                annee_donnees = annee
                
            else : 
                resultats_annuels_ambiance_annee = resultats_annuels_ambiance[-1]
                annee_donnees = annee_debut + len(resultats_annuels_ambiance) - 1
            
                
            for indice_meteo in range(len(resultats_annuels_ambiance_annee)):
            
                resultat_annuel = resultats_annuels_ambiance_annee[indice_meteo]
                
                revenu_annuel = calcul_revenu_annuel(unite, annee_donnees, resultat_annuel, donnees_entree)
                
                liste_revenus_annuels_ambiance_annee.append(revenu_annuel)

            matrice_revenus_annuels_ambiance.append(liste_revenus_annuels_ambiance_annee)
        matrice_revenus_annuels.append(matrice_revenus_annuels_ambiance)

    return matrice_revenus_annuels
    
    

def calcul_revenu_annuel_hors_contrat_sans_CF(actif, resultat_annuel, donnees_entree):
    """
    Calcule le revenu hors contrat d'une unité de l'actif pour les données annuelles et le résultat annuel donnés.

    Paramètres
    ----------
    actif : DonneesEntree.Actif
        type d'actif auquel appartient l'unité dont on veut calculer le revenu
    resultat_annuel : DispatchV0.ResultatAnnuel
        resultat de dispatch à utiliser
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser

    Retours
    -------
    float
        revenu annuel hors contrat
    """

    annee_courante = resultat_annuel.annee_courante
    annee = resultat_annuel.annee
    df_cv = resultat_annuel.df_cv
    donnees_couts_var = resultat_annuel.donnees_couts_var
    

    cout_variable_actif = 0
    if actif.categorie == "Pilotable":
        cout_variable_actif = df_cv.at[actif.cle,"CV"]
    elif actif.categorie == "ENR":
        cout_variable_actif = actif.cout_variable
    elif actif.categorie == "Stockage":
        cout_variable_actif = actif.cout_variable


    revenu_annuel = np.sum((resultat_annuel.cout_marginal - cout_variable_actif) * resultat_annuel.production_unitaire(actif.cle))



    if actif.categorie == "Stockage":
        nombre_unites_actif = max(1, resultat_annuel.compte_unites[actif.cle])
        revenu_annuel += - np.sum(resultat_annuel.cout_marginal * resultat_annuel.charge[actif.cle] / nombre_unites_actif)

    if actif.categorie == "ENR":
        revenu_annuel += donnees_couts_var.at["prix_certificats_verts","Annee_%d"%annee] * np.sum(resultat_annuel.production_unitaire(actif.cle))
        if donnees_entree.parametres_simulation.certificats_verts_au_productible:
            nombre_unites_actif = max(1, resultat_annuel.compte_unites[actif.cle])
            revenu_annuel += np.sum(resultat_annuel.ecretement[actif.cle]) * donnees_couts_var.at["prix_certificats_verts","Annee_%d"%annee]/ nombre_unites_actif
            
    return revenu_annuel


def calcul_revenu_annuel_sans_CF(unite, annee_donnee, annee_revenu, resultat_annuel, donnees_entree):
    """
    Calcule le revenu de l'unité pour l'année, les données annuelles et le résultat annuel donnés.

    Paramètres
    ----------
    unite : DonneesSimulation.Unite
        unité dont on veut calculer le revenu
    annee_donnee : int
        année à laquelle correspond la donnée
    annee_revenu : int
        année à laquelle on veut calculer le revenu
    resultat_annuel : DispatchV0.ResultatAnnuel
        resultat de dispatch à utiliser, il devrait correspondre à l'année données
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser

    Retours
    -------
    float
        revenu annuel
    """

    #if not (unite.annee_ouverture <= annee_revenu < unite.annee_fermeture):
    if not (unite.annee_ouverture <= annee_revenu < unite.annee_fermeture):
        return 0

    if not (unite.contrat):
        # si l'unité n'a pas de contrat, le revenu est calculé normalement
        return calcul_revenu_annuel_hors_contrat_sans_CF(unite.actif, resultat_annuel, donnees_entree)
    else:
        return unite.contrat.calcul_revenu_annuel_sans_CF(unite.actif, annee_donnee, resultat_annuel, donnees_entree)


def calcul_matrice_revenus_annuels_sans_CF(unite, matrice_resultats_annuels, annee_debut, annee_fin, donnees_entree, donnees_simulation):
    """
    Renvoie une matrice indexée par [ambiance][année][météo] des revenus annuels de l'unité correspondant
    aux resultats annuels de matrice_resultats_annuels pour les années entre annee_debut et annee_fin.

    Si annee_fin se situe au delà de la période couverte par matrice_resultats_annuels,
    le revenu des années supplémentaires sera calculé à partir des résultats de la dernière année fournie.

    Paramètres
    ----------
    unite : DonneesSimulation.Unite
        unité dont on veut calculer les revenus
    matrice_resultats_annuels : list
        matrice indexée par [ambiance][année][météo] contenant les resultats de dispatchs à utiliser
    annee_debut : int
        première année pour laquelle on veut connaître le revenu, on suppose qu'elle coïncide avec l'année 0 de
        matrice_resultats_annuels
    annee_fin : int
        dernière année, non incluse pour le calcul
    donnees_entree : DonneesEntree.DonneesEntree
        données de simulation à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser

    Retours
    -------
    list
        matrice de revenus annuels indexée par [ambiance][année][météo]
    """
    
    matrice_revenus_annuels = []
    for indice_ambiance in range(len(matrice_resultats_annuels)):
        matrice_revenus_annuels_ambiance = []
        resultats_annuels_ambiance = matrice_resultats_annuels[indice_ambiance]
        for annee in range(annee_debut, annee_fin):
        
            liste_revenus_annuels_ambiance_annee = []
            
            if(annee - annee_debut < len(resultats_annuels_ambiance)):

                resultats_annuels_ambiance_annee = resultats_annuels_ambiance[annee - annee_debut]
                annee_donnees = annee
                annee_revenu = annee
                
            else : 
                resultats_annuels_ambiance_annee = resultats_annuels_ambiance[-1]
                annee_donnees = annee_debut + len(resultats_annuels_ambiance) - 1
                annee_revenu = annee
            
                
            for indice_meteo in range(len(resultats_annuels_ambiance_annee)):
            
                resultat_annuel = resultats_annuels_ambiance_annee[indice_meteo]
                
                revenu_annuel = calcul_revenu_annuel_sans_CF(unite, annee_donnees, annee_revenu, resultat_annuel, donnees_entree)
                
                liste_revenus_annuels_ambiance_annee.append(revenu_annuel)

            matrice_revenus_annuels_ambiance.append(liste_revenus_annuels_ambiance_annee)
        matrice_revenus_annuels.append(matrice_revenus_annuels_ambiance)

    return matrice_revenus_annuels


def calcul_VAN_equivalente(matrice_flux_financiers, taux_actualisation, donnees_entree, investissement_initial, nbAnneeNPV):
    """
    Calcule la VAN équivalente correspondant aux flux financiers donnés.

    Les flux financiers sont actualisés dès l'année actuelle, le seul terme d'ordre 0 est l'investissement initial.

    Paramètres
    ----------
    matrice_flux_financiers : list
        matrice indexée par [ambiance][année][météo] contenant les flux financiers à utiliser
    taux_actualisation : float
        taux d'actualisation à utiliser
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    investissement_initial : float
        investissement initial
    duree_construction : int
        nombre d'années séparant la date de l'investissement initial de l'année 0 des flux financiers

    Retours
    -------
    float
        VAN équivalente
    """
    horizon_prevision = donnees_entree.parametres_simulation.horizon_prevision
    parametre_VAN_equivalente = donnees_entree.parametres_simulation.VAN_equivalente
    liste_VAN_possibles = []
    
    df_ponderation = donnees_entree.df_parametres_ponderation
    
    if (parametre_VAN_equivalente == "moyenne_ponderee") or (parametre_VAN_equivalente == "equivalent_certain" and donnees_entree.parametres_simulation.coefficient_risque == 0) : 
        somme_VAN_equivalente = 0
        for indice_ambiance in range(len(matrice_flux_financiers)):
            VAN_equivalente_ambiance = -investissement_initial
            
            for annee in range(nbAnneeNPV) : 
                for indice_meteo in range(len(matrice_flux_financiers[indice_ambiance][annee])):
                    flux_financier = matrice_flux_financiers[indice_ambiance][annee][indice_meteo]
                    VAN_equivalente_ambiance += (flux_financier * df_ponderation.at[indice_meteo, "value"]) / ((1 + taux_actualisation)**(annee))
              
            somme_VAN_equivalente += VAN_equivalente_ambiance            
            liste_VAN_possibles.append(VAN_equivalente_ambiance)
        
        VAN_equivalente = somme_VAN_equivalente / len(matrice_flux_financiers)  
        #annuite_equivalente_VAN = VAN_equivalente / nbAnneeNPV
        VAN_annualisee = VAN_equivalente * (taux_actualisation / (1 + taux_actualisation)) / ( 1 - (1 + taux_actualisation)**(-nbAnneeNPV))
        prime_risque = 0
        
        return VAN_equivalente, VAN_annualisee, prime_risque, liste_VAN_possibles
            
    if parametre_VAN_equivalente == "equivalent_certain" : 
        liste_EC_possibles = []
        alpha = donnees_entree.parametres_simulation.coefficient_risque
    
        somme_EC = 0
        annuite_equivalente_VAN = 0
        annuite_equivalente_EC = 0
        moyenne_ambiance_prime_risque = 0
        
        for indice_ambiance in range(len(matrice_flux_financiers)):
            EC_ambiance = -investissement_initial
            
            for annee in range(nbAnneeNPV) :
            
                liste_flux_annee =  matrice_flux_financiers[indice_ambiance][annee]
                esp_VAN_annee = (liste_flux_annee * df_ponderation.T).sum(axis=1).value
                
                #annuite_equivalente_VAN += esp_VAN_annee / (nbAnneeNPV * len(matrice_flux_financiers))
                
                esp_utility = 0
                
                if esp_VAN_annee != 0 : 
                
                    for indice_meteo in range(len(liste_flux_annee)):
                        
                        flux_financier = liste_flux_annee[indice_meteo] 
                        utility_flux_financier =  1 - np.exp(-alpha * (flux_financier/esp_VAN_annee))
                        esp_utility += utility_flux_financier * df_ponderation.at[indice_meteo, "value"]
                        
                    equivalent_certain = -np.log(1-esp_utility)*esp_VAN_annee/alpha
                    #annuite_equivalente_EC += equivalent_certain / (nbAnneeNPV * len(matrice_flux_financiers))
                    
                    EC_ambiance += equivalent_certain / ((1 + taux_actualisation)**(annee))
                    moyenne_ambiance_prime_risque += (esp_VAN_annee - equivalent_certain) / (len(matrice_flux_financiers))
                     
            somme_EC += EC_ambiance            
            liste_EC_possibles.append(EC_ambiance)
        
        EC = somme_EC / len(matrice_flux_financiers)  

        EC_annualise = EC * (taux_actualisation/( 1 + taux_actualisation)) / ( 1 - (1 + taux_actualisation)**(-nbAnneeNPV)) 
        prime_risque = moyenne_ambiance_prime_risque
        
        return EC, EC_annualise, prime_risque, liste_EC_possibles
        
    
    for indice_ambiance in range(len(matrice_flux_financiers)):
        liste_sommes_partielles = [-investissement_initial]

        for annee in range(nbAnneeNPV):
            nouvelle_liste_sommes_partielles = []
            for somme_partielle in liste_sommes_partielles:
                for indice_meteo in range(len(matrice_flux_financiers[indice_ambiance][annee])):
                    flux_financier = matrice_flux_financiers[indice_ambiance][annee][indice_meteo]
                    nouvelle_somme_partielle = somme_partielle + flux_financier/(1 + taux_actualisation)**(annee)
                    nouvelle_liste_sommes_partielles.append(nouvelle_somme_partielle)
            liste_sommes_partielles = nouvelle_liste_sommes_partielles


        liste_VAN_possibles_ambiance = liste_sommes_partielles
        liste_VAN_possibles += liste_VAN_possibles_ambiance


    
    # la VAN équivalente est déterminée à partir de la liste des VAN possibles en appliquant
    # une fonction choisie par l'utilisateur
    VAN_equivalente = 0

    if parametre_VAN_equivalente == "moyenne":
        VAN_equivalente = stat.mean(liste_VAN_possibles)
    elif parametre_VAN_equivalente == "mediane":
        VAN_equivalente = stat.median(liste_VAN_possibles)
    elif parametre_VAN_equivalente == "minimum":
        VAN_equivalente = min(liste_VAN_possibles)
    elif parametre_VAN_equivalente == "maximum":
        VAN_equivalente = max(liste_VAN_possibles)
    elif parametre_VAN_equivalente == "quantile":
        VAN_equivalente = np.quantile(liste_VAN_possibles, donnees_entree.parametres_simulation.quantile_meteo)
        
    else:
        raise ValueError("Paramètre VAN_equiv %s non reconnu"%parametre_VAN_equivalente)

    VAN_annualisee = VAN_equivalente * (taux_actualisation / (1 + taux_actualisation)) / ( 1 - (1 + taux_actualisation)**(-nbAnneeNPV))
    prime_risque = 0

    return VAN_equivalente, VAN_annualisee, prime_risque, liste_VAN_possibles


def calcul_taux_rentabilite_interne_equivalent(matrice_flux_financiers, donnees_entree, investissement_initial = 0, duree_construction = 0):
    """
        Calcule le TRI équivalent correspondant aux flux financiers donnés.

        Les flux financiers sont actualisés dès l'année actuelle, le seul terme d'ordre 0 est l'investissement initial.

        Paramètres
        ----------
        matrice_flux_financiers : list
            matrice indexée par [ambiance][année][météo] contenant les flux financiers à utiliser
        donnees_entree : DonneesEntree.DonneesEntree
            données d'entrée à utiliser. Attention, éviter d'utiliser le TRI avec donnees_entree.parametres_simulation.VAN_equivalente == "moyenne".
        investissement_initial : float
            investissement initial
        duree_construction : int
            nombre d'années séparant la date de l'investissement initial de l'année 0 des flux financiers

        Retours
        -------
        float
            TRI équivalent
        """
    horizon_prevision = donnees_entree.parametres_simulation.horizon_prevision
    parametre_VAN_equivalente = donnees_entree.parametres_simulation.VAN_equivalente

    liste_flux_financiers_possibles = []
    for indice_ambiance in range(len(matrice_flux_financiers)):
        liste_flux_financiers_partiels = [[-investissement_initial]+[0]*duree_construction]

        # pour les années couvertes par l'horizon de prévision, chaque scénario météo est envisagé
        # attention : le nombre de scénarios augmente exponentiellement avec l'horizon de simulation
        for annee in range(duree_construction,min(horizon_prevision, len(matrice_flux_financiers[indice_ambiance]) + duree_construction)):
            nouvelle_liste_flux_financiers_partiels = []
            for flux_financiers_partiels in liste_flux_financiers_partiels:
                for indice_meteo in range(len(matrice_flux_financiers[indice_ambiance][annee - duree_construction])):
                    flux_financier = matrice_flux_financiers[indice_ambiance][annee - duree_construction][indice_meteo]
                    nouveaux_flux_financiers_partiels = flux_financiers_partiels + [flux_financier]
                    nouvelle_liste_flux_financiers_partiels.append(nouveaux_flux_financiers_partiels)
            liste_flux_financiers_partiels = nouvelle_liste_flux_financiers_partiels

        # au delà de l'horizon de simulation, on ajoute la somme correspondant à la réalisation d'une seule météo
        # sur toutes les années restantes
        annee_debut_extrapolation = horizon_prevision
        annee_fin_extrapolation = max(horizon_prevision, len(matrice_flux_financiers[indice_ambiance]) + duree_construction)
        if (annee_debut_extrapolation < annee_fin_extrapolation):
            liste_flux_extrapoles = []
            for indice_meteo in range(len(matrice_flux_financiers[indice_ambiance][annee_debut_extrapolation - duree_construction])):
                flux_financier = matrice_flux_financiers[indice_ambiance][annee_debut_extrapolation - duree_construction][indice_meteo]
                liste_flux_extrapoles.append([flux_financier])
            for annee in range(annee_debut_extrapolation + 1, annee_fin_extrapolation):
                for indice_meteo in range(len(matrice_flux_financiers[indice_ambiance][annee - duree_construction])):
                    flux_financier = matrice_flux_financiers[indice_ambiance][annee - duree_construction][indice_meteo]
                    liste_flux_extrapoles[indice_meteo].append(flux_financier)

            # ajout des termes extrapoles à la fin des sommes partielles
            nouvelle_liste_flux_financiers_partiels = []
            for flux_financiers_partiels in liste_flux_financiers_partiels:
                for flux_extrapoles in liste_flux_extrapoles:
                    nouvelle_liste_flux_financiers_partiels.append(flux_financiers_partiels + flux_extrapoles)
            liste_flux_financiers_partiels = nouvelle_liste_flux_financiers_partiels

        liste_flux_financiers_possibles_ambiance = liste_flux_financiers_partiels
        liste_flux_financiers_possibles += liste_flux_financiers_possibles_ambiance

    liste_taux_rentabilite_interne_possibles = []
    for flux_financiers in liste_flux_financiers_possibles:
        taux_rentabilite_interne = np.irr(flux_financiers)
        if np.isnan(taux_rentabilite_interne):
            taux_rentabilite_interne = float('-inf')
        liste_taux_rentabilite_interne_possibles.append(taux_rentabilite_interne)

    # le TRI équivalent est déterminé à partir de la liste des TRI possibles en appliquant
    # une fonction choisie par l'utilisateur
    taux_rentabilite_interne_equivalent = 0
    if parametre_VAN_equivalente == "moyenne":
        taux_rentabilite_interne_equivalent = stat.mean(liste_taux_rentabilite_interne_possibles)
    elif parametre_VAN_equivalente == "mediane":
        taux_rentabilite_interne_equivalent = stat.median(liste_taux_rentabilite_interne_possibles)
    elif parametre_VAN_equivalente == "minimum":
        taux_rentabilite_interne_equivalent = min(liste_taux_rentabilite_interne_possibles)
    elif parametre_VAN_equivalente == "maximum":
        taux_rentabilite_interne_equivalent = max(liste_taux_rentabilite_interne_possibles)
    elif parametre_VAN_equivalente == "quantile":
        taux_rentabilite_interne_equivalent = np.quantile(liste_taux_rentabilite_interne_possibles, donnees_entree.parametres_simulation.quantile_meteo)
    else:
        raise ValueError("Paramètre VAN_equiv %s non reconnu" % parametre_VAN_equivalente)

    return taux_rentabilite_interne_equivalent


def calcul_investissement_annualise(actif, annee_investissement):
    """
    Calcule le coût d'investissement annualisé d'une unité de l'actif donné.

    Paramètres
    ----------
    actif : DonneesEntree.Actif
        type d'actif
    annee_investissement : int
        année à laquelle débute la construction

    Retours
    -------
    float
        coût d'investissement annualisé
    """

    return actif.cout_fixe_construction(annee_investissement) * (actif.taux_actualisation / (1 + actif.taux_actualisation)) / (1 - 1 / (1 + actif.taux_actualisation)**actif.duree_vie)

def calcul_investissement_IDC_annualise(actif, annee_investissement):
    """
    Calcule le coût d'investissement IDC annualisé d'une unité de l'actif donné.

    Paramètres
    ----------
    actif : DonneesEntree.Actif
        type d'actif
    annee_investissement : int
        année à laquelle débute la construction

    Retours
    -------
    float
        coût d'investissement IDC annualisé
    """

    return calcul_investissement_annualise(actif, annee_investissement) * (1 + actif.taux_actualisation)**actif.duree_construction


def calcul_indice_profitabilite(actif, VAN_equivalente_par_unite, investissement_initial):
    """
    Calcule l'indice de profitabilité d'une unité de l'actif ayant la VAN équivalente donnée.

    Paramètres
    ----------
    actif : DonneesEntree.Actif
        type d'actif
    VAN_equivalente_par_unite : float
        VAN équivalente pour une unité de l'actif
    investissement_initial : float
        investissement initial

    Retours
    -------
    float
        indice de profitabilité
    """

    if(investissement_initial == 0):
        if(VAN_equivalente_par_unite>0):
            return float('inf')
        elif(VAN_equivalente_par_unite<0):
            return float('-inf')
        else:
            return 1

    indice_profitabilite = 1 + VAN_equivalente_par_unite / investissement_initial
    return indice_profitabilite


def calcul_VAN_par_MW(actif, VAN_equivalente_par_unite):
    """
    Calcule la VAN par MW d'une unité de l'actif ayant la VAN équivalente donnée.

    Paramètres
    ----------
    actif : DonneesEntree.Actif
        type d'actif
    VAN_equivalente_par_unite : float
        VAN équivalente pour une unité de l'actif

    Retours
    -------
    float
        VAN par MW
    """

    capacite = 1
    if actif.categorie == "Stockage":
        capacite = actif.puissance_nominale_decharge
    elif actif.categorie == "ENR":
        capacite = actif.puissance_reference
    elif actif.categorie == "Pilotable":
        capacite = actif.puissance_nominale
    VAN_par_MW = VAN_equivalente_par_unite / capacite
    return VAN_par_MW












