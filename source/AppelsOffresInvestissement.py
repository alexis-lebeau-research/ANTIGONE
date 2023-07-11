# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import DonneesSimulation
import Contrats
import Anticipation
import Ecriture
import Lecture

import numpy as np

import sys
import os

class AppelOffresInvestissement:
    """
    Cette classe représente un appel d'offres d'investissement.

    Attributs
    ---------
    actif : DonneesEntree.Actif
        type d'actif dont des unités vont être construites
    nombre_unites_demantelees : int
        nombre d'unités dont la construction a été programmée
    contrat : Contrats.Contrat
        contrat dont bénéficient les unités
    """
    def __init__(self, actif, nombre_unites_actif, contrat):
        self.actif = actif
        self.nombre_unites_actif = nombre_unites_actif
        self.contrat = contrat

class RapportAppelsOffresInvestissement:
    """
    Cette classe synthétise les informations d'une séquence d'appels d'offres d'investissement.

    Attributs
    ---------
    argent_restant : float
        part du budget consacré aux appels d'offres d'investissement qui n'a pas été dépensée
    puissance_restante : float
        part du budget en puissance consacré aux appels d'offres d'investissement qui n'a pas été dépensée
    liste_appels_offres_investissement : list
        liste des appels d'offre émis au cours de la séquence
    """
    def __init__(self, argent_restant, puissance_restante, liste_appels_offres_investissement):
        self.argent_restant = argent_restant
        self.puissance_restante = puissance_restante
        self.liste_appels_offres_investissement = liste_appels_offres_investissement

    def __getitem__(self, indice_appel_offres):
        return self.liste_appels_offres_investissement[indice_appel_offres]

def compute_auction_volume(donnees_entree,donnees_simulation,actif,annee_anticipee, capacite_investissement_argent, capacite_investissement_puissance):

    # calcul du nombre maximum d'unités de l'actif pouvant être construites, initialisé à plus infini
    nombre_max_unites_investies = np.float("inf")

    puissance = 0
    if actif.categorie == "Stockage":
        puissance = actif.puissance_nominale_decharge
    elif actif.categorie == "Pilotable":
        puissance = actif.puissance_nominale
    elif actif.categorie == "ENR":
        puissance = actif.puissance_reference

    # non-dépassement de la limite de construction annuelle
    if not (actif.limite_construction_annuelle == 'aucune'):
        nombre_unites_deja_ouvertes = donnees_simulation.parc.nombre_unites_ouvertes(actif.cle, annee_courante + actif.duree_construction)
        nombre_max_unites_investies = np.min([nombre_max_unites_investies, np.max([0, actif.limite_construction_annuelle - nombre_unites_deja_ouvertes])])

    # non-dépassement de la capacité d'investissement en argent

    cout_fixe_construction_actif = actif.cout_fixe_construction(annee_anticipee - actif.duree_construction)
        
    if not capacite_investissement_argent == np.inf :
        if cout_fixe_construction_actif > 0:
            nombre_max_unites_investies = min(nombre_max_unites_investies, np.int(capacite_investissement_argent / cout_fixe_construction_actif))

    # non-dépassement de la capacité d'investissement en puissance
    
    if not capacite_investissement_puissance == np.inf :
        if puissance > 0:
            nombre_max_unites_investies = min(nombre_max_unites_investies, int(capacite_investissement_puissance / puissance))

    # non-dépassement du gisement sur toute la durée de vie de l'actif potentiellement construit
    # uniquement vérifié s'il est possible d'investir dans au moins une unité avec les capacités restantes
    if (nombre_max_unites_investies > 0) and (not actif.gisement_max == "aucun") and puissance > 0:
        nombre_max_unites_total = int(actif.gisement_max / puissance)
        for annee_fonctionnement in range(annee_anticipee, min(annee_anticipee + actif.duree_vie, horizon_simulation)):
            nombre_max_unites_investies = min(nombre_max_unites_investies, nombre_max_unites_total - donnees_simulation.parc.nombre_unites(actif.cle, annee_fonctionnement))

    # calcul du nombre d'unites manquantes pour atteindre la cible
    nombre_unites_cible = donnees_entree.mix_cible[actif.cle][annee_anticipee]
    nombre_unites_manquantes = max(0, nombre_unites_cible - donnees_simulation.parc.nombre_unites(actif.cle, annee_anticipee))

    # calcul du nombre de contrats qui seront émis pour ce type d'actif
    nombre_unites_actif = min(nombre_unites_manquantes, nombre_max_unites_investies)
    
    
    capacite_investissement_argent -= nombre_unites_actif * cout_fixe_construction_actif
    capacite_investissement_puissance -= nombre_unites_actif * puissance

    return nombre_unites_actif,capacite_investissement_argent,capacite_investissement_puissance
    
def sequence_appels_offres_investissement(donnees_entree, donnees_simulation):
    """
    Cette fonction effectue la séquence d'appels d'offres d'investissement annuelle et renvoie le rapport associé.

    Paramètres
    ----------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser, ce paramètre est modifié par la fonction

    Retours
    -------
    RapportAppelsOffresInvestissement
        rapport de la séquence d'appels d'offres d'investissement
    """
    
    
    annee_courante = donnees_simulation.annee_courante
    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation
    horizon_prevision = donnees_entree.parametres_simulation.horizon_prevision
    idx_fin = (donnees_entree.parametres_simulation.horizon_simulation-1)


    
    df_param_ao = donnees_entree.df_param_ao
    
    cond_techno_eligibile = df_param_ao["sequence_investissement"] == True
    df_param_ao = df_param_ao[cond_techno_eligibile]
        
    if len(df_param_ao.index) == 0 :
        print("Pas de techno eligibiles aux AO ouverture")
        return RapportAppelsOffresInvestissement(0, 0, [])
    
    df_param_ao = df_param_ao.sort_values(by="preseance")
    
    dict_actif_eligible = {}
    
    for nom_actif in df_param_ao.index :
        ordre_preseance = df_param_ao.at[nom_actif,"preseance"]
        for actif in donnees_entree.tous_actifs():
            if nom_actif == actif.cle : 
                dict_actif_eligible[ordre_preseance] = actif
                

    liste_appels_offres = []
    
    # realisation de l'anticipation
    # calcul de la date de fin (maximum dont on a besoin pour tous les AO)
    
    min_horizon_appels_offres = df_param_ao["horizon_appels_offres"].min()

    if(annee_courante == 0):
        annee_debut_anticipation = 0
    else :
        annee_debut_anticipation = annee_courante + min_horizon_appels_offres
        
    fin_anticipation = annee_courante + min_horizon_appels_offres 
    
    for round_ao in dict_actif_eligible :
        actif = dict_actif_eligible[round_ao]
        
        horizon_appels_offres = df_param_ao.at[actif.cle,"horizon_appels_offres"]
        
        fin_anticipation_actif = np.min([annee_courante+horizon_appels_offres + actif.duree_vie,
                                annee_courante+horizon_prevision,
                                horizon_simulation]).astype(int)
                                
        fin_anticipation = np.max([fin_anticipation,fin_anticipation_actif])

    # mise en cohérence du parc si besoin et realisation de l'anticipation
    
    df_nb_unites_parc_reel = donnees_simulation.parc.get_df_nb_unites().loc[0:idx_fin]

    nom_fic = "DF_PR_InvestAO_%s.csv"%(str(annee_courante))    
    path_df_parc_reel = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
    df_nb_unites_parc_reel.to_csv(path_df_parc_reel,sep=";")


    if donnees_entree.parametres_simulation.anticipation_parc_exogene :
        
        dico_parcs_anticipes_ao = donnees_entree.get_parc_anticipation()
        
        dico_df_nb_unites_ambiances = donnees_entree.mise_en_coherence_parc(annee_courante,
                                                                            dico_parcs_anticipes_ao,
                                                                            donnees_simulation.parc,
                                                                            add_current_investment=True,
                                                                            add_current_divestment=True)
                                                                                
        for ambiance in donnees_entree.ambiances :
        
            nom_fic = "DF_PA_%s_InvestAO_%s.csv"%(ambiance,str(annee_courante))    
            path_df_parc_reel = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
            dico_df_nb_unites_ambiances[ambiance].to_csv(path_df_parc_reel,sep=";")


        print("realisation d'une anticiation entre %s et %s"%(annee_debut_anticipation,fin_anticipation-1))

        matrice_resultats_annuels = Anticipation.anticipation_resultats_annuels_parc_exogene(annee_debut_anticipation, fin_anticipation, donnees_entree, donnees_simulation,dico_df_nb_unites_ambiances,True,"AO")

    else : 

        matrice_resultats_annuels = Anticipation.anticipation_resultats_annuels(annee_debut_anticipation, fin_anticipation, donnees_entree, donnees_simulation)


    Ecriture.ecriture_dispatch_CFD(matrice_resultats_annuels,donnees_entree,donnees_simulation,annee_courante)

    # realisation des AO

    
    for round_ao in dict_actif_eligible :
    
        actif = dict_actif_eligible[round_ao]

        horizon_appels_offres = df_param_ao.at[actif.cle,"horizon_appels_offres"]
        capacite_investissement_argent = df_param_ao.at[actif.cle,"budget_annuel_investissement"]
        capacite_investissement_puissance = df_param_ao.at[actif.cle,"capacite_maximale_investissement"]

        if(annee_courante == 0):
            # à l'année 0, des appels d'offre sont émis pour toutes les années jusqu'à l'horizon de prévision
            for annee_anticipee in range(horizon_appels_offres + 1):
            

                print("lancement d'une sequence d'AO pour la techno %s pour l'annee %s"%(actif.cle, annee_anticipee))
                capacite_investissement_argent, capacite_investissement_puissance, liste_appels_offres = lancement_annuel_appels_offres_investissement(donnees_entree, donnees_simulation, annee_anticipee, actif, capacite_investissement_argent, capacite_investissement_puissance, liste_appels_offres,matrice_resultats_annuels)
                
        else:
            # pour les autres années, les appels d'offre ne sont émis que pour la dernière année de l'horizon de prévision

            annee_anticipee = annee_courante + horizon_appels_offres
            print("lancement d'une sequence d'AO pour la techno %s pour l'annee %s"%(actif.cle, annee_anticipee))
            capacite_investissement_argent, capacite_investissement_puissance, liste_appels_offres = lancement_annuel_appels_offres_investissement(donnees_entree, donnees_simulation, annee_anticipee, actif, capacite_investissement_argent, capacite_investissement_puissance, liste_appels_offres,matrice_resultats_annuels)



    

    rapport_appels_offres_investissement = RapportAppelsOffresInvestissement(capacite_investissement_argent, capacite_investissement_puissance, liste_appels_offres)
    return rapport_appels_offres_investissement


# revoir éventuellement la structure des fonctions
def lancement_annuel_appels_offres_investissement(donnees_entree, donnees_simulation, annee_anticipee, actif, capacite_investissement_argent, capacite_investissement_puissance, liste_appels_offres,matrice_resultats_annuels):
    """
    Effectue les appels d'offres d'investissement pour construire des unités qui ouvriront à une année donnée.

    La fonction émet des appels d'offres pour des unités qui commenceront à fonctionner à l'année correspondant à
    l'argument annee_anticipee et fait évoluer en conséquence la liste des appels d'offres ainsi que les
    capacités d'investissement en argent et en puissance. Elle peut être appelée plusieurs fois en une même séquence
    d'appels d'offres si elle couvre plusieurs années futures.

    Attributs
    ---------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser, ce paramètre est modifié par la fonction
    annee_anticipee : int
        année à laquelle on envisage d'ouvrir des unités
    liste_candidats_appels_offres_par_preseance : list
        liste des types d'actifs triés par ordre de préséance décroissante, ceux de préséance nulle étant exclus
    capacite_investissement_argent : float
        part du budget en argent consacré aux appels d'offre d'investissement encore disponible
    capacite_investissement_puissance : float
        part du budget en puissance consacré aux appels d'offre d'investissement encore disponible
    liste_appels_offres : list
        liste des appels d'offres déjà émis

    Retours
    -------
    float
        capacité d'investissement en argent restante
    float
        capacité d'investissement en pluissance restante
    list
        liste des appels d'offres
    """

    annee_courante = donnees_simulation.annee_courante
    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation
    horizon_prevision = donnees_entree.parametres_simulation.horizon_prevision
    idx_fin = (donnees_entree.parametres_simulation.horizon_simulation-1)
    
    nombre_unites_actif,capacite_investissement_argent,capacite_investissement_puissance = compute_auction_volume(donnees_entree,donnees_simulation,actif,annee_anticipee, capacite_investissement_argent, capacite_investissement_puissance)
                
    
    if nombre_unites_actif == 0 : 
        return capacite_investissement_argent, capacite_investissement_puissance, liste_appels_offres


    idx = donnees_simulation.df_resume.index.max()+1
    donnees_simulation.df_resume.at[idx,"step"] = "LTC_new_for_%d_%s"%(nombre_unites_actif,actif.cle)
    donnees_simulation.df_resume.at[idx,"module"] = "InvestAO"
    donnees_simulation.df_resume.at[idx,"year"] = annee_courante
    donnees_simulation.df_resume.at[idx,"tech"] = actif.cle
    
    type_contrat = donnees_entree.df_param_ao.at[actif.cle,"type_contrat"]

    if(type_contrat == "contrat_parfait"):
        # calcul du montant de la rémunération par MWh du contrat
        LCOE = Contrats.ContratParfait.calcul_LCOE(actif, annee_courante, donnees_entree)

        contrat = Contrats.ContratParfait(LCOE, annee_courante, annee_anticipee, annee_anticipee + actif.duree_vie)

    elif(type_contrat == "contrat_pour_difference"):
        # calcul du montant de la rémunération par MWh du contrat
        # en se basant sur les estimations pour l'ajout d'une unique unité de l'actif à l'année anticipée

        duree_contrat = Contrats.ContratPourDifference.duree                   
                                
        
        ### Ecriture des résultats EOD
        
        
        prix_contractuel = Contrats.ContratPourDifference.calcul_prix_annulation_VAN(actif, matrice_resultats_annuels, annee_anticipee, donnees_entree, donnees_simulation)

        donnees_simulation.parc.annule_tests()


        volume_contractuel = donnees_entree.df_param_cfd.at[actif.cle,"volume_contractuel"]
        contrat = Contrats.ContratPourDifference(volume_contractuel, prix_contractuel, annee_courante, annee_anticipee, annee_anticipee + duree_contrat)


    else:
        raise ValueError("Type de contrat %s non reconnu"%type_contrat)


    type_contrat = contrat.categorie

    # des unités de l'actif sont ajoutées au parc de sorte à être construites à l'année anticipée
    print("Emission d'un %s pour %d unités de %s pour l'annee %d" % (type_contrat, nombre_unites_actif, actif.cle, annee_anticipee))
    for indice_unite_sous_contrat in range(int(nombre_unites_actif)):
        unite_sous_contrat = DonneesSimulation.Unite(actif, annee_anticipee, annee_anticipee + actif.duree_vie, contrat)
        donnees_simulation.parc.ajout_unite(unite_sous_contrat)

    appel_offre = AppelOffresInvestissement(actif, nombre_unites_actif, contrat)

    liste_appels_offres.append(appel_offre)

    return capacite_investissement_argent, capacite_investissement_puissance, liste_appels_offres
