# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import DonneesSimulation
import IndicateursEconomiques
import MecanismeCapacite

import pandas as pd
import os
import time
import  numpy as np
import sys
import shutil

def pjoin(*args, **kwargs):
    return os.path.join(*args, **kwargs).replace(os.sep, '//')
    


def ecriture_rapport_boucle_demantelement(chemin_fichier, rapport_boucle_demantelement):
    """
    Ecrit le fichier de sortie décrivant le rapport de boucle de démantèlement à l'emplacement donné.

    Paramètres
    ----------
    chemin_fichier : str
        emplacement dans lequel écrire le fichier de sortie
    rapport_boucle_demantelement : Demantelement.RapportBoucleDemantelement
        rapport de boucle de démantèlement à utiliser
    """

    data_frame_rapport_boucle_demantelement = pd.DataFrame(columns=["actif", "annee_ouverture", "revenu_moyen_terme_equivalent"])

    liste_unites_fermees = rapport_boucle_demantelement.liste_unites_fermees
    data_frame_rapport_boucle_demantelement["actif"] = [unite_fermee.actif.cle for unite_fermee in liste_unites_fermees]
    data_frame_rapport_boucle_demantelement["annee_ouverture"] = [unite_fermee.annee_ouverture for unite_fermee in liste_unites_fermees]
    data_frame_rapport_boucle_demantelement["revenu_moyen_terme_equivalent"] = [rapport_boucle_demantelement.revenu_moyen_terme_equivalent_unites_fermees for unite_fermee in liste_unites_fermees]

    data_frame_rapport_boucle_demantelement.to_csv(chemin_fichier, sep=";")


def ecriture_rapport_demantelement(chemin_dossier, rapport_demantelement):
    """
    Ecrit le dossier de sortie décrivant le rapport de démantèlement dans le dossier donné.

    Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le dossier de sortie
    rapport_demantelement : Demantelement.RapportDemantelement
        rapport de démantèlement à utiliser
    """

    dossier_rapport_demantelement = chemin_dossier + "/rapport_demantelement"
    
    if not os.path.isdir(dossier_rapport_demantelement):
        os.mkdir(dossier_rapport_demantelement)

    for indice_boucle in range(len(rapport_demantelement.liste_rapports_boucle_demantelement)):
        rapport_boucle_demantelement = rapport_demantelement.liste_rapports_boucle_demantelement[indice_boucle]
        ecriture_rapport_boucle_demantelement(dossier_rapport_demantelement + "/boucle_%d.csv"%indice_boucle, rapport_boucle_demantelement)


def ecriture_rapport_boucle_investissement(chemin_fichier, rapport_boucle_investissement):
    """
    Ecrit le fichier de sortie décrivant le rapport de boucle de d'investissement à l'emplacement donné.

    Paramètres
    ----------
    chemin_fichier : str
        emplacement dans lequel écrire le fichier de sortie
    rapport_boucle_investissement : Investissement.RapportBoucleInvestissement
        rapport de boucle d'investissement à utiliser
    """

    liste_cles_actifs = rapport_boucle_investissement.dict_VAN_equivalente.keys()
    data_frame_rapport_boucle_investissement = pd.DataFrame(index=liste_cles_actifs, columns=["VAN equivalente", "revenu equivalent premiere annee de fonctionnement", "critere d'investissement", "choix d'investissement"])

    for cle_actif, VAN_equivalente in rapport_boucle_investissement.dict_VAN_equivalente.items():
        data_frame_rapport_boucle_investissement.loc[cle_actif, "VAN equivalente"] = VAN_equivalente
    for cle_actif, revenu_equivalent_premiere_annee_fonctionnement in rapport_boucle_investissement.dict_revenu_equivalent_premiere_annee_fonctionnement.items():
        data_frame_rapport_boucle_investissement.loc[cle_actif, "revenu equivalent premiere annee de fonctionnement"] = revenu_equivalent_premiere_annee_fonctionnement
    for cle_actif, critere_investissement in rapport_boucle_investissement.dict_critere_investissement.items():
        data_frame_rapport_boucle_investissement.loc[cle_actif, "critere d'investissement"] = critere_investissement

    actif_choisi = rapport_boucle_investissement.actif_choisi
    if actif_choisi:
        data_frame_rapport_boucle_investissement.loc[actif_choisi.cle, "choix d'investissement"] = "%d unites construites"%rapport_boucle_investissement.nombre_unites_investies

    data_frame_rapport_boucle_investissement.to_csv(chemin_fichier, sep=";")


def ecriture_rapport_investissement(chemin_dossier, rapport_investissement):
    """
    Ecrit le dossier de sortie décrivant le rapport d'investissement dans le dossier donné.

    Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le dossier de sortie
    rapport_investissement : Investissement.RapportInvestissement
        rapport d'investissement à utiliser
    """

    dossier_rapport_investissement = chemin_dossier + "/rapport_investissement"
    
    if not os.path.isdir(dossier_rapport_investissement):
        os.mkdir(dossier_rapport_investissement)

    for indice_boucle in range(len(rapport_investissement.liste_rapports_boucle_investissement)):
        rapport_boucle_investissement = rapport_investissement.liste_rapports_boucle_investissement[indice_boucle]
        ecriture_rapport_boucle_investissement(dossier_rapport_investissement + "/boucle_%d.csv" % indice_boucle, rapport_boucle_investissement)

    data_frame_ressources_restantes = pd.DataFrame(columns=["capacite restante", "argent restant"])
    data_frame_ressources_restantes["capacite restante"] = [rapport_investissement.puissance_restante]
    data_frame_ressources_restantes["argent restant"] = [rapport_investissement.argent_restant]
    data_frame_ressources_restantes.to_csv(dossier_rapport_investissement + "/ressources_restantes.csv", sep=";")


def ecriture_appel_offres_investissement(chemin_fichier, appel_offres_investissement):
    """
    Ecrit le fichier de sortie décrivant l'appel d'offres d'investissement à l'emplacement donné.

    Paramètres
    ----------
    chemin_fichier : str
        emplacement dans lequel écrire le fichier de sortie
    appel_offres_investissement : AppelsOffresInvestissement.AppelOffresInvestissement
        appel d'offres d'investissement à utiliser
    """

    data_frame_appel_offres_investissement = pd.DataFrame(columns=["actif", "nombre_unites", "categorie_contrat", "annee_emission",  "annee_debut_contrat", "annee_fin_contrat"])

    contrat = appel_offres_investissement.contrat
    actif = appel_offres_investissement.actif
    nombre_unites = appel_offres_investissement.nombre_unites_actif
    data_frame_appel_offres_investissement["actif"] = [actif.cle]
    data_frame_appel_offres_investissement["nombre_unites"] = [nombre_unites]
    data_frame_appel_offres_investissement["categorie_contrat"] = [contrat.categorie]
    data_frame_appel_offres_investissement["annee_emission"] = [contrat.annee_emission]
    data_frame_appel_offres_investissement["annee_debut_contrat"] = [contrat.annee_debut]
    data_frame_appel_offres_investissement["annee_fin_contrat"] = [contrat.annee_fin]

    if(contrat.categorie == "contrat_pour_difference"):
        data_frame_appel_offres_investissement["prix_contractuel"] = [contrat.prix_contractuel]
    elif(contrat.categorie == "contrat_parfait"):
        data_frame_appel_offres_investissement["LCOE"] = [contrat.montant_remuneration]

    data_frame_appel_offres_investissement.to_csv(chemin_fichier, sep=';')

def ecriture_rapport_appels_offres_investissement(chemin_dossier, rapport_appels_offres_investissement):
    """
    Ecrit le dossier de sortie décrivant le rapport d'appels d'offres d'investissement dans le dossier donné.

    Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le dossier de sortie
    rapport_appels_offres_investissement : AppelsOffresInvestissement.RapportAppelsOffresInvestissement
        rapport d'appels d'offres d'investissement à utiliser
    """

    dossier_rapport_appels_offres_investissement = chemin_dossier + "/rapport_appels_offres_investissement"
    if not os.path.isdir(dossier_rapport_appels_offres_investissement):
        os.mkdir(dossier_rapport_appels_offres_investissement)

    for indice_appel_offres in range(len(rapport_appels_offres_investissement.liste_appels_offres_investissement)):
        appel_offres_investissement = rapport_appels_offres_investissement.liste_appels_offres_investissement[indice_appel_offres]
        ecriture_appel_offres_investissement(dossier_rapport_appels_offres_investissement + "/appel_offres_%d.csv" % indice_appel_offres, appel_offres_investissement)

    data_frame_ressources_restantes = pd.DataFrame(columns=["capacite restante", "argent restant"])
    data_frame_ressources_restantes["capacite restante"] = [rapport_appels_offres_investissement.puissance_restante]
    data_frame_ressources_restantes["argent restant"] = [rapport_appels_offres_investissement.argent_restant]
    data_frame_ressources_restantes.to_csv(dossier_rapport_appels_offres_investissement + "/ressources_restantes.csv", sep=";")


def ecriture_appel_offres_demantelement(chemin_fichier, appel_offres_demantelement):
    """
    Ecrit le fichier de sortie décrivant l'appel d'offres de démantèlement à l'emplacement donné.

    Paramètres
    ----------
    chemin_fichier : str
        emplacement dans lequel écrire le fichier de sortie
    appel_offres_demantelement : AppelsOffresDemantelement.AppelOffresDemantelement
        appel d'offres de démantèlement à utiliser
    """

    data_frame_appel_offres_demantelement = pd.DataFrame(columns=["actif", "nombre_unites", "prix"])
    data_frame_appel_offres_demantelement["actif"] = [appel_offres_demantelement.actif.cle]
    data_frame_appel_offres_demantelement["nombre_unites"] = [appel_offres_demantelement.nombre_unites_actif]
    data_frame_appel_offres_demantelement["prix"] = [appel_offres_demantelement.prix]
    data_frame_appel_offres_demantelement.to_csv(chemin_fichier, sep=';')

def ecriture_rapport_appels_offres_demantelement(chemin_dossier, rapport_appels_offres_demantelement):
    """
    Ecrit le dossier de sortie décrivant le rapport d'appels d'offres de démantèlement dans le dossier donné.

    Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le dossier de sortie
    rapport_appels_offres_demantelement : AppelsOffresDemantelement.RapportAppelsOffresDemantelement
        rapport d'appels d'offres de démantèlement à utiliser
    """

    dossier_rapport_appels_offres_demantelement = chemin_dossier + "/rapport_appels_offres_demantelement"
    
    if not os.path.isdir(dossier_rapport_appels_offres_demantelement):
        os.mkdir(dossier_rapport_appels_offres_demantelement)

    for indice_appel_offres in range(len(rapport_appels_offres_demantelement.liste_appels_offres_demantelement)):
        appel_offres_demantelement = rapport_appels_offres_demantelement.liste_appels_offres_demantelement[indice_appel_offres]
        ecriture_appel_offres_demantelement(dossier_rapport_appels_offres_demantelement + "/appel_offres_%d.csv" % indice_appel_offres, appel_offres_demantelement)

    data_frame_ressources_restantes = pd.DataFrame(columns=["argent restant"])
    data_frame_ressources_restantes["argent restant"] = [rapport_appels_offres_demantelement.argent_restant]
    data_frame_ressources_restantes.to_csv(dossier_rapport_appels_offres_demantelement+ "/ressources_restantes.csv", sep=";")

####################################################################################################################################################
################### Pour l'instant une seule enchère donc il n'y a qu'une seule boucle, mais cela pourra servir lorsqu'il y aura plusieurs enchère  
def ecriture_rapport_boucle_mecanisme_capacite(chemin_fichier, rapport_boucle_mecanisme_capacite):
    """
    Ecrit le fichier de sortie décrivant le rapport de boucle du mécanisme de capacité à l'emplacement donné.

    Paramètres
    ----------
    chemin_fichier : str
        emplacement dans lequel écrire le fichier de sortie
    rapport_boucle_mecanisme_capacite : MecanismeCapacite.RapportBoucleMecanisme de capacité
        rapport de boucle du mécanisme de capacité à utiliser
    """

    data_frame_rapport_boucle_mecanisme_capacite = pd.DataFrame(columns=["actif", "annee_ouverture", "revenu_moyen_terme_equivalent"])




def ecriture_rapport_mecanisme_capacite(chemin_dossier, dict_rapport_annuel_mecanisme_capacite):
    """
    Ecrit le dossier de sortie décrivant le rapport du mécanisme de capacité dans le dossier donné.

    Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le dossier de sortie
    dict_rapport_annuel_mecanisme_capacite : dict
        dictionnaire contenant pour chaque année de livraison un rapport du Mecanisme de capacité 
    """
    for annee_livraison in dict_rapport_annuel_mecanisme_capacite : 
        dossier_rapport_mecanisme_capacite = chemin_dossier + "/annee_%d/rapport_mecanisme_capacite"%annee_livraison
    
        
        
        rapport_mecanisme_capacite = dict_rapport_annuel_mecanisme_capacite[annee_livraison]
        
        if rapport_mecanisme_capacite.df_actifs_non_laureats.empty : 
            continue
        
        if not os.path.isdir(dossier_rapport_mecanisme_capacite):
            os.makedirs(dossier_rapport_mecanisme_capacite)
        
        rapport_mecanisme_capacite.df_actifs_non_laureats.to_csv(dossier_rapport_mecanisme_capacite + "/actifs_non_laureats.csv", sep=";")
        rapport_mecanisme_capacite.df_actifs_laureats.to_csv(dossier_rapport_mecanisme_capacite + "/actifs_laureats.csv", sep=";")
        
        resultats_generaux_enchere = pd.DataFrame(index = [rapport_mecanisme_capacite.annee_courante])
        resultats_generaux_enchere['annee_livraison'] = rapport_mecanisme_capacite.annee_livraison
        resultats_generaux_enchere['quantite_capacite'] = rapport_mecanisme_capacite.quantite_capacite
        resultats_generaux_enchere['prix_capacite'] = rapport_mecanisme_capacite.prix_capacite
        
        resultats_generaux_enchere.to_csv(dossier_rapport_mecanisme_capacite + "/resultats_generaux_enchere.csv", sep=";")
        
        #for indice_boucle in range(len(rapport_demantelement.liste_rapports_boucle_demantelement)):
            #rapport_boucle_demantelement = rapport_demantelement.liste_rapports_boucle_demantelement[indice_boucle]
            #ecriture_rapport_boucle_demantelement(dossier_rapport_demantelement + "/boucle_%d.csv"%indice_boucle, rapport_boucle_demantelement)  
    
def ecriture_resultat_annuel(chemin_fichier, resultat_annuel):
    """
    Ecrit le fichier de sortie décrivant le résultat de dispatch annuel à l'emplacement donné.

    Paramètres
    ----------
    chemin_fichier : str
        emplacement dans lequel écrire le fichier de sortie
    resultat_annuel : DispatchV0.ResultatAnnuel
        résultat de dispatch annuel à utiliser
    """

    resultat_annuel.data_frame_resultat_annuel.to_csv(chemin_fichier, sep=";")

    
def ecriture_dispatch_CFD(matrice_resultats_annuels,donnees_entree,donnees_simulation,annee_anticipee):

    """
    
    Ecrit les résultats de dispatch associés à une anticipation donnée dans le cadre de
    la construction d'un contrat pour difference
    (i.e. retour de la fonction Anticipation.anticipation_resultats_annuels).
    
    """
    
    annee_courante = donnees_simulation.annee_courante
    
    
    for idxAmbiance,nom in enumerate(donnees_entree.ambiances) : 

        nbAnnees = len(matrice_resultats_annuels[idxAmbiance])
        
        for annee in range(nbAnnees):
        
            nbMeteo = len(matrice_resultats_annuels[idxAmbiance][annee])
            
            for meteo in range(nbMeteo):
                  
                dossier_dispatch = os.path.join(donnees_entree.dossier_sortie,"Dispatch","annee_"+ str(annee_courante),"AO_" + str(annee_anticipee))
                
                if not os.path.isdir(dossier_dispatch):
                    os.makedirs(dossier_dispatch)
                    
                nom_fichier = "%s_annee_%s_meteo_%s.csv"%(nom,str(annee_anticipee+annee),str(meteo))
                chemin_fichier = os.path.join(dossier_dispatch,nom_fichier)   
                
                ecriture_resultat_annuel(chemin_fichier,matrice_resultats_annuels[idxAmbiance][annee][meteo])    

    return None

    
    
def ecriture_dispatch_boucle(matrice_resultats_annuels,donnees_entree,donnees_simulation,boucle,nb_iter,premiere_annee_matrice,unite=None):

    """
    
    Ecrit les résultats de dispatch associés à une anticipation donnée dans le cadre de
    la construction d'un contrat pour difference
    (i.e. retour de la fonction Anticipation.anticipation_resultats_annuels).
    
    boucle : "demantelement" ou "investissement"
    nb_iter : numéro de l'itération pour l'année courante
    unite : durant les boucles d'investissement, nom de la techno testée
    """
    
    annee_courante = donnees_simulation.annee_courante
    
    
    for idxAmbiance,nom in enumerate(donnees_entree.ambiances) : 

        
        nbAnnees = len(matrice_resultats_annuels[idxAmbiance])
        
        for annee in range(nbAnnees):
        
            nbMeteo = len(matrice_resultats_annuels[idxAmbiance][annee])
            
            for meteo in range(nbMeteo):
                  
                dossier_dispatch = os.path.join(donnees_entree.dossier_sortie,"annee_"+ str(annee_courante),boucle,str(nb_iter))
                
                if not os.path.isdir(dossier_dispatch):
                    os.makedirs(dossier_dispatch)
                    
                num_annee = premiere_annee_matrice + annee
                
                if unite == None : 
                    nom_fichier = "%s_annee_%s_meteo_%s.csv"%(nom,str(num_annee),str(meteo))
                else : 
                    nom_fichier = "%s_annee_%s_meteo_%s_unite_%s.csv"%(nom,str(num_annee),str(meteo),unite)
                    
                chemin_fichier = os.path.join(dossier_dispatch,nom_fichier)   
                ecriture_resultat_annuel(chemin_fichier,matrice_resultats_annuels[idxAmbiance][annee][meteo])    

    return None
    
    
def ecriture_realisation(chemin_dossier, liste_resultats_annuels):
    """
    Ecrit le dossier de sortie décrivant la réalisation dans le dossier donné.

    Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le dossier de sortie
    liste_resultats_annuels : list
        liste des résultats de dispatch annuels à utiliser
    """

    dossier_realisation = chemin_dossier + "/realisation"
    
    if not os.path.isdir(dossier_realisation):
        os.mkdir(dossier_realisation)

    for indice_meteo in range(len(liste_resultats_annuels)):
        resultat_annuel = liste_resultats_annuels[indice_meteo]
        ecriture_resultat_annuel(dossier_realisation + "/meteo_%d.csv"%indice_meteo, resultat_annuel)


def ecriture_compte_unites(chemin_dossier, donnees_entree, donnees_simulation):
    """
    Ecrit le fichier de sortie décrivant l'évolution du compte des unités au cours de la simulation dans le dossier
    donné.

    Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le fichier de sortie
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    """

    fichier_compte_unites = chemin_dossier + "/compte_unites.csv"

    liste_cles_actifs = [actif.cle for actif in donnees_entree.tous_actifs()]
    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation

    data_frame_compte_unites = pd.DataFrame(index=liste_cles_actifs, columns=range(horizon_simulation))

    for actif in donnees_entree.tous_actifs():
        for annee in range(horizon_simulation):
            data_frame_compte_unites.loc[actif.cle].iat[annee] = donnees_simulation.parc.nombre_unites(actif.cle, annee)

    data_frame_compte_unites.to_csv(fichier_compte_unites, sep=";")

def ecriture_compte_capacites(chemin_dossier, donnees_entree, donnees_simulation):
    """
    Ecrit le fichier de sortie décrivant l'évolution du compte des capacités de production installées au cours de la
    simulation dans le dossier donné.

    Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le fichier de sortie
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    """

    fichier_compte_capacites = chemin_dossier + "/compte_capacites.csv"

    liste_cles_actifs = [actif.cle for actif in donnees_entree.tous_actifs()]
    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation

    data_frame_compte_capacites = pd.DataFrame(index=liste_cles_actifs, columns=range(horizon_simulation))

    for actif in donnees_entree.tous_actifs():
        puissance = 0
        if actif.categorie == "Stockage":
            puissance = actif.puissance_nominale_decharge
        elif actif.categorie == "Pilotable":
            puissance = actif.puissance_nominale
        elif actif.categorie == "ENR":
            puissance = actif.puissance_reference
        for annee in range(horizon_simulation):
            data_frame_compte_capacites.loc[actif.cle].iat[annee] = donnees_simulation.parc.nombre_unites(actif.cle, annee) * puissance

    data_frame_compte_capacites.to_csv(fichier_compte_capacites, sep=";")


def ecriture_registres_ouvertures_fermeture(chemin_dossier, donnees_entree, donnees_simulation):
    """
    Ecrit les fichiers de sortie décrivant, respectivement, les registres d'ouvertures et de fermetures au cours de la
    simulation, dans le dossier donné.

    Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le fichier de sortie
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    """

    fichier_registre_ouvertures = chemin_dossier + "/registre_ouvertures.csv"
    fichier_registre_fermetures = chemin_dossier + "/registre_fermetures.csv"

    liste_cles_actifs = [actif.cle for actif in donnees_entree.tous_actifs()]
    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation

    data_frame_registre_ouvertures = pd.DataFrame(index=liste_cles_actifs, columns=range(horizon_simulation))
    data_frame_registre_fermetures = pd.DataFrame(index=liste_cles_actifs, columns=range(horizon_simulation))

    # mise à zéro des compteurs d'ouvertures et de fermetures
    for cle_actif in liste_cles_actifs:
        for annee in range(horizon_simulation):
            data_frame_registre_fermetures.loc[cle_actif].iat[annee] = 0
            data_frame_registre_ouvertures.loc[cle_actif].iat[annee] = 0

    liste_toutes_unites = donnees_simulation.parc.toutes_unites()

    for unite in liste_toutes_unites:
        cle_actif = unite.actif.cle
        annee_ouverture = unite.annee_ouverture
        annee_fermeture = unite.annee_fermeture
        if(annee_ouverture < horizon_simulation):
            data_frame_registre_ouvertures.loc[cle_actif].iat[annee_ouverture] += 1
        if (annee_fermeture < horizon_simulation):
            data_frame_registre_fermetures.loc[cle_actif].iat[annee_fermeture] += 1

    data_frame_registre_fermetures.to_csv(fichier_registre_fermetures, sep=";")
    data_frame_registre_ouvertures.to_csv(fichier_registre_ouvertures, sep=";")


def ecriture_registres_ouvertures_fermetures_appels_offres(chemin_dossier, donnees_entree, donnees_simulation):
    """
    Ecrit les fichiers de sortie décrivant, respectivement, les registres d'ouvertures et de fermetures dues aux appels
    d'offres au cours de la simulation, dans le dossier donné.

    Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le fichier de sortie
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    """

    fichier_registre_ouvertures_appels_offres = chemin_dossier + "/registre_ouvertures_appels_offres.csv"
    fichier_registre_fermetures_appels_offres = chemin_dossier + "/registre_fermetures_appels_offres.csv"

    liste_cles_actifs = [actif.cle for actif in donnees_entree.tous_actifs()]
    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation

    data_frame_registre_ouvertures_appels_offres = pd.DataFrame(index=liste_cles_actifs, columns=range(horizon_simulation))
    data_frame_registre_fermetures_appels_offres = pd.DataFrame(index=liste_cles_actifs, columns=range(horizon_simulation))

    # mise à zéro des compteurs d'ouvertures et de fermetures
    for cle_actif in liste_cles_actifs:
        for annee in range(horizon_simulation):
            data_frame_registre_fermetures_appels_offres.loc[cle_actif].iat[annee] = 0
            data_frame_registre_ouvertures_appels_offres.loc[cle_actif].iat[annee] = 0

    for rapport_appels_offres_investissement in donnees_simulation.liste_rapports_appels_offres_investissement:
        for appel_offres_investissement in rapport_appels_offres_investissement.liste_appels_offres_investissement:
            cle_actif = appel_offres_investissement.actif.cle
            nombre_unites = appel_offres_investissement.nombre_unites_actif
            annee_ouverture = appel_offres_investissement.contrat.annee_debut
            if (annee_ouverture < horizon_simulation):
                data_frame_registre_ouvertures_appels_offres.loc[cle_actif].iat[annee_ouverture] += nombre_unites

    for annee in range(len(donnees_simulation.liste_rapports_appels_offres_demantelement)):
        rapport_appels_offres_demantelement = donnees_simulation.liste_rapports_appels_offres_demantelement[annee]
        for appel_offres_demantelement in rapport_appels_offres_demantelement.liste_appels_offres_demantelement:
            cle_actif = appel_offres_demantelement.actif.cle
            nombre_unites = appel_offres_demantelement.nombre_unites_actif
            if (annee < horizon_simulation):
                data_frame_registre_fermetures_appels_offres.loc[cle_actif].iat[annee] += nombre_unites

    data_frame_registre_fermetures_appels_offres.to_csv(fichier_registre_fermetures_appels_offres, sep=";")
    data_frame_registre_ouvertures_appels_offres.to_csv(fichier_registre_ouvertures_appels_offres, sep=";")


def ecriture_registre_prix_contractuels_contrats_pour_difference(chemin_dossier, donnees_entree, donnees_simulation):
    """
    Ecrit le fichier de sortie détaillant les prix contractuels des contrats pour différence le cas échéant.

     Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le fichier de sortie
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    """
    if donnees_entree.parametres_simulation.architecture == "AOCLT":

        horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation
        horizon_prevision = donnees_entree.parametres_simulation.horizon_prevision
        data_frame_registre_prix_contractuels = pd.DataFrame(index=[actif.cle for actif in donnees_entree.tous_actifs()], columns=["annee_%d"%annee for annee in range(horizon_simulation + horizon_prevision)])
        for annee in range(horizon_simulation):
            for appel_offres_investissement in donnees_simulation.liste_rapports_appels_offres_investissement[annee].liste_appels_offres_investissement:
                actif = appel_offres_investissement.actif
                contrat_pour_difference = appel_offres_investissement.contrat
                prix_contractuel = contrat_pour_difference.prix_contractuel
                annee_debut_contrat = contrat_pour_difference.annee_debut
                data_frame_registre_prix_contractuels.loc[actif.cle, "annee_%d"%annee_debut_contrat] = prix_contractuel

        fichier_registre_prix_contractuels = chemin_dossier + "/registre_prix_contractuels.csv"
        data_frame_registre_prix_contractuels.to_csv(fichier_registre_prix_contractuels, sep=";")


def ecriture_registre_contribution_capacitaire(dossier_sortie, donnees_entree, donnees_simulation) : 
    """
    Ecrit le fichier de sortie détaillant la contribution de chaque type d'actif à la pointe hivernale.

     Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le fichier de sortie
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    """
    realisation = donnees_entree.realisation
    
    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation
    df_ponderation = donnees_entree.df_parametres_ponderation

    liste_cles_actifs = [actif.cle for actif in donnees_entree.tous_actifs()]
    df_capacites_parc = pd.DataFrame(index=liste_cles_actifs, columns=range(horizon_simulation))

    for actif in donnees_entree.tous_actifs():
        puissance = 0
        if actif.categorie == "Stockage":
            puissance = actif.puissance_nominale_decharge
        elif actif.categorie == "Pilotable":
            puissance = actif.puissance_nominale
        elif actif.categorie == "ENR":
            puissance = actif.puissance_reference
        for annee in range(horizon_simulation):
            df_capacites_parc.loc[actif.cle].iat[annee] = donnees_simulation.parc.nombre_unites(actif.cle, annee) * puissance
    
    df_contribution_capacitaire = pd.DataFrame(index=liste_cles_actifs, columns=range(horizon_simulation))
       
    for actif in donnees_entree.tous_actifs() :
        
        capa_pointe_actif = []
        
        for annee in range (horizon_simulation) :
            
            disponibilite_annee = pd.DataFrame([0 for k in range(8760)], columns = ["Annee_%d"%annee])["Annee_%d"%annee]
            
            for meteo in [meteo for meteo in realisation.keys()][1:]  : 

                indice_meteo = int(meteo[-1])
                dispo_pilot_meteo = realisation[meteo]["dispo"]
                facteur_charge_enr_meteo = realisation[meteo]["fc"]        
                
                if actif.categorie == "Pilotable":
                    try :
                        disponibilite_annee += dispo_pilot_meteo["%s_%d"%(actif.cle, annee)] * df_ponderation.at[indice_meteo, "value"]
                    except KeyError:
                        disponibilite_annee += pd.DataFrame([1 for k in range(8760)], columns = ["Annee_%d"%annee])["Annee_%d"%annee] * df_ponderation.at[indice_meteo, "value"]
                elif actif.categorie == "ENR":
                    try : 
                        disponibilite_annee += facteur_charge_enr_meteo["%s_%d"%(actif.cle, annee)] * df_ponderation.at[indice_meteo, "value"]
                    except KeyError:
                        disponibilite_annee += pd.DataFrame([1 for k in range(8760)], columns = ["Annee_%d"%annee])["Annee_%d"%annee] * df_ponderation.at[indice_meteo, "value"]
            
            disponibilite_moyenne = disponibilite_annee.mean()
            
            contribution_pointe_actif = df_capacites_parc.at[actif.cle, annee] * disponibilite_moyenne
        
            df_contribution_capacitaire.loc[actif.cle].iat[annee] = contribution_pointe_actif
    
    fichier_contribution_capacitaire = dossier_sortie + "/registre_contribution_capacitaire.csv"
    
    df_contribution_capacitaire.to_csv(fichier_contribution_capacitaire, sep=";")
    
    
def ecriture_entrees_gep(donnees_entree, donnees_simulation):

    dossier_sortie = donnees_entree.dossier_sortie
    
    annee_courante = donnees_simulation.annee_courante
    
    chemins_gep = []
    
    for indice_ambiance,ambiance in enumerate(donnees_entree.ambiances):
    
        entrees_gep = pjoin(dossier_sortie,"INPUT_GEP_%d_%s"%(annee_courante,ambiance))
        os.makedirs(entrees_gep)
        
        chemins_gep.append(entrees_gep)
        
        # copie du repertoire actif
        
        src = pjoin(donnees_entree.chemin_dossier,"Actifs")
        dst = pjoin(entrees_gep,"Actifs")
        shutil.copytree(src,dst)
        
        # copie du repertoire parametres

        src = pjoin(donnees_entree.chemin_dossier,"Parametres")
        dst = pjoin(entrees_gep,"Parametres")
        shutil.copytree(src,dst)    
        
        # modif du nombre d'années dans parametres
        
        path = pjoin(entrees_gep,"Parametres","parametres_simulation.csv")
        df_param = pd.read_csv(path,sep=";",index_col=0)
        
        horizon_total = int(df_param.at["horizon_simulation","value"])
        
        df_param_modif = df_param.copy()
        df_param_modif.at["horizon_simulation","value"] = int( horizon_total - annee_courante)
        df_param_modif.to_csv(path,sep=";")
        
        # copie du repertoire realisation

        src = pjoin(donnees_entree.chemin_dossier,"Ambiances",ambiance,"Annee_%d"%annee_courante)
        dst = pjoin(entrees_gep,"Realisation")
        shutil.copytree(src,dst)
        
        # modif des colonnes 
        
        ## CCC
        
        path = pjoin(entrees_gep,"Realisation","couts_combustibles_et_carbone.csv")
        df_ccc = pd.read_csv(path,sep=";",index_col = 0)
        
        cols = ["Annee_%d"%n for n in np.arange(annee_courante,horizon_total)]
        df_ccc = df_ccc[cols]
        
        cols_rename = ["Annee_%d"%n for n in (np.arange(annee_courante,horizon_total) - annee_courante  )]
        df_ccc.columns = cols_rename
        
        df_ccc.to_csv(path,sep=";")
        
        for indice_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
        
            ## Demande
            
            path = pjoin(entrees_gep,"Realisation","meteo_%d"%indice_meteo,"demande.csv")
            df_demande = pd.read_csv(path,sep=";",index_col=0)
            df_demande = df_demande[cols]
            df_demande.columns = cols_rename
            df_demande.to_csv(path,sep=";")
            
            ## Disponibilite

            path = pjoin(entrees_gep,"Realisation","meteo_%d"%indice_meteo,"disponibilite_pilot.csv")
            df_dispo_pilot = pd.read_csv(path,sep=";",index_col=0)
            
            
            list_tech = np.unique([ "_".join(col.split("_")[:-1]) for col in df_dispo_pilot.columns])
            
            cols = [tech + "_%d"%n  for tech in list_tech for n in range(annee_courante,horizon_total) ]
            
            df_dispo_pilot = df_dispo_pilot[cols]
            
            
            cols_rename = [tech + "_%d"%n  for tech in list_tech for n in (np.arange(annee_courante,horizon_total) - annee_courante) ]
            df_dispo_pilot.columns = cols_rename
            
            df_dispo_pilot.to_csv(path,sep=";")
            
            
            ### EnR
            
            path = pjoin(entrees_gep,"Realisation","meteo_%d"%indice_meteo,"facteurs_production_ENR.csv")
            df_enr = pd.read_csv(path,sep=";",index_col=0)
            
            
            list_tech = np.unique([ "_".join(col.split("_")[:-1]) for col in df_enr.columns])
            
            cols = [tech + "_%d"%n  for tech in list_tech for n in np.arange(annee_courante,horizon_total) ]
            
            df_enr = df_enr[cols]
            cols_rename = [tech + "_%d"%n  for tech in list_tech for n in (np.arange(annee_courante,horizon_total) - annee_courante) ]
            df_enr.columns = cols_rename

            df_enr.to_csv(path,sep=";")
            
            
            
        
        # copie du repertoire GenerationMixCible

        src = pjoin(donnees_entree.chemin_dossier,"GenerationMixCible")
        dst = pjoin(entrees_gep,"GenerationMixCible")
        shutil.copytree(src,dst)    
        
        # modif des colonnes
        
        #### contraintes trajectoires
        
        path = pjoin(entrees_gep,"GenerationMixCible","contraintes_trajectoire.csv")
        df_contraintes_traj = pd.read_csv(path,sep=";",index_col=0)
        
        cols = ["type_contrainte","grandeur_concernee"] + ["annee_%d"%n for n in np.arange(annee_courante,horizon_total)]
        df_contraintes_traj = df_contraintes_traj[cols]

        df_contraintes_traj.columns = ["type_contrainte","grandeur_concernee"] + ["annee_%d"%n for n in (np.arange(annee_courante,horizon_total)-annee_courante)]
        df_contraintes_traj.to_csv(path,sep=";")
        
        #### contraintes CO2
        
        path = pjoin(entrees_gep,"GenerationMixCible","co2_quota.csv")
        df_quota = pd.read_csv(path,sep=";",index_col=0)
        
        rows = ["Annee_%d"%n for n in np.arange(annee_courante,horizon_total)]
        df_quota = df_quota.loc[rows]
        df_quota["CO2_quota"] = "inf"
        df_quota.index = ["Annee_%d"%n for n in (np.arange(annee_courante,horizon_total) - annee_courante)]
        
        df_quota.to_csv(path,sep=";")
        
        
        
                
        # repertoire parc
        
        path_rep_parc = pjoin(entrees_gep,"Parc")
        os.makedirs(path_rep_parc)
        
        df_parc = donnees_simulation.parc.get_df_nb_unites()
        
        path = pjoin(entrees_gep,"Parc","parc_initial.csv")
        df_parc_initial = df_parc.loc[annee_courante].T.astype(int)
        df_parc_initial = df_parc_initial.rename("nombre")
        df_parc_initial.to_csv(path,sep=";")

        
        df_parc = df_parc.loc[annee_courante:]
        df_parc.index = df_parc.index.to_numpy() - annee_courante
        
        
        df_rythme = df_parc.diff().fillna(0)
        
        df_rythme_ouverture = df_rythme.clip(lower=0).T.astype(int)
        df_rythme_fermeture = -1* df_rythme.clip(upper=0).T.astype(int)
                
        path_ouverture = pjoin(entrees_gep,"Parc","registre_ouvertures.csv")
        df_rythme_ouverture.to_csv(path_ouverture,sep=";")
        
        path_fermeture = pjoin(entrees_gep,"Parc","registre_fermetures.csv")
        df_rythme_fermeture.to_csv(path_fermeture,sep=";")

   

    return chemins_gep
    

def ecriture_registres_generaux(chemin_dossier, donnees_entree, donnees_simulation):
    """
    Ecrit les fichiers de sortie regroupant les données annuelles générales dans le dossier donné.

    Paramètres
    ----------
    chemin_dossier : str
        emplacement du dossier dans lequel écrire le fichier de sortie
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    """

    strike_price_RO = 300
      
    fichier_registre_energie = chemin_dossier + "/registre_energie.csv"
    fichier_registre_economique = chemin_dossier + "/registre_economique.csv"

    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation
    df_ponderation = donnees_entree.df_parametres_ponderation

    data_frame_registre_energie = pd.DataFrame(index=["annee_%d" % annee for annee in range(horizon_simulation)])
    data_frame_registre_economique = pd.DataFrame(index=["annee_%d"%annee for annee in range(horizon_simulation)])
    
    if donnees_entree.parametres_simulation.mecanisme_capacite :
        dict_rapports_mecanisme_capacite = donnees_simulation.dict_rapports_mecanisme_capacite
        dict_traitement = {}
        for annee_courante in dict_rapports_mecanisme_capacite :
            dict_rapport_annuel_mecanisme_capacite = dict_rapports_mecanisme_capacite[annee_courante]
            for annee_livraison in dict_rapport_annuel_mecanisme_capacite :
                rapport_mecanisme_capacite = dict_rapport_annuel_mecanisme_capacite[annee_livraison]
                dict_traitement[annee_livraison] = rapport_mecanisme_capacite
        dict_rapports_mecanisme_capacite = dict_traitement  
    
    dict_energie_produite = dict()
    dict_remuneration = dict()
    dict_remuneration_RO = dict()
    dict_remuneration_capacitaire = dict()
    dict_cout_variable = dict()
    dict_cout_investissement_IDC_annualise = dict()
    dict_cout_investissement_IDC_annualise_hors_marche = dict()
    dict_cout_maintenance = dict()
    prix_capacite = []
    for actif in donnees_entree.tous_actifs():
        dict_energie_produite[actif.cle] = np.zeros(horizon_simulation)
        dict_remuneration[actif.cle] = np.zeros(horizon_simulation)
        dict_remuneration_RO[actif.cle] = np.zeros(horizon_simulation)
        dict_remuneration_capacitaire[actif.cle] = np.zeros(horizon_simulation)
        dict_cout_variable[actif.cle] = np.zeros(horizon_simulation)
        dict_cout_investissement_IDC_annualise[actif.cle] = np.zeros(horizon_simulation)
        dict_cout_investissement_IDC_annualise_hors_marche[actif.cle] = np.zeros(horizon_simulation)
        dict_cout_maintenance[actif.cle] = np.zeros(horizon_simulation)


    dict_ecretement = dict()
    for actif_ENR in donnees_entree.actifs_ENR():
        dict_ecretement[actif_ENR.cle] = np.zeros(horizon_simulation)
    dict_charge = dict()
    for actif_stockage in donnees_entree.actifs_stockage():
        dict_charge[actif_stockage.cle] = np.zeros(horizon_simulation)
    demande_totale = np.zeros(horizon_simulation)

    defaillance = np.zeros(horizon_simulation)
    heures_defaillance = np.zeros(horizon_simulation)
    cout_defaillance = np.zeros(horizon_simulation)

    prix_spot_moyen = np.zeros(horizon_simulation)

    prix_carbone = np.zeros(horizon_simulation)
    prix_certificats_verts = np.zeros(horizon_simulation)

    cout_variable_total = np.zeros(horizon_simulation)
    cout_maintenance = np.zeros(horizon_simulation)
    cout_investissement_one_shot = np.zeros(horizon_simulation)
    cout_investissement_IDC_annualise = np.zeros(horizon_simulation)
    cout_investissement_one_shot_hors_marche = np.zeros(horizon_simulation)
    cout_investissement_IDC_annualise_hors_marche = np.zeros(horizon_simulation)
    cout_financement_contrats = np.zeros(horizon_simulation)

    emissions_carbone = np.zeros(horizon_simulation)

    
    donnees_couts_var = donnees_entree.realisation["couts_combustibles"]
    
        
    for annee in range(horizon_simulation):

        liste_resultats_annuels = donnees_simulation.matrice_resultats_annuels[annee]
        nombre_meteos = donnees_entree.parametres_simulation.nb_meteo

        demande_totale_moyenne_annee = 0
        for indice_meteo in range(nombre_meteos):
            donnees_dispatch = donnees_entree.realisation["meteo_%d"%indice_meteo]
            demande = donnees_dispatch["demande"]["Annee_%d"%annee].sum()
            demande_totale_moyenne_annee += demande * df_ponderation.at[indice_meteo, "value"]
        demande_totale[annee] = demande_totale_moyenne_annee

        for actif in donnees_entree.tous_actifs():

            cout_variable_actif = 0
            if actif.categorie == "Pilotable":
            
                cle = actif.cle
                
                combu = actif.combustible
                rend = actif.rendement
                coef_emi = actif.emission_carbone
                
                cout_combu = donnees_couts_var.at[combu,"Annee_%d"%annee ]
                cout_carbone = donnees_couts_var.at["cout_CO2","Annee_%d"%annee ]
                
                cout_variable_actif =  ((1/rend)*cout_combu) + (coef_emi*cout_carbone) 
            
            elif actif.categorie == "ENR":
                cout_variable_actif = actif.cout_variable
            elif actif.categorie == "Stockage":
                cout_variable_actif = actif.cout_variable

            somme_productions_actif = 0
            somme_nombre_heures_production_actif = 0
            somme_remunerations_actif = 0
            somme_remunerations_RO_actif = 0
            somme_couts_variables_actif = 0
            for indice_meteo in range(nombre_meteos):

                resultat_annuel = liste_resultats_annuels[indice_meteo]    
                cout_marginal_RO = np.clip(resultat_annuel.cout_marginal, 0, strike_price_RO)

                production_actif = resultat_annuel.production[actif.cle]

                somme_productions_actif += np.sum(production_actif) * df_ponderation.at[indice_meteo, "value"]
                somme_nombre_heures_production_actif += np.sum(production_actif > 0) * df_ponderation.at[indice_meteo, "value"]
                somme_remunerations_actif += np.sum(resultat_annuel.cout_marginal*production_actif) * df_ponderation.at[indice_meteo, "value"]
                somme_remunerations_RO_actif += np.sum(cout_marginal_RO*production_actif) * df_ponderation.at[indice_meteo, "value"]
                
                if actif.categorie == "Stockage":
                    charge_actif = resultat_annuel.charge[actif.cle]
                    somme_couts_variables_actif += np.sum(cout_variable_actif * production_actif + resultat_annuel.cout_marginal * charge_actif ) * df_ponderation.at[indice_meteo, "value"]
                elif actif.categorie == "Pilotable" or "ENR":
                    somme_couts_variables_actif += np.sum(cout_variable_actif * production_actif) * df_ponderation.at[indice_meteo, "value"]

            # moyenne sur les météos
            dict_energie_produite[actif.cle][annee] = somme_productions_actif
            dict_remuneration[actif.cle][annee] = somme_remunerations_actif
            dict_remuneration_RO[actif.cle][annee] = somme_remunerations_RO_actif
            dict_cout_variable[actif.cle][annee] = somme_couts_variables_actif
            dict_cout_maintenance[actif.cle][annee] = actif.cout_fixe_maintenance * donnees_simulation.parc.nombre_unites(actif.cle, annee)

            cout_variable_total[annee] += dict_cout_variable[actif.cle][annee]
            cout_maintenance[annee] += actif.cout_fixe_maintenance * donnees_simulation.parc.nombre_unites(actif.cle, annee)
            

            if donnees_entree.parametres_simulation.mecanisme_capacite : 
                if donnees_entree.data_frame_actifs_eligibles_mecapa.at[actif.cle, 'eligible'] :
                    derating_factor_actif = MecanismeCapacite.facteur_de_charge_mecapa(actif,annee, donnees_entree)
                else :
                    derating_factor_actif = donnees_entree.data_frame_derating_factor.at[actif.cle, annee]

                puissance = 0
                if actif.categorie == "Stockage":
                    puissance = actif.puissance_nominale_decharge
                elif actif.categorie == "Pilotable":
                    puissance = actif.puissance_nominale
                elif actif.categorie == "ENR":
                    puissance = actif.puissance_reference
                
                capacite_remuneree_actif = donnees_simulation.parc.nombre_unites(actif.cle, annee) * puissance * derating_factor_actif
                prix_capacite_annee = dict_rapports_mecanisme_capacite[annee].prix_capacite

                remuneration_capacitaire_actif = prix_capacite_annee * capacite_remuneree_actif

                dict_remuneration_capacitaire[actif.cle][annee] = remuneration_capacitaire_actif



        # couts d'investissement
        cout_investissement_one_shot[annee] = donnees_entree.parametres_simulation.limite_argent - donnees_simulation.liste_rapports_investissement[annee].argent_restant
        for rapport_boucle_investissement in donnees_simulation.liste_rapports_investissement[annee].liste_rapports_boucle_investissement:
            actif_choisi = rapport_boucle_investissement.actif_choisi
            if(not actif_choisi):
                continue
            nombre_unites_construites = rapport_boucle_investissement.nombre_unites_investies

            annuite_IDC = nombre_unites_construites * IndicateursEconomiques.calcul_investissement_IDC_annualise(actif_choisi, annee)

            for annee_fonctionnement in range(min(annee + actif_choisi.duree_construction, horizon_simulation), min(annee + actif_choisi.duree_construction + actif_choisi.duree_vie, horizon_simulation)):
                cout_investissement_IDC_annualise[annee_fonctionnement] += annuite_IDC
                dict_cout_investissement_IDC_annualise[actif_choisi.cle][annee_fonctionnement] += annuite_IDC


        somme_defaillances = 0
        somme_heures_defaillance = 0
        somme_couts_defaillance = 0
        somme_prix_spot_moyens = 0
        somme_emissions_cabone = 0
        for indice_meteo in range(nombre_meteos):
            resultat_annuel = liste_resultats_annuels[indice_meteo]

            defaillance_annuelle = np.sum(resultat_annuel.defaillance)
            somme_defaillances += defaillance_annuelle * df_ponderation.at[indice_meteo, "value"]
            somme_heures_defaillance += np.sum(resultat_annuel.defaillance > 0) * df_ponderation.at[indice_meteo, "value"]
            somme_couts_defaillance += defaillance_annuelle * donnees_entree.parametres_simulation.VOLL

            somme_prix_spot_moyens += np.mean(resultat_annuel.cout_marginal) * df_ponderation.at[indice_meteo, "value"]

            for actif_pilotable in donnees_entree.actifs_pilotables():
                production_actif = resultat_annuel.production[actif_pilotable.cle]
                somme_emissions_cabone += actif_pilotable.emission_carbone * np.sum(production_actif) * df_ponderation.at[indice_meteo, "value"]

        # moyenne sur les météos
        defaillance[annee] = somme_defaillances
        heures_defaillance[annee] = somme_heures_defaillance
        cout_defaillance[annee] = somme_couts_defaillance
        prix_spot_moyen[annee] = somme_prix_spot_moyens
        emissions_carbone[annee] = somme_emissions_cabone

        # écrêtements
        for actif_ENR in donnees_entree.actifs_ENR():
            somme_ecretement_actif = 0
            for indice_meteo in range(nombre_meteos):
                resultat_annuel = liste_resultats_annuels[indice_meteo]
                somme_ecretement_actif += np.sum(resultat_annuel.ecretement[actif_ENR.cle]) * df_ponderation.at[indice_meteo, "value"]
            dict_ecretement[actif_ENR.cle][annee] = somme_ecretement_actif 
        
		# Charge
        for actif_stockage in donnees_entree.actifs_stockage():
            somme_charge_actif = 0
            for indice_meteo in range(nombre_meteos):
                resultat_annuel = liste_resultats_annuels[indice_meteo]
                somme_charge_actif += np.sum(resultat_annuel.charge[actif_stockage.cle]) * df_ponderation.at[indice_meteo, "value"]
            dict_charge[actif_stockage.cle][annee] = somme_charge_actif 
        # rappel des données de l'ambiance réalisée
        prix_certificats_verts[annee] = donnees_couts_var.at["prix_certificats_verts","Annee_%d"%annee]
        
        prix_carbone[annee] = donnees_couts_var.at["cout_CO2","Annee_%d"%annee]
        
        # Prix de la capacité 
        if donnees_entree.parametres_simulation.mecanisme_capacite :
            prix_capacite.append(dict_rapports_mecanisme_capacite[annee].prix_capacite)

    # écriture des productions + défaillance
    for actif in donnees_entree.tous_actifs():
        data_frame_registre_energie["Energie produite %s"%actif.cle] = dict_energie_produite[actif.cle]
    data_frame_registre_energie["Defaillance"] = defaillance
    data_frame_registre_energie["Heures de defaillance"] = heures_defaillance

    # écriture des écrêtements
    for actif_ENR in donnees_entree.actifs_ENR():
        data_frame_registre_energie["Ecretement %s" % actif_ENR.cle] = dict_ecretement[actif_ENR.cle]
    # écriture des charges
    for actif_stockage in donnees_entree.actifs_stockage():
        data_frame_registre_energie["Charge %s" % actif_stockage.cle] = dict_charge[actif_stockage.cle]
    # ériture de la demande totale
    data_frame_registre_energie["demande totale"] = demande_totale

    # écriture des émissions de CO2
    data_frame_registre_energie["Emissions CO2"] = emissions_carbone

    # écriture des rémunérations + prix spot moyen + prix capacitaire
    for actif in donnees_entree.tous_actifs():
        data_frame_registre_economique["Remuneration %s"%actif.cle] = dict_remuneration[actif.cle]
        if donnees_entree.parametres_simulation.mecanisme_capacite : 
            data_frame_registre_economique["Remuneration capacitaire %s"%actif.cle] = dict_remuneration_capacitaire[actif.cle]
            data_frame_registre_economique["Remuneration RO %s"%actif.cle] = dict_remuneration_RO[actif.cle]
    data_frame_registre_economique["Prix spot moyen"] = prix_spot_moyen
    if donnees_entree.parametres_simulation.mecanisme_capacite : 
        data_frame_registre_economique["Prix capacite"] = prix_capacite

    # rappel des prix du carbone et des certificats verts de l'ambiance réalisée
    data_frame_registre_economique["Prix carbone"] = prix_carbone
    data_frame_registre_economique["Prix certificats_verts"] = prix_certificats_verts

    # écriture des coûts
    data_frame_registre_economique["Cout variable total"] = cout_variable_total
    data_frame_registre_economique["Cout de defaillance"] = cout_defaillance
    data_frame_registre_economique["Cout de maintenance"] = cout_maintenance
    data_frame_registre_economique["Cout investissement one shot"] = cout_investissement_one_shot
    data_frame_registre_economique["Cout investissement IDC annualise"] = cout_investissement_IDC_annualise

    # if donnees_entree.parametres_simulation.architecture == "AOCLT":
        # data_frame_registre_economique["Cout investissement one shot hors marche"] = cout_investissement_one_shot_hors_marche
        # data_frame_registre_economique["Cout investissement IDC annualise hors marche"] = cout_investissement_IDC_annualise_hors_marche
        # data_frame_registre_economique["Cout financement contrats"] = cout_financement_contrats

    for actif in donnees_entree.tous_actifs():
        data_frame_registre_economique["Cout variable %s"%actif.cle] = dict_cout_variable[actif.cle]

    for actif in donnees_entree.tous_actifs():
        data_frame_registre_economique["Cout maintenance %s"%actif.cle] = dict_cout_maintenance[actif.cle]

    for actif in donnees_entree.tous_actifs():
        data_frame_registre_economique["Cout investissement IDC annualise %s"%actif.cle] = dict_cout_investissement_IDC_annualise[actif.cle]

    if donnees_entree.parametres_simulation.architecture == "AOCLT":
        for actif in donnees_entree.tous_actifs():
            data_frame_registre_economique["Cout investissement IDC annualise hors marche %s" % actif.cle] = dict_cout_investissement_IDC_annualise_hors_marche[actif.cle]

    data_frame_registre_energie.to_csv(fichier_registre_energie, sep=";")
    data_frame_registre_economique.to_csv(fichier_registre_economique, sep=";")
    

def ecriture_generale(donnees_entree, donnees_simulation, nom_dossier_donnees):
    """
    Ecrit le dossier de sortie de toute la simulation effectuée à partir des données du dossier dont le nom est fourni
    en paramètre.

    Paramètres
    ----------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    nom_dossier_donnees : str
        nom du dossier contenant les données d'entrée utilisées pour la simulation
    """

    dossier_sortie = donnees_simulation.dossier_sortie

    for annee in range(donnees_entree.parametres_simulation.horizon_simulation):
        dossier_annee = dossier_sortie + "/annee_%d" % annee
        
        if not os.path.isdir(dossier_annee):
            os.mkdir(dossier_annee)

        if(donnees_entree.parametres_simulation.architecture == "AOCLT"):
            ecriture_rapport_appels_offres_investissement(dossier_annee, donnees_simulation.liste_rapports_appels_offres_investissement[annee])
            ecriture_rapport_appels_offres_demantelement(dossier_annee, donnees_simulation.liste_rapports_appels_offres_demantelement[annee])
        
        ## On écrit le rapport directement à la fin de la réalisation de chaque année afin de pouvoir suivre en temps réel     
        #if donnees_entree.parametres_simulation.mecanisme_capacite :
            #ecriture_rapport_mecanisme_capacite(dossier_sortie, donnees_simulation.dict_rapports_mecanisme_capacite[annee])

        ecriture_rapport_investissement(dossier_annee, donnees_simulation.liste_rapports_investissement[annee])

        ecriture_rapport_demantelement(dossier_annee, donnees_simulation.liste_rapports_demantelement[annee])

        ecriture_realisation(dossier_annee, donnees_simulation.matrice_resultats_annuels[annee])

    ecriture_compte_unites(dossier_sortie, donnees_entree, donnees_simulation)
    ecriture_registres_generaux(dossier_sortie, donnees_entree, donnees_simulation)
    ecriture_compte_capacites(dossier_sortie, donnees_entree, donnees_simulation)
    ecriture_registres_ouvertures_fermeture(dossier_sortie, donnees_entree, donnees_simulation)

    if (donnees_entree.parametres_simulation.architecture == "AOCLT"):
        ecriture_registres_ouvertures_fermetures_appels_offres(dossier_sortie, donnees_entree, donnees_simulation)
        ecriture_registre_prix_contractuels_contrats_pour_difference(dossier_sortie, donnees_entree, donnees_simulation)
        
    #os.rename('parc_vision.csv', dossier_sortie + 'parc_vision.csv')
