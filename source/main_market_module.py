# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import sys
import time
import os

import MarketModule.Lecture_MarketModule as Lecture
import MarketModule.Ecriture_MarketModule as Ecriture
import MarketModule.Realisation_MarketModule as Realisation
import MarketModule.market_module as market_module
import MarketModule.Investissement_MarketModule as Investissement
import MarketModule.Demantelement_MarketModule as Demantelement
import MarketModule.Anticipation_MarketModule as Anticipation



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

    print("\n###########################################################################\n")
    print("LECTURE DES DONNEES : %s"%nom_dossier_donnees)
    donnees_entree, donnees_simulation = Lecture.lecture_generale(nom_dossier_donnees, callType = 'antigone')
    print("DONNEES LUES\n")
    
    donnees_entree.dossier_sortie = dossier_sortie
    donnees_simulation.dossier_sortie = dossier_sortie

    donnees_simulation.parc.print_parc("Parc initial")
    
    
    if donnees_entree.parametres_simulation.anticipation_parc_exogene :
        for ambiance in donnees_entree.tableau_ambiances :
            parc = donnees_simulation.dico_parcs_anticipes[ambiance.nom]        
            parc.print_parc("Parc anticipation - ambiance : %s"%(ambiance.nom))
        
        matrice_resultats_annuels = Anticipation.anticipation_resultats_annuels_parc_exogene(0,donnees_entree.parametres_simulation.horizon_simulation,
                                                    donnees_entree, donnees_simulation,donnees_simulation.dico_parcs_anticipes)              
        
        Ecriture.ecriture_dispatch_boucle(matrice_resultats_annuels,donnees_entree,donnees_simulation,"dispatch_parc_exogene",0,0)
                    
        
    for annee in range(donnees_entree.parametres_simulation.horizon_simulation):
    
        # market module

        print("ANNEE %d | Market Module"%annee)
        market_module.run_market_module(donnees_entree, donnees_simulation)

        # realisation
        
        print("ANNEE %d | REALISATION" % annee)
        liste_resultats_annuels = Realisation.realisation_annee_courante(donnees_entree, donnees_simulation)

        # incrementaiton annee
        
        print("ANNEE %d TERMINEE" % annee)
        donnees_simulation.incrementation_annee(liste_resultats_annuels)


    # write global summary
    
    path_resume = os.path.join(donnees_entree.dossier_sortie, "resume_general.csv")    
    donnees_simulation.resume_general.to_csv(path_resume,sep=";")

    
    sys.exit()
        
    print("ECRITURE DES FICHIERS DE SORTIE")
    Ecriture.ecriture_generale(donnees_entree, donnees_simulation, nom_dossier_donnees)
    print("SIMULATION TERMINEE : %s"%nom_dossier_donnees)


if __name__ == '__main__':
    temps_debut = time.time()

    liste_noms_dossier_donnees = sys.argv[1:]

    for nom_dossier_donnees in liste_noms_dossier_donnees:
        simulation(nom_dossier_donnees)

    temps_fin = time.time()

    print("Temps d'exécution : ", temps_fin - temps_debut)