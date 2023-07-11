# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import os
import sys
import copy

import numpy as np
import pandas as pd

import IndicateursEconomiques
import Anticipation
import DonneesSimulation
import Ecriture
import Lecture


class RapportBoucleInvestissement:
    """
    Cette classe synthétise les informations d'une boucle d'investissement.

    Attributs
    ---------
    actif_choisi : DonneesEntree.Actif
        actif qui a été choisi pour en construire des unités dans la boucle d'investissement
    nombre_unites_investies : int
        nombre d'unités dont la construction a été décidée dans la boucle d'investissement
    dict_VAN_equivalente : dict
        dictionnaire contenant, pour chaque type d'actif, la valeur de la VAN équivalente, si elle a été calculée
    dict_revenu_equivalent_premiere_annee_fonctionnement : dict
        dictionnaire contenant, pour chaque type d'actif, la valeur du revenu équivalent de la première année de
        fonctionnement, si elle a été calculée
    dict_critere_investissement : dict
        dictionnaire contenant, pour chaque type d'actif, la valeur du critère d'investissement, si elle a été calculée
    """

    def __init__(self, actif_choisi, nombre_unites_investies, dict_VAN_equivalente, dict_revenu_equivalent_premiere_annee_fonctionnement, dict_criteres_investissement):
        self.actif_choisi = actif_choisi
        self.nombre_unites_investies = nombre_unites_investies
        self.dict_VAN_equivalente = dict_VAN_equivalente
        self.dict_revenu_equivalent_premiere_annee_fonctionnement = dict_revenu_equivalent_premiere_annee_fonctionnement
        self.dict_critere_investissement = dict_criteres_investissement


class RapportInvestissement:
    """
    Cette classe synthétise les informations d'une séquence d'investissement.

    Attributs
    ---------
    argent_restant : float
        part du budget consacré à l'investissement qui n'a pas été dépensée
    puissance_restante : float
        part du budget en puissance consacré à l'investissement qui n'a pas été dépensée
    liste_rapports_boucle_investissement : list
        liste des rapports de boucles d'investissement de la séquence
    """

    def __init__(self, argent_restant, puissance_restante, liste_rapports_boucle_investissement):
        self.argent_restant = argent_restant
        self.puissance_restante = puissance_restante
        self.liste_rapports_boucle_investissement = liste_rapports_boucle_investissement

    def __getitem__(self, indice_boucle):
        return self.liste_rapports_boucle_investissement[indice_boucle]


def choix_actif_candidat(liste_actifs_eligibles, dict_criteres_investissement, dict_revenu_equivalent_premiere_annee_fonctionnement, donnees_entree):
    """
    Calcule les critères d'investissements pour les actifs éligibles fournis et en déduit l'actif candidat pour
    l'investissement.

    Paramètres
    ----------
    liste_actifs_eligibles : list
        liste des actifs éligibles pour l'investissement
    dict_criteres_investissement : dict
        dictionnaire contenant, pour chaque actif éligible, la valeur du critère d'investissement
    dict_revenu_equivalent_premiere_annee_fonctionnement : dict
        dictionnaire contenant, pour chaque actif éligible, la valeur du revenu équivalent de la première année
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser

    Retours
    -------
    DonneesEntree.Actif
        actif candidat pour l'investissement, None si aucun n'a pu être sélectionné
    dict
        dictionnaire contenant, pour chaque actif éligible, la valeur du critère d'investissement
    """

    # selection des actifs candidats qui ont des indicateurs économiques satisfaisants
    liste_actifs_candidats = []
    for actif in liste_actifs_eligibles:
        booleen_actif_candidat = True

        # condition de critère d'investissement au dessus de la valeur limite
        if donnees_entree.parametres_simulation.critere_investissement == "PI":
            booleen_actif_candidat = booleen_actif_candidat and (dict_criteres_investissement[actif.cle] > 1)
        else:
            booleen_actif_candidat = booleen_actif_candidat and (dict_criteres_investissement[actif.cle] > 0)

        # condition de rentabilité la première année si les paramètres le demandent
        if donnees_entree.parametres_simulation.contrainte_rentabilite_premiere_annee:
            booleen_actif_candidat = booleen_actif_candidat and (dict_revenu_equivalent_premiere_annee_fonctionnement[actif.cle] >= actif.exigence_rentabilite_premiere_annee)

        # ajout de l'actif à la liste des candidats si les conditions sont satisfaites
        if booleen_actif_candidat:
            liste_actifs_candidats.append(actif)

    # tri des candidats par ordre décroissant de critère d'investissement
    liste_actifs_candidats.sort(key=lambda actif: -dict_criteres_investissement[actif.cle])

    # choix de l'actif candidat de critère d'investissement le plus haut (s'il y en a un)
    actif_choisi = None
    if len(liste_actifs_candidats) > 0:
        actif_choisi = liste_actifs_candidats[0]

    return actif_choisi, dict_criteres_investissement

def evaluation_indicateurs_economiques_parc_exogene(liste_actifs_eligibles, donnees_entree, donnees_simulation,indice_boucle_investissement,dico_df_nb_unites_ambiances):
    """
    Calcule les indicateurs économiques qui permettent d'évaluer la rentabilité d'un investissement dans chacun
    des actifs éligibles.

    Paramètres
    ----------
    liste_actifs_eligibles : list
        liste des actifs éligibles pour l'investissement
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser

    Retours
    -------
    dict
        dictionnaire contenant, pour chaque actif éligible, la valeur du critère d'investissement
    dict
        dictionnaire contenant, pour chaque actif éligible, la valeur du revenu équivalent de la première année
    """

    annee_courante = donnees_simulation.annee_courante

    dict_VAN_equivalentes = dict()
    dict_criteres_investissement = dict()
    dict_revenu_equivalent_premiere_annee_fonctionnement = dict()
    
    df_resume_evaluation = pd.DataFrame()
    
    # calcul des valeurs nécessaires pour comparer la rentabilité des différents actifs eligibles
    for actif in liste_actifs_eligibles:
        # l'ajout de l'actif est testé
        print("\t\t test d'ajout  d'une unité de %s" % (actif.cle))
        duree_construction = actif.duree_construction
        duree_vie = actif.duree_vie
        annee_ouverture = annee_courante + duree_construction
        annee_fermeture = annee_ouverture + duree_vie
        unite = DonneesSimulation.Unite(actif, annee_ouverture, annee_fermeture)

        # calcul des résultats annuels pour les différentes ambiances, années et météos avec l'unité testée dans le parc
        annee_debut_anticipation = annee_ouverture
        annee_fin_anticipation = min(annee_courante + donnees_entree.parametres_simulation.horizon_prevision,
                                        annee_debut_anticipation + actif.duree_vie,
                                        donnees_entree.parametres_simulation.horizon_simulation)
        
        
        if donnees_entree.parametres_simulation.extrapolation_EOM :
            annee_fin_calcul_NPV = annee_debut_anticipation + actif.duree_vie
        else : 
            annee_fin_calcul_NPV = annee_fin_anticipation          
        
        nbAnneeNPV = annee_fin_calcul_NPV - annee_debut_anticipation
        
        print("\t\t\t Anticipation entre les années %d (année ouverture) et %d (non incluse)"%(annee_debut_anticipation,annee_fin_anticipation))

        dico_nb_unites_ambiances_test = {}

        for ambiance in donnees_entree.ambiances :
            
            if donnees_entree.parametres_simulation.test_avant_invest :
            
                df_nb_unites_ambiances_test = dico_df_nb_unites_ambiances[ambiance].copy()
                
                for k in range(annee_ouverture,annee_fermeture):
                    if k in df_nb_unites_ambiances_test.index :
                        df_nb_unites_ambiances_test.at[k,actif.cle] = df_nb_unites_ambiances_test.at[k,actif.cle] + 1


            nom_fic = "DF_PA_%s_MerchInvest_%s_%s_test_%s.csv"%(ambiance,str(annee_courante),str(indice_boucle_investissement),actif.cle)    
            path_df_parc = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
            df_nb_unites_ambiances_test.to_csv(path_df_parc,sep=";")
            
            dico_nb_unites_ambiances_test[ambiance] = df_nb_unites_ambiances_test
        
        # realisation de l'anticipation
        
        matrice_resultats_annuels = Anticipation.anticipation_resultats_annuels_parc_exogene(annee_debut_anticipation,annee_fin_anticipation, donnees_entree, donnees_simulation,dico_nb_unites_ambiances_test,True,"test_%s"%(actif.cle))
        
        Ecriture.ecriture_dispatch_boucle(matrice_resultats_annuels,donnees_entree,donnees_simulation,"rapport_investissement",indice_boucle_investissement,annee_courante,actif.cle)


        # calcul des revenus annuels à partir des résultats annuels avec extrapolation éventuelle au delà de
        # l'horizon de prévision pour couvrir la totalité de la durée de vie
        matrice_revenus_annuels = IndicateursEconomiques.calcul_matrice_revenus_annuels_sans_CF(unite, matrice_resultats_annuels, annee_ouverture, annee_fin_calcul_NPV, donnees_entree, donnees_simulation)
        
        
        # Calcul du volume de CAPEX à prendre en compte
        
        taux_actualisation = actif.taux_actualisation
        annuite = IndicateursEconomiques.calcul_investissement_IDC_annualise(actif,annee_courante)
        
        print("annuite ",annuite)
        

        investissement_initial =  np.array([ annuite* (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum() 
        
                       
        parametre_critere_investissement = donnees_entree.parametres_simulation.critere_investissement
        critere_investissement = 0
        
        if(parametre_critere_investissement == "PI"):
            VAN_equivalente,VAN_annualisee,prime_risque,liste_VAN_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_annuels, taux_actualisation, donnees_entree, investissement_initial, nbAnneeNPV)
            VAN_equivalente -= np.array([ actif.cout_fixe_maintenance* (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum() 
            critere_investissement = IndicateursEconomiques.calcul_indice_profitabilite(actif, VAN_equivalente, investissement_initial)
        elif(parametre_critere_investissement == "VAN_MW"):
            VAN_equivalente,VAN_annualisee,prime_risque,liste_VAN_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_annuels, taux_actualisation, donnees_entree, investissement_initial, nbAnneeNPV)
            VAN_equivalente -= np.array([ actif.cout_fixe_maintenance* (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum() 
            critere_investissement = IndicateursEconomiques.calcul_VAN_par_MW(actif, VAN_equivalente)
        elif(parametre_critere_investissement == "TRI"):
            taux_rentabilite_interne = IndicateursEconomiques.calcul_taux_rentabilite_interne_equivalent(matrice_revenus_annuels, donnees_entree, investissement_initial, duree_construction,False,"investissement")
            critere_investissement = taux_rentabilite_interne - actif.taux_actualisation
            VAN_equivalente = "non calculé"

        
        # ecriture du resume 
        
        df_resume_evaluation.loc[ actif.cle , "VAN_equivalente"] = VAN_equivalente
        for idx,ambiance in enumerate(donnees_entree.ambiances) :
            df_resume_evaluation.loc[ actif.cle , "VAN_" + ambiance] = liste_VAN_possibles[idx]
             

        # on construit une restriction de la matrice des revenus annuels à l'année d'ouverture de l'unité
        matrice_revenus_annuels_annnee_ouverture = [[matrice_revenus_annuels_ambiance[0]] for matrice_revenus_annuels_ambiance in matrice_revenus_annuels]

        # on calcule le "revenu équivalent" de la première année de fonctionnement en appliquant la fonction de calcul
        # de VAN équivalente uniquement aux revenus de l'année d'ouverture sans actualisation ni investissement initial
        
        revenu_equivalent_premiere_annee_fonctionnement,revenu_equivalent_premiere_annee_fonctionnement_annualisee,prime_risque,liste_VAN_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_annuels_annnee_ouverture, 0, donnees_entree,0,1)
        
        revenu_equivalent_premiere_annee_fonctionnement -= actif.cout_fixe_maintenance

        dict_VAN_equivalentes[actif.cle] = VAN_equivalente
        dict_criteres_investissement[actif.cle] = critere_investissement
        dict_revenu_equivalent_premiere_annee_fonctionnement[actif.cle] = revenu_equivalent_premiere_annee_fonctionnement

        # retrait de l'actif testé du parc
        
        if donnees_entree.parametres_simulation.test_avant_invest :        
            if not donnees_entree.parametres_simulation.anticipation_parc_exogene :
                donnees_simulation.parc.annule_tests()

                
    path_resume_folder = os.path.join(donnees_entree.dossier_sortie,"annee_"+ str(annee_courante),"rapport_investissement",str(indice_boucle_investissement))
    if not os.path.isdir(path_resume_folder):
        os.makedirs(path_resume_folder)
        
    path_resume = os.path.join(path_resume_folder,"resume_VAN.csv")

    df_resume_evaluation.to_csv(path_resume,sep=";")
    
    return dict_criteres_investissement, dict_revenu_equivalent_premiere_annee_fonctionnement, dict_VAN_equivalentes


def selection_actifs_eligibles(capacite_investissement_argent, capacite_investissement_puissance, donnees_entree, donnees_simulation):
    """
    Sélectionne, parmi l'ensemble des actifs, ceux qui sont eligibles pour l'investissement et calcule pour chacun le
    nombre maximum d'unités pouvant être construites en respectant les capacités d'investissement et les limites de
    gisement.

    Paramètres
    ----------
    capacite_investissement_argent : float
        part du budget consacré à l'investissement encore disponible
    capacite_investissement_puissance : float
        part du budget en puissance consacré à l'investissement encore disponible
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser

    Retours
    -------
    list
        liste des actifs éligibles
    dict
        dictionnaire contenant, pour chaque actif éligible, le nombre maximal d'unités pouvant être construites
    """

    annee_courante = donnees_simulation.annee_courante
    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation

    # représentation de l'infini
    plus_infini = float("inf")

    liste_actifs_eligibles = []

    dict_nombre_max_unites_investies = dict()

    # construction de la liste des actifs eligible selon les ressources d'investissement restantes
    # et selon le gisement disponible pour la technologie
    for actif in donnees_entree.tous_actifs():

        dict_nombre_max_unites_investies[actif.cle] = 0

        # on va calculer le nombre maximum d'unités de l'actif dans lesquelles on peut investir
        # ce nombre est initialisé à plus_infini
        nombre_max_unites_investies = plus_infini

        puissance = 0
        if actif.categorie == "Stockage":
            puissance = actif.puissance_nominale_decharge
        elif actif.categorie == "Pilotable":
            puissance = actif.puissance_nominale
        elif actif.categorie == "ENR":
            puissance = actif.puissance_reference

        # non-dépassement de la limite de construction annuelle
        if not(actif.limite_construction_annuelle == 'aucune'):
            nombre_unites_deja_ouvertes = donnees_simulation.parc.nombre_unites_ouvertes(actif.cle, annee_courante + actif.duree_construction)
            nombre_max_unites_investies = min(nombre_max_unites_investies, max(0, actif.limite_construction_annuelle - nombre_unites_deja_ouvertes))

        # non-dépassement de la capacité d'investissement en argent
        cout_fixe_construction_actif = actif.cout_fixe_construction(annee_courante)
        if cout_fixe_construction_actif > 0:
            nombre_max_unites_investies = min(nombre_max_unites_investies, int(capacite_investissement_argent / cout_fixe_construction_actif))

        # non-dépassement de la capacité d'investissement en puissance
        if puissance > 0:
            nombre_max_unites_investies = min(nombre_max_unites_investies, int(capacite_investissement_puissance / puissance))

        # non-dépassement du gisement sur toute la durée de vie de l'actif potentiellement construit
        # uniquement vérifié s'il est possible d'investir dans au moins une unité avec les capacités restantes
        if (nombre_max_unites_investies > 0) and (not actif.gisement_max == "aucun") and puissance > 0:
            nombre_max_unites_total = int(actif.gisement_max / puissance)
            for annee_fonctionnement in range(min(annee_courante + actif.duree_construction, horizon_simulation), min(annee_courante + actif.duree_construction + actif.duree_vie, horizon_simulation)):
                nombre_max_unites_investies = min(nombre_max_unites_investies, nombre_max_unites_total - donnees_simulation.parc.nombre_unites(actif.cle, annee_fonctionnement))

        if actif.ajoutable and nombre_max_unites_investies > 0:
            liste_actifs_eligibles.append(actif)
            dict_nombre_max_unites_investies[actif.cle] = nombre_max_unites_investies

    return liste_actifs_eligibles, dict_nombre_max_unites_investies


def sequence_investissement_classique(donnees_entree, donnees_simulation):
    """
    Cette fonction effectue la séquence d'investissement annuelle classique et renvoie le rapport associé.

    Paramètres
    ----------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser, ce paramètre est modifié par la fonction

    Retours
    -------
    RapportInvestissement
        rapport de la séquence d'investissement
    """

    annee_courante = donnees_simulation.annee_courante
    idx_fin = (donnees_entree.parametres_simulation.horizon_simulation-1)
    capacite_investissement_argent = donnees_entree.parametres_simulation.limite_argent
    capacite_investissement_puissance = donnees_entree.parametres_simulation.limite_capacite
            
    ### Avant de commencer les boucles d'investissements, on prépare le parc anticipé si cette option est activée
      
    dico_parcs_anticipes_boucle = donnees_simulation.dico_parcs_anticipes

    #### Boucle d'investissements
    
    continuer_investissements = True
    liste_rapports_investissement = []
    indice_boucle_investissement = 0

    parc_avant_sequences = copy.deepcopy(donnees_simulation.parc_avant_sequences)
    
    while (continuer_investissements):
        print("\t Investissement boucle %d \n" % indice_boucle_investissement)
  
        # selection des actifs eligibles selon les capacités d'investissement et de gisement
        # et calcul du nombre maximum d'unités dans lesquelles il est possible d'investir
        liste_actifs_eligibles, dict_nombre_max_unites_investies = selection_actifs_eligibles(capacite_investissement_argent, capacite_investissement_puissance, donnees_entree, donnees_simulation)


        df_nb_unites_parc_reel = donnees_simulation.parc.get_df_nb_unites().loc[0:idx_fin]
        
        nom_fic = "DF_PR_MerchInvest_%s_%s.csv"%(str(annee_courante),str(indice_boucle_investissement))    
        path_df_parc_reel = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
        df_nb_unites_parc_reel.to_csv(path_df_parc_reel,sep=";")
        
        
        if donnees_entree.parametres_simulation.anticipation_parc_exogene :

            if  donnees_entree.parametres_simulation.anticipation_demantelement :
            
                # si on voit ce qu'a fait la boule de demantelement, on met en cohérence avec le parc réel
                
                dico_df_nb_unites_ambiances = donnees_entree.mise_en_coherence_parc(annee_courante,dico_parcs_anticipes_boucle,parc_avant_sequences,add_current_divestment=True)
 
            else : 

                # si on suppose que la sequence d'investissement ignore le resultat de la sequence de demantelement,
                # on met en cohérence avec le parc avant séquences
                
                
                dico_df_nb_unites_ambiances = donnees_entree.mise_en_coherence_parc(annee_courante,dico_parcs_anticipes_boucle,parc_avant_sequences)            
                

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
        
            nom_fic = "DF_PA_%s_MerchInvest_%s_%s.csv"%(ambiance,str(annee_courante),str(indice_boucle_investissement))    
            path_df_parc_anticip = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
            dico_df_nb_unites_ambiances[ambiance].to_csv(path_df_parc_anticip,sep=";")
        
            
        dict_criteres_investissement, dict_revenu_equivalent_premiere_annee_fonctionnement, dict_VAN_equivalentes = evaluation_indicateurs_economiques_parc_exogene(liste_actifs_eligibles, donnees_entree, donnees_simulation,indice_boucle_investissement,dico_df_nb_unites_ambiances)
  
        actif_choisi, dict_criteres_investissement = choix_actif_candidat(liste_actifs_eligibles, dict_criteres_investissement, dict_revenu_equivalent_premiere_annee_fonctionnement, donnees_entree)
        
        print("critères d'investissement : ", dict_criteres_investissement)

        if (not actif_choisi):
            # si aucun actif n'a pu être choisi, on renvoie un rapport de boucle d'investissement "vide"
            # dans lequel la clé d'actif choisi est None et le nombre d'unités investies est 0
            print("Stop investissement")
            continuer_investissements = False
            liste_rapports_investissement.append(RapportBoucleInvestissement(None, 0, dict_VAN_equivalentes, dict_revenu_equivalent_premiere_annee_fonctionnement, dict_criteres_investissement))

            idx = donnees_simulation.df_resume.index.max()+1
            donnees_simulation.df_resume.at[idx,"step"] = "stopping_MerchInvest"
            donnees_simulation.df_resume.at[idx,"module"] = "MerchInvest"
            donnees_simulation.df_resume.at[idx,"year"] = annee_courante     
            donnees_simulation.df_resume.at[idx,"loop"] = indice_boucle_investissement     
            break

        print("l'actif choisi est : %s" % actif_choisi.cle)

        # calcul du nombre d'unités investies selon la granularité et le nombre maximum possible
        nombre_max_unites_investies_actif_choisi = dict_nombre_max_unites_investies[actif_choisi.cle]
        nombre_unites_investies = min(nombre_max_unites_investies_actif_choisi, actif_choisi.granularite_investissement)

        # mise à jour des capacités d'investissement
        capacite_investissement_argent -= actif_choisi.cout_fixe_construction(annee_courante) * nombre_unites_investies
        puissance = 0
        if actif_choisi.categorie == "Stockage":
            puissance = actif_choisi.puissance_nominale_decharge
        elif actif_choisi.categorie == "Pilotable":
            puissance = actif_choisi.puissance_nominale
        elif actif_choisi.categorie == "ENR":
            puissance = actif_choisi.puissance_reference
        capacite_investissement_puissance -= puissance * nombre_unites_investies

        print("Choix d'investissement : ajout de %d unités de %s\n" % (nombre_unites_investies, actif_choisi.cle))
        annee_ouverture = annee_courante + actif_choisi.duree_construction
        annee_fermeture = annee_ouverture + actif_choisi.duree_vie
        for indice_unite_ajoutee in range(nombre_unites_investies):
            unite_ajoutee = DonneesSimulation.Unite(actif_choisi, annee_ouverture, annee_fermeture)
            donnees_simulation.parc.ajout_unite(unite_ajoutee)
            parc_avant_sequences.ajout_unite(unite_ajoutee)
            
            idx = donnees_simulation.df_resume.index.max()+1
            donnees_simulation.df_resume.at[idx,"step"] = "adding_%d_%s"%(nombre_unites_investies, actif_choisi.cle)
            donnees_simulation.df_resume.at[idx,"module"] = "MerchInvest"
            donnees_simulation.df_resume.at[idx,"year"] = annee_courante                 
            donnees_simulation.df_resume.at[idx,"loop"] = indice_boucle_investissement                 

        rapport_boucle_investissement = RapportBoucleInvestissement(actif_choisi, nombre_unites_investies, dict_VAN_equivalentes, dict_revenu_equivalent_premiere_annee_fonctionnement, dict_criteres_investissement)
        liste_rapports_investissement.append(rapport_boucle_investissement)

        indice_boucle_investissement += 1
        
    # sortie de la boucle
        

    rapport_investissement = RapportInvestissement(capacite_investissement_argent, capacite_investissement_puissance, liste_rapports_investissement)
    return rapport_investissement


def sequence_investissement(donnees_entree, donnees_simulation):
    """
    Cette fonction effectue la séquence d'investissement annuelle en utilisant le type de séquence choisie par
    l'utilisateur et renvoie le rapport associé.

    Paramètres
    ----------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser, ce paramètre est modifié par la fonction

    Retours
    -------
    RapportInvestissement
        rapport de la séquence d'investissement
    """

    if not(donnees_entree.parametres_simulation.sequence_investissement):
        print("Séquence d'investissement désactivée")
        return RapportInvestissement(donnees_entree.parametres_simulation.limite_argent, donnees_entree.parametres_simulation.limite_capacite, [])

    # sélection de la fonction de séquence d'investissement
    fonction_sequence_investissement = sequence_investissement_classique

    rapport_investissement = fonction_sequence_investissement(donnees_entree, donnees_simulation)
    return rapport_investissement
