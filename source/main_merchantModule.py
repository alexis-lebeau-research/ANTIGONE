# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import Lecture
import Ecriture
import Investissement
import Demantelement
import Realisation
import AppelsOffresInvestissement
import AppelsOffresDemantelement
import MerchantModule
import Gep

import sys
import time
import os
import pandas as pd
import copy

def simulation(nom_dossier_donnees):
    """ 
    Effectue une simulation en utilisant les données contenues dans le sous-dossier du dossier instances dont le nom est
    donné en paramètre.

    Paramètres
    ----------
    nom_dossier_donnees : str
        nom du dossier contenant les données, le dossier doit être contenu dans le dossier instances
    """
    
    
    dossier_sortie = os.path.dirname(os.getcwd()) + "/results/" +   time.strftime("%d_%B_%Y/") + time.strftime("%Hh%Mm%Ss") + "_" + nom_dossier_donnees.replace("/","_")
    os.makedirs(dossier_sortie)

    path_parc_vision = os.path.join(dossier_sortie,"parc_vision")
    os.makedirs(path_parc_vision)

    print("\n###########################################################################\n")
    print("LECTURE DES DONNEES : %s"%nom_dossier_donnees)
    donnees_entree, donnees_simulation = Lecture.lecture_generale(nom_dossier_donnees, callType = 'antigone')
    print("DONNEES LUES\n")
    
    donnees_entree.dossier_sortie = dossier_sortie
    donnees_simulation.dossier_sortie = dossier_sortie


    # ECRITURE DES PARCS INITIAUX

    parc_reel = donnees_simulation.parc
    df_nbu_pr = parc_reel.get_df_nb_unites().loc[0:]

    nom_fic = "DF_PR_init.csv"    
    path_df_pr = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
    df_nbu_pr.to_csv(path_df_pr,sep=";")  
    
    if donnees_entree.parametres_simulation.anticipation_parc_exogene :
        for ambiance in donnees_entree.ambiances :
        
            parc = donnees_simulation.dico_parcs_anticipes[ambiance]
        
            df_nb_unites = parc.get_df_nb_unites().loc[0:]
            
            nom_fic = "DF_PA_%s.csv"%(ambiance)    
            path_df_pa = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
            df_nb_unites.to_csv(path_df_pa,sep=";")            
        
    # DEBUT DES SEQUENCES
    
    for annee in range(donnees_entree.parametres_simulation.horizon_simulation):

        if donnees_entree.parametres_simulation.update_gep == True :
            if donnees_simulation.annee_courante > 0 : 
                if ( donnees_simulation.annee_courante % donnees_entree.parametres_simulation.update_gep_frequency) == 0 :
            
                    chemins_gep = Ecriture.ecriture_entrees_gep(donnees_entree, donnees_simulation)
                    Gep.update_anticipation(donnees_entree, donnees_simulation,chemins_gep)
                    
               
                    for ambiance in donnees_entree.ambiances :

                        parc = donnees_simulation.dico_parcs_anticipes[ambiance]

                        df_nb_unites = parc.get_df_nb_unites().loc[0:]

                        nom_fic = "DF_PA_updated_%s_%d.csv"%(ambiance,annee)    
                        path_df_pa = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
                        df_nb_unites.to_csv(path_df_pa,sep=";")  
                        
        
        
        rapport_appels_offres_investissement = AppelsOffresInvestissement.RapportAppelsOffresInvestissement(0, 0, [])
        rapport_appels_offres_demantelement = AppelsOffresDemantelement.RapportAppelsOffresDemantelement(0, [])
        dict_rapport_annuel_mecanisme_capacite = {}
        
        if(donnees_entree.parametres_simulation.architecture == "AOCLT"):
            print("ANNEE %d | APPELS D'OFFRES INVESTISSEMENT"%annee)
            rapport_appels_offres_investissement = AppelsOffresInvestissement.sequence_appels_offres_investissement(donnees_entree, donnees_simulation)
            print("ANNEE %d | APPELS D'OFFRES DEMANTELEMENT" % annee)
            rapport_appels_offres_demantelement = AppelsOffresDemantelement.sequence_appels_offres_demantelement(donnees_entree, donnees_simulation)
            

        donnees_simulation.parc_avant_sequences = copy.deepcopy(donnees_simulation.parc)
        
        
        
        print("ANNEE %d | DEMANTELEMENT"%annee)
        rapport_demantelement = Demantelement.sequence_demantelement(donnees_entree, donnees_simulation)

        print("ANNEE %d | INVESTISSEMENT" % annee)
        rapport_investissement = Investissement.sequence_investissement(donnees_entree, donnees_simulation)
        
        MerchantModule.sequence_merchant_decisions(donnees_entree, donnees_simulation)

        print("ANNEE %d | REALISATION" % annee)
        liste_resultats_annuels = Realisation.realisation_annee_courante(donnees_entree, donnees_simulation)

        print("ANNEE %d TERMINEE" % annee)

        donnees_simulation.incrementation_annee(rapport_investissement, rapport_demantelement, rapport_appels_offres_investissement, rapport_appels_offres_demantelement, dict_rapport_annuel_mecanisme_capacite, liste_resultats_annuels)
        
    print("ECRITURE DES FICHIERS DE SORTIE")
    Ecriture.ecriture_generale(donnees_entree, donnees_simulation, nom_dossier_donnees)
    print("SIMULATION TERMINEE : %s"%nom_dossier_donnees)

    # ECRITURE DU PARC FINAL
    
    df_nbu_pr = donnees_simulation.parc.get_df_nb_unites().loc[0:]

    nom_fic = "DF_PR_final.csv"    
    path_df_pr = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
    df_nbu_pr.to_csv(path_df_pr,sep=";")  


    idx = donnees_simulation.df_resume.index.max()+1
    donnees_simulation.df_resume.at[idx,"step"] = "stopping_ANTIGONE"
    donnees_simulation.df_resume.to_csv(os.path.join(dossier_sortie,"resume.csv"),sep=";")
    
if __name__ == '__main__':
    temps_debut = time.time()

    liste_noms_dossier_donnees = sys.argv[1:]

    for nom_dossier_donnees in liste_noms_dossier_donnees:
        simulation(nom_dossier_donnees)

    temps_fin = time.time()

    print("Temps d'exécution : ", temps_fin - temps_debut)