# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import os

import IndicateursEconomiques
import Anticipation
import Ecriture
import Lecture
import DonneesSimulation

import numpy as np

class AppelOffresDemantelement:
    """
    Cette classe représente un appel d'offres de démantèlement.

    Attributs
    ---------
    actif : DonneesEntree.Actif
        type d'actif dont des unités ont été démantelées
    nombre_unites_demantelees : int
        nombre d'unités dont la fermeture a été demandée
    prix : float
        coût total des compensations versées par l'agence de régulation pour fermer les unités
    """
    def __init__(self, actif, nombre_unites_actif, prix):
        self.actif = actif
        self.nombre_unites_actif = nombre_unites_actif
        self.prix = prix


class RapportAppelsOffresDemantelement:
    """
    Cette classe synthétise les informations d'une séquence d'appels d'offres de démantèlement.

    Attributs
    ---------
    argent_restant : float
        part du budget consacré aux appels d'offres de démantèlement qui n'a pas été dépensée
    liste_appels_offres_demantelement : list
        liste les appels d'offres émis lors de la séquence
    """
    def __init__(self, argent_restant, liste_appels_offres_demantelement):
        self.argent_restant = argent_restant
        self.liste_appels_offres_demantelement = liste_appels_offres_demantelement


def sequence_appels_offres_demantelement(donnees_entree, donnees_simulation):
    """
    Effectue la séquence d'appels d'offres de démantèlement annuelle et renvoie le rapport associé.

    Paramètres
    ----------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser, ce paramètre est modifié par la fonction

    Retours
    -------
    RapportAppelsOffresDemantelement
        rapport de la séquence d'appels d'offres de démantèlement
    """
    
    
    annee_courante = donnees_simulation.annee_courante
    idx_fin = (donnees_entree.parametres_simulation.horizon_simulation-1)    
    df_param_ao = donnees_entree.df_param_ao
    
    cond_techno_eligibile = df_param_ao["sequence_demantelement"] == True
    df_param_ao = df_param_ao[cond_techno_eligibile]
        
    if len(df_param_ao.index) == 0 :
        print("Pas de techno eligibiles aux AO fermeture")
        return RapportAppelsOffresDemantelement(0, [])
    
    annee_courante = donnees_simulation.annee_courante
    horizon_prevision = donnees_entree.parametres_simulation.horizon_prevision
    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation


    df_param_ao = df_param_ao.sort_values(by="preseance")
    
    dict_actif_eligible = {}
    
    for nom_actif in df_param_ao.index :
        ordre_preseance = df_param_ao.at[nom_actif,"preseance"]
        for actif in donnees_entree.tous_actifs():
            if nom_actif == actif.cle : 
                dict_actif_eligible[ordre_preseance] = actif

    df_nb_unites_parc_reel = donnees_simulation.parc.get_df_nb_unites().loc[0:idx_fin]
    
    nom_fic = "DF_PR_DivestAO_%s.csv"%(str(annee_courante))    
    path_df_parc_reel = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
    df_nb_unites_parc_reel.to_csv(path_df_parc_reel,sep=";")
        
    #### Lecture du parc exogène 
        
    if donnees_entree.parametres_simulation.anticipation_parc_exogene :

        dico_parcs_anticipes_ao = donnees_entree.get_parc_anticipation()
        dico_df_nb_unites_ambiances = donnees_entree.mise_en_coherence_parc(annee_courante,
                                                                            dico_parcs_anticipes_ao,
                                                                            donnees_simulation.parc,
                                                                            add_current_divestment=True)


    else : 

        
        df_nb_unites = df_nb_unites_parc_reel.copy()
        
        dico_df_nb_unites_ambiances = {}
        
        for ambiance in donnees_entree.ambiances :

            if donnees_entree.parametres_simulation.extrapolation_capa :
            
                nb_annee_extrapolation =  donnees_entree.parametres_simulation.nb_annee_extrapolation_capa          
                dico_df_nb_unites_ambiances[ambiance] = donnees_simulation.parc.get_df_nb_unites_extrapole(annee_courante,nb_annee_extrapolation)
                
            else :
                dico_df_nb_unites_ambiances[ambiance] = df_nb_unites.copy()

    for ambiance in donnees_entree.ambiances :
    
        nom_fic = "DF_PA_%s_DivestAO_%s.csv"%(ambiance,str(annee_courante))    
        path_df = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
        dico_df_nb_unites_ambiances[ambiance].to_csv(path_df,sep=";")

                
    fin_anticipation = np.min([annee_courante+horizon_prevision,
                            horizon_simulation]).astype(int)
    
    print("realisation d'une anticiation entre %s et %s"%(annee_courante,fin_anticipation-1))
    
                                    
    # matrice des résultats annuels anticipés pour évaluer le manque à gagner des unités fermées
    matrice_resultats_annuels = Anticipation.anticipation_resultats_annuels_parc_exogene(annee_courante, fin_anticipation, donnees_entree, donnees_simulation,dico_df_nb_unites_ambiances)

        
    liste_appels_offres_demantelement = []

    for round_ao in dict_actif_eligible:
    
        actif = dict_actif_eligible[round_ao]
        
        capacite_demantelement_argent = df_param_ao.at[actif.cle,"budget_annuel_demantelement"]

        
        nombre_unites_cible = donnees_entree.mix_cible[actif.cle][annee_courante]
        nombre_unites_excedentaires = donnees_simulation.parc.nombre_unites(actif.cle, annee_courante) - nombre_unites_cible

        if not(nombre_unites_excedentaires > 0):
            continue

        idx = donnees_simulation.df_resume.index.max()+1
        donnees_simulation.df_resume.at[idx,"step"] = "LTC_closure_for_%d_%s"%(nombre_unites_excedentaires,actif.cle)
        donnees_simulation.df_resume.at[idx,"tech"] = actif.cle
        donnees_simulation.df_resume.at[idx,"module"] = "DivestAO"
        donnees_simulation.df_resume.at[idx,"year"] = annee_courante
        
        liste_unites_actives_avec_cout_fermeture = []
        for unite in donnees_simulation.parc.unites_actives(actif.cle, annee_courante):
            # calcul des revenus annuels de l'unité à partir des résultats annuels avec extrapolation éventuelle des
            # revenus des années non anticipées jusqu'à la fin de la durée de vie
            matrice_revenus_annuels = IndicateursEconomiques.calcul_matrice_revenus_annuels_sans_CF(unite, matrice_resultats_annuels, annee_courante, unite.annee_fermeture, donnees_entree, donnees_simulation)

            nbAnneeCalculNPV = unite.annee_fermeture - annee_courante 
            
            taux_actualisation = actif.taux_actualisation
            investissement_initial = 0
            
            
            VAN_equivalente,VAN_annualisee,prime_risque,liste_VAN_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_annuels, taux_actualisation, donnees_entree, investissement_initial, nbAnneeCalculNPV)
            VAN_equivalente -= np.array([ actif.cout_fixe_maintenance* (1+taux_actualisation)**(-n) for n in range(nbAnneeCalculNPV)]).sum() 

            
            # on calcule le coût de fermeture anticipée comme la VAN sur le reste de la durée de vie de l'unité
            # sans investissement initial ni durée de construction
            cout_fermeture_anticipee = VAN_equivalente

            # si l'unité est déficitaire, la fermer ne coûte rien
            cout_fermeture_anticipee = max(0, cout_fermeture_anticipee)

            liste_unites_actives_avec_cout_fermeture.append((unite, cout_fermeture_anticipee))

        # tri de la liste par cout de fermeture anticipée croissant
        liste_unites_actives_avec_cout_fermeture.sort(key=lambda x: x[1])

        nombre_unites_fermees = 0
        prix_appel_offres = 0
        for unite, cout_fermeture_anticipee in liste_unites_actives_avec_cout_fermeture:
            if (capacite_demantelement_argent - (nombre_unites_fermees + 1) * cout_fermeture_anticipee < 0):
                # si l'unité examinée est fermée, sont coût de fermeture fixe le prix de clearing de l'appel d'offres
                # si la capacité en argent est insuffisante pour financer la fermeture supplémentaire et toutes les
                # autres au prix de clearing, on s'arrête
                break

            if not (nombre_unites_fermees < nombre_unites_excedentaires):
                break

            nombre_unites_fermees += 1

            prix_appel_offres = nombre_unites_fermees * cout_fermeture_anticipee

            donnees_simulation.parc.fermeture_anticipee_unite(unite, annee_courante)

        capacite_demantelement_argent -= prix_appel_offres

        print("Émission de %d appels d'offres de fermeture pour des unités de %s"%(nombre_unites_fermees, actif.cle))

        appel_offres_demantelement = AppelOffresDemantelement(actif, nombre_unites_fermees, prix_appel_offres)
        liste_appels_offres_demantelement.append(appel_offres_demantelement)


    rapport_appels_offres_demantelement = RapportAppelsOffresDemantelement(capacite_demantelement_argent, liste_appels_offres_demantelement)
    return rapport_appels_offres_demantelement
