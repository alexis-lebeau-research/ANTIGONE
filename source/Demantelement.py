# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import sys
import os
import copy

import numpy as np

import Anticipation
import IndicateursEconomiques
import Ecriture
import Lecture
import DonneesSimulation


class RapportBoucleDemantelement:
    """
    Cette classe synthétise les informations d'une boucle de démantèlement.

    Attributs
    ---------
    liste_unites_fermees : list
        liste des unités fermées
    revenu_moyen_terme_equivalent_unites_fermees : float
        revenu moyen terme équivalent des unités fermées
    """

    def __init__(self, liste_unites_fermees, revenu_moyen_terme_equivalent_unites_fermees):
        self.liste_unites_fermees = liste_unites_fermees
        self.revenu_moyen_terme_equivalent_unites_fermees = revenu_moyen_terme_equivalent_unites_fermees


class RapportDemantelement:
    """
    Cette classe synthétise les informations d'une séquence de démantèlement.

    Attributs
    ---------
    liste_rapports_boucle_demantelement : list
        liste des rapports de boucles de démantèlement de la séquence
    """

    def __init__(self, liste_rapports_boucle_demantelement):
        self.liste_rapports_boucle_demantelement = liste_rapports_boucle_demantelement

    def __getitem__(self, indice_boucle):
        return self.liste_rapports_boucle_demantelement[indice_boucle]


def sequence_demantelement(donnees_entree, donnees_simulation):
    """
    Cette fonction effectue la séquence de démantèlement annuelle et renvoie le rapport associé.

    Paramètres
    ----------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser, ce paramètre est modifié par la fonction

    Retours
    -------
    RapportDemantelement
        rapport de la séquence de démantèlement
    """
    if not(donnees_entree.parametres_simulation.sequence_demantelement):
        print("Séquence de démantèlement désactivée")
        return RapportDemantelement([])

    annee_courante = donnees_simulation.annee_courante
    idx_fin = (donnees_entree.parametres_simulation.horizon_simulation-1)
    continuer_demantelements = True
    liste_rapports_demantelement = []
    boucle_demantelement = 0

    dico_parcs_anticipes_boucle = donnees_simulation.dico_parcs_anticipes
    
 
    ### Debut de la boucle de demantelement 


    while (continuer_demantelements):

        print("\t Demantelement boucle %d" % boucle_demantelement)

        df_nb_unites_parc_reel = donnees_simulation.parc.get_df_nb_unites().loc[0:idx_fin]
        
        nom_fic = "DF_PR_MerchDivest_%s_%s.csv"%(str(annee_courante),str(boucle_demantelement))    
        path_df_parc_reel = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
        df_nb_unites_parc_reel.to_csv(path_df_parc_reel,sep=";")
     
        # anticipation des résultats annuels pour la prochaine année de fonctionnement
        
        if donnees_entree.parametres_simulation.anticipation_parc_exogene :
            print("\t\t utilisation d'un parc exogene")             
             
            if donnees_entree.parametres_simulation.anticipation_investissement :
            
                print("\t\t\t anticipation des investissements")

                dico_df_nb_unites_ambiances = donnees_entree.mise_en_coherence_parc(annee_courante,
                                                                                    dico_parcs_anticipes_boucle,
                                                                                    donnees_simulation.parc,
                                                                                    add_current_investment=True)

            else :
            
                print("\t\t\t pas d'anticipation des investissements")

                dico_df_nb_unites_ambiances = donnees_entree.mise_en_coherence_parc(annee_courante,
                                                                                    dico_parcs_anticipes_boucle,
                                                                                    donnees_simulation.parc,
                                                                                    add_current_investment=False)

        else : 
        
            print("\t\t pas d'utilisation d'un parc exogene") 
            
            dico_df_nb_unites_ambiances = {}
            
            for ambiance in donnees_entree.ambiances :
             
                if donnees_entree.parametres_simulation.extrapolation_capa :
                    print("\t\t\t extrapolation des capacités")                
                    nb_annee_extrapolation =  donnees_entree.parametres_simulation.nb_annee_extrapolation_capa
                    
                    dico_df_nb_unites_ambiances[ambiance] = donnees_simulation.parc.get_df_nb_unites_extrapole(annee_courante,nb_annee_extrapolation)   
                else : 
                    print("\t\t\t pas d'extrapolation des capacités")       
                    
                    dico_df_nb_unites_ambiances[ambiance] = donnees_simulation.parc.get_df_nb_unites().loc[0:idx_fin]

        for ambiance in donnees_entree.ambiances :
            nom_fic = "DF_PA_%s_MerchDivest_%s_%s.csv"%(ambiance,str(annee_courante),str(boucle_demantelement))
            path_df_parc_reel = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
            dico_df_nb_unites_ambiances[ambiance].to_csv(path_df_parc_reel,sep=";")
        
        print("\t\t Anticipation des résultats pour l'année courante : année %s"%(annee_courante))
            
        matrice_resultats_annuels_annee_courante = Anticipation.anticipation_resultats_annuels_parc_exogene(annee_courante, annee_courante+1, donnees_entree, donnees_simulation,dico_df_nb_unites_ambiances)
        
        Ecriture.ecriture_dispatch_boucle(matrice_resultats_annuels_annee_courante,donnees_entree,donnees_simulation,"rapport_demantelement",boucle_demantelement,annee_courante)
    
        # identification des actifs déficitaires pour au moins une combinaison ambiance-météo pour l'année à suivre
        dict_unites_en_sursis = dict()
        for actif in donnees_entree.tous_actifs():
           
            if not actif.demantelable:
                continue

            liste_unites_en_sursis_actif = []

            for unite in donnees_simulation.parc.unites_actives(actif.cle, annee_courante):
                
                # calcul des revenus de l'unité examinée pour l'année courante dans les différentes ambiances et météos
                matrice_revenus_annuels_annee_courante = IndicateursEconomiques.calcul_matrice_revenus_annuels(unite, matrice_resultats_annuels_annee_courante, annee_courante, annee_courante + 1, donnees_entree, donnees_simulation)
                
                deficitaire = False
                for indice_ambiance in range(len(matrice_revenus_annuels_annee_courante)):
                    for indice_meteo in range(len(matrice_revenus_annuels_annee_courante[indice_ambiance][0])):
                        if matrice_revenus_annuels_annee_courante[indice_ambiance][0][indice_meteo] < 0:
                            deficitaire = True

                if deficitaire:
                    liste_unites_en_sursis_actif.append(unite)

            if(len(liste_unites_en_sursis_actif) > 0):
                dict_unites_en_sursis[actif.cle] = liste_unites_en_sursis_actif
                print("\t\t %d unités de %s en sursis"%(len(liste_unites_en_sursis_actif), actif.cle))
                
            
        horizon_prevision = donnees_entree.parametres_simulation.horizon_prevision
        dict_listes_unites_en_sursis_et_revenu_moyen_terme_equivalent = dict()

        if(len(dict_unites_en_sursis.keys()) > 0):
                 
            # anticipation des années manquantes jusqu'à l'horizon de prévision
            
            annee_fin_anticipation = np.min((donnees_entree.parametres_simulation.horizon_simulation, annee_courante + horizon_prevision))
            
            print("\t\t Anticipation du reste de l'horizon de prévision, i.e. de l'année %s à %s (non incluse)"%(annee_courante + 1,annee_fin_anticipation))
            
            matrice_resultats_annuels_reste_horizon_prevision = Anticipation.anticipation_resultats_annuels_parc_exogene(annee_courante + 1, annee_fin_anticipation, donnees_entree, donnees_simulation,dico_df_nb_unites_ambiances)
            
            Ecriture.ecriture_dispatch_boucle(matrice_resultats_annuels_reste_horizon_prevision,donnees_entree,donnees_simulation,"rapport_demantelement",boucle_demantelement,annee_courante+1)    
            
            # fusion des matrices de résultats annuels pour compléter les anticipations jusqu'à l'horizon de prévision
            matrice_resultats_annuels_horizon_prevision = []
            for indice_ambiance in range(len(matrice_resultats_annuels_annee_courante)):
                matrice_resultats_annuels_horizon_prevision_ambiance = matrice_resultats_annuels_annee_courante[indice_ambiance] + matrice_resultats_annuels_reste_horizon_prevision[indice_ambiance]
                matrice_resultats_annuels_horizon_prevision.append(matrice_resultats_annuels_horizon_prevision_ambiance)
            

            for cle_actif, liste_unites_en_sursis_actif in dict_unites_en_sursis.items():
                liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif = []
                
                for unite in liste_unites_en_sursis_actif:
                    
                    if donnees_entree.parametres_simulation.extrapolation_EOM :
                        annee_fin_calcul_NPV = annee_courante + unite.actif.duree_vie
                    else : 
                        annee_fin_calcul_NPV = annee_fin_anticipation          
                    
                    nbAnneeNPV = annee_fin_calcul_NPV - annee_courante
                    
                    matrice_revenus_sans_CF_annuels_unite = IndicateursEconomiques.calcul_matrice_revenus_annuels_sans_CF(unite, matrice_resultats_annuels_horizon_prevision, annee_courante, annee_fin_calcul_NPV , donnees_entree, donnees_simulation)
                    
                    revenu_sans_CF_moyen_terme_equivalent_unite,revenu_sans_CF_moyen_terme_equivalent_unite_annualise, prime_risque, liste_VAN_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_sans_CF_annuels_unite, unite.actif.taux_actualisation, donnees_entree,0,nbAnneeNPV)
                    
                    couts_fixes_maintenance = 0
                    for annee in range (annee_courante, annee_fin_calcul_NPV) : 
                        if (unite.annee_ouverture <= annee < unite.annee_fermeture):
                            couts_fixes_annee = unite.actif.cout_fixe_maintenance* (1+unite.actif.taux_actualisation)**(-(annee - annee_courante))
                        else :
                            couts_fixes_annee = 0 
                        couts_fixes_maintenance += couts_fixes_annee  
                        
                    
                    revenu_moyen_terme_equivalent_unite = revenu_sans_CF_moyen_terme_equivalent_unite - couts_fixes_maintenance
                    print(unite.annee_ouverture, unite.annee_fermeture, revenu_sans_CF_moyen_terme_equivalent_unite, couts_fixes_maintenance, revenu_moyen_terme_equivalent_unite < 0)
                    if(revenu_moyen_terme_equivalent_unite < 0):
                        # mise à jour des variables faisant le compte des années consécutives où la fermeture de l'unité
                        # est envisagée
                        if unite.derniere_annee_fermeture_anticipee_envisagee == annee_courante - 1:
                            # si la dernière année à laquelle une fermeture a été envisagée est l'année précédente,
                            # le compte d'années consécutives où la fermeture est envisagée est incrémenté
                            unite.nombre_annees_consecutives_fermeture_anticipee_envisagee += 1
                            unite.derniere_annee_fermeture_anticipee_envisagee = annee_courante
                        elif unite.derniere_annee_fermeture_anticipee_envisagee == annee_courante:
                            # si la fermeture de l'unité a déjà été envisagée à l'année courante, rien ne se passe
                            # car on ne peut incrémenter plusieurs fois le compteur à la même année
                            pass
                        elif unite.derniere_annee_fermeture_anticipee_envisagee < annee_courante - 1:
                            # si la dernière année à laquelle une fermeture a été envisagée est antérieure à l'année
                            # précédente, on réinitialise le compteur d'années consécutives où la fermeture est
                            # envisagée à 1
                            unite.nombre_annees_consecutives_fermeture_anticipee_envisagee = 1
                            unite.derniere_annee_fermeture_anticipee_envisagee = annee_courante

                        delai_fermeture = unite.actif.delai_fermeture
                        if(unite.nombre_annees_consecutives_fermeture_anticipee_envisagee >= delai_fermeture):
                            # si la fermeture de l'unité a été envisagée pendant suffisamment d'années consécutives,
                            # elle est ajoutée à la liste où seront choisies les unités démantelées
                            liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif.append((unite, revenu_moyen_terme_equivalent_unite))
                
                        
                if(len(liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif) > 0):
                    # tri de la liste des unités toujours déficitaires sur l'ensemble de l'horizon de prévision
                    # par ordre de revenu moyen terme équivalent croissant
                    liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif.sort(key=lambda x: x[1])
                    dict_listes_unites_en_sursis_et_revenu_moyen_terme_equivalent[cle_actif] = liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif
                    print("dictionnaire rempli")
                    
        # parcours du dictionnaire des listes d'unités déficitaires pour trouver
        # l'actif réalisant le minimum de revenu moyen terme équivalent
        revenu_moyen_terme_equivalent_minimal = 0
        cle_actif_moins_rentable = None
        for cle_actif, liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif in dict_listes_unites_en_sursis_et_revenu_moyen_terme_equivalent.items():
            revenu_moyen_terme_equivalent_minimal_actif = liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif[0][1]
            if(revenu_moyen_terme_equivalent_minimal_actif < revenu_moyen_terme_equivalent_minimal):
                revenu_moyen_terme_equivalent_minimal = revenu_moyen_terme_equivalent_minimal_actif
                cle_actif_moins_rentable = cle_actif


        if cle_actif_moins_rentable:
            actif_moins_rentable = donnees_entree.trouve_actif(cle_actif_moins_rentable)
            liste_unites_fermees = []

            liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif_moins_rentable = dict_listes_unites_en_sursis_et_revenu_moyen_terme_equivalent[cle_actif_moins_rentable]

            # les unités de l'actif le moins rentable ayant un revenu moyen terme équivalent égal
            # au revenu moyen terme équivalent minimal sont fermées dans la limite de la granularité de démantèlement

            """for indice_unite in range(min(actif_moins_rentable.granularite_demantelement, len(liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif_moins_rentable))):
                unite = liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif_moins_rentable[indice_unite][0]
                revenu_moyen_terme_equivalent_unite = liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif_moins_rentable[indice_unite][1]

                if not (revenu_moyen_terme_equivalent_unite == revenu_moyen_terme_equivalent_minimal):
                    # on ne traite que les unités réalisant le minimum du revenu moyen terme équivalent
                    # la liste étant triée, on s'arrête dès qu'on atteint un revenu moyen terme équivalent différent
                    break
                
                
                if donnees_entree.parametres_simulation.anticipation_parc_exogene :
                    for ambiance in donnees_entree.ambiances :                
                        dico_parcs_anticipes_boucle[ambiance].fermeture_anticipee_plus_lointaine(cle_actif_moins_rentable,annee_courante)

          
                print(unite.annee_fermeture)    
                donnees_simulation.parc.fermeture_anticipee_unite(unite, annee_courante)
                liste_unites_fermees.append(unite)
            """

            nb_unite_a_fermer = min(actif_moins_rentable.granularite_demantelement, len(liste_unites_en_sursis_et_revenu_moyen_terme_equivalent_actif_moins_rentable))

            for unite in range(nb_unite_a_fermer):


                if donnees_entree.parametres_simulation.unite_demantelee_anticipation == "plus_lointaine":

                    unite_fermee = donnees_simulation.parc.fermeture_anticipee_plus_lointaine(actif_moins_rentable.cle, annee_courante)
                    liste_unites_fermees.append(unite_fermee)

                    if donnees_entree.parametres_simulation.anticipation_parc_exogene:
                        for ambiance in donnees_entree.ambiances:
                            dico_parcs_anticipes_boucle[ambiance].fermeture_anticipee_plus_lointaine(unite_fermee.actif.cle,
                                                                                                  annee_courante)

                if donnees_entree.parametres_simulation.unite_demantelee_anticipation == "plus_proche":

                    unite_fermee = donnees_simulation.parc.fermeture_anticipee_plus_proche(actif_moins_rentable.cle, annee_courante)
                    liste_unites_fermees.append(unite_fermee)

                    if donnees_entree.parametres_simulation.anticipation_parc_exogene:
                        for ambiance in donnees_entree.ambiances:
                            dico_parcs_anticipes_boucle[ambiance].fermeture_anticipee_plus_proche(unite_fermee.actif.cle,
                                                                                                  annee_courante)


            # enregistrement du rapport de la boucle de demantelement
            print("\t\t %d unités de %s démantelées"%(len(liste_unites_fermees), cle_actif_moins_rentable))
            rapport_boucle_demantelement = RapportBoucleDemantelement(liste_unites_fermees, revenu_moyen_terme_equivalent_minimal)
            liste_rapports_demantelement.append(rapport_boucle_demantelement)
            
            idx = donnees_simulation.df_resume.index.max()+1
            donnees_simulation.df_resume.at[idx,"step"] = "removing_%d_%s"%(len(liste_unites_fermees), cle_actif_moins_rentable)
            donnees_simulation.df_resume.at[idx,"module"] = "MerchDivest"
            donnees_simulation.df_resume.at[idx,"year"] = annee_courante
            donnees_simulation.df_resume.at[idx,"loop"] = boucle_demantelement
               
            
            boucle_demantelement += 1

                
            if not(len(liste_unites_fermees) > 0):
                # si aucune unité n'a été démantelée, on met fin aux boucles de démantèlement

                idx = donnees_simulation.df_resume.index.max()+1
                donnees_simulation.df_resume.at[idx,"step"] = "stopping_MerchDivest"
                donnees_simulation.df_resume.at[idx,"module"] = "MerchDivest"
                donnees_simulation.df_resume.at[idx,"year"] = annee_courante
                donnees_simulation.df_resume.at[idx,"loop"] = boucle_demantelement
                                   
                continuer_demantelements = False

        else:
            print("\t\t Pas d'unité à démanteler\n")


            idx = donnees_simulation.df_resume.index.max()+1
            donnees_simulation.df_resume.at[idx,"step"] = "stopping_MerchDivest"
            donnees_simulation.df_resume.at[idx,"module"] = "MerchDivest"
            donnees_simulation.df_resume.at[idx,"year"] = annee_courante
            donnees_simulation.df_resume.at[idx,"loop"] = boucle_demantelement


            continuer_demantelements = False
                  
                               
    rapport_demantelement = RapportDemantelement(liste_rapports_demantelement)
    return rapport_demantelement





