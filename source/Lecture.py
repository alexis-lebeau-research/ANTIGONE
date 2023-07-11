# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF


import pandas as pd
import numpy as np
import os
import sys

import DonneesEntree
import DonneesSimulation

import Contrats

import GenerationMixCible
import GenerationMixOptimal

def pjoin(*args, **kwargs):
    return os.path.join(*args, **kwargs).replace(os.sep, '//')
    
# ######################### fonctions de lecture des fichiers d'actifs ##################################

def lecture_fichier_actifs_pilotables(chemin_fichier):
    """
    Lit le fichier décrivant les actifs pilotables à l'emplacement donné et renvoie un dictionnaire contenant les
    instances correspondantes de DonneesEntree.ActifPilotable.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant les actifs pilotables

    Retours
    -------
    dict
        dictionnaire contenant les instances de DonneesEntree.ActifPilotable indexées par leurs clés
    """

    data_frame_actifs_pilotables = pd.read_csv(chemin_fichier, sep=";")
    dict_actifs_pilotables = dict()
    for ligne in data_frame_actifs_pilotables.index:  # !!! à changer par une méthode plus efficace
        cle = data_frame_actifs_pilotables.loc[ligne, "type"]
        cout_fixe_construction = data_frame_actifs_pilotables.loc[ligne, "CC_MW"] * data_frame_actifs_pilotables.loc[ligne, "Pnom"]
        cout_fixe_maintenance = data_frame_actifs_pilotables.loc[ligne, "CF_MW"] * data_frame_actifs_pilotables.loc[ligne, "Pnom"]
        duree_construction = data_frame_actifs_pilotables.loc[ligne, "duree_const"]
        duree_vie = data_frame_actifs_pilotables.loc[ligne, "duree_vie"]
        taux_actualisation = data_frame_actifs_pilotables.loc[ligne, "taux_actu"]
        gisement_max = data_frame_actifs_pilotables.loc[ligne, "gisement_max"]
        ajoutable = data_frame_actifs_pilotables.loc[ligne, "ajoutable"]
        demantelable = data_frame_actifs_pilotables.loc[ligne, "demantelable"]
        puissance_nominale = data_frame_actifs_pilotables.loc[ligne, "Pnom"]
        rendement = data_frame_actifs_pilotables.loc[ligne, "rend"]
        emission_carbone = data_frame_actifs_pilotables.loc[ligne, "emission_CO2"]
        combustible = data_frame_actifs_pilotables.loc[ligne, "combustible"]

        # granularité d'investissement facultative
        granularite_investissement = 1
        try:
            granularite_investissement = int(data_frame_actifs_pilotables.loc[ligne, "granularite_investissement"])
        except (KeyError, ValueError):
            pass

        # granularité de demantelement facultative
        granularite_demantelement = 1
        try:
            granularite_demantelement = int(data_frame_actifs_pilotables.loc[ligne, "granularite_demantelement"])
        except (KeyError, ValueError):
            pass

        # limite de construction annuelle facultative
        limite_construction_annuelle = 'aucune'
        try:
            limite_construction_annuelle = int(data_frame_actifs_pilotables.loc[ligne, "limite_construction_annuelle"])
        except (KeyError, ValueError):
            pass

        # délai de fermeture facultatif
        delai_fermeture = 1
        try:
            delai_fermeture = int(data_frame_actifs_pilotables.loc[ligne, "delai_fermeture"])
        except (KeyError, ValueError):
            pass

        # exigence de rentabilité la première année facultative
        exigence_rentabilite_premiere_annee = 0
        try:
            exigence_rentabilite_premiere_annee = data_frame_actifs_pilotables.loc[ligne, "exigence_rentabilite_premiere_annee"] * data_frame_actifs_pilotables.loc[ligne, "Pnom"]
        except (KeyError, ValueError):
            pass
        
        actif_pilotable = DonneesEntree.ActifPilotable(cle, cout_fixe_construction, cout_fixe_maintenance, duree_construction, duree_vie, taux_actualisation, gisement_max, ajoutable, demantelable, granularite_investissement, granularite_demantelement, limite_construction_annuelle, delai_fermeture, exigence_rentabilite_premiere_annee, puissance_nominale, rendement, emission_carbone, combustible)
        dict_actifs_pilotables[cle] = actif_pilotable
        
    return dict_actifs_pilotables


def lecture_fichier_actifs_ENR(chemin_fichier):
    """
    Lit le fichier décrivant les actifs renouvelables à l'emplacement donné et renvoie un dictionnaire contenant les
    instances correspondantes de DonneesEntree.ActifENR.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant les actifs renouvelables

    Retours
    -------
    dict
        dictionnaire contenant les instances de DonneesEntree.ActifENR indexées par leurs clés
    """

    data_frame_actifs_ENR = pd.read_csv(chemin_fichier, sep=";")
    dict_actifs_ENR = dict()
    for ligne in data_frame_actifs_ENR.index:
        cle = data_frame_actifs_ENR.loc[ligne, "type"]
        cout_fixe_construction = data_frame_actifs_ENR.loc[ligne, "CC_MW"] * data_frame_actifs_ENR.loc[ligne, "Pnom"]
        cout_fixe_maintenance = data_frame_actifs_ENR.loc[ligne, "CF_MW"] * data_frame_actifs_ENR.loc[ligne, "Pnom"]
        duree_construction = int(data_frame_actifs_ENR.loc[ligne, "duree_const"])
        duree_vie = int(data_frame_actifs_ENR.loc[ligne, "duree_vie"])
        taux_actualisation = data_frame_actifs_ENR.loc[ligne, "taux_actu"]
        gisement_max = data_frame_actifs_ENR.loc[ligne, "gisement_max"]
        ajoutable = data_frame_actifs_ENR.loc[ligne, "ajoutable"]
        demantelable = data_frame_actifs_ENR.loc[ligne, "demantelable"]
        puissance_reference = data_frame_actifs_ENR.loc[ligne, "Pnom"]
        cout_variable = data_frame_actifs_ENR.loc[ligne, "CV"]

        # granularité d'investissement facultative
        granularite_investissement = 1
        try:
            granularite_investissement = int(data_frame_actifs_ENR.loc[ligne, "granularite_investissement"])
        except (KeyError, ValueError):
            pass

        # granularité de demantelement facultative
        granularite_demantelement = 1
        try:
            granularite_demantelement = int(data_frame_actifs_ENR.loc[ligne, "granularite_demantelement"])
        except (KeyError, ValueError):
            pass

        # limite de construction annuelle facultative
        limite_construction_annuelle = 'aucune'
        try:
            limite_construction_annuelle = int(
                data_frame_actifs_ENR.loc[ligne, "limite_construction_annuelle"])
        except (KeyError, ValueError):
            pass

        # délai de fermeture facultatif
        delai_fermeture = 1
        try:
            delai_fermeture = int(data_frame_actifs_ENR.loc[ligne, "delai_fermeture"])
        except (KeyError, ValueError):
            pass

        # exigence de rentabilité la première année facultative
        exigence_rentabilite_premiere_annee = 0
        try:
            exigence_rentabilite_premiere_annee = data_frame_actifs_ENR.loc[ligne, "exigence_rentabilite_premiere_annee"] * data_frame_actifs_ENR.loc[ligne, "Pnom"]
        except (KeyError, ValueError):
            pass
        
        actif_ENR = DonneesEntree.ActifENR(cle, cout_fixe_construction, cout_fixe_maintenance, duree_construction, duree_vie, taux_actualisation, gisement_max, ajoutable, demantelable, granularite_investissement, granularite_demantelement, limite_construction_annuelle, delai_fermeture, exigence_rentabilite_premiere_annee, puissance_reference, cout_variable)
        dict_actifs_ENR[cle] = actif_ENR
    return dict_actifs_ENR

def lecture_fichier_actifs_stockage(chemin_fichier):
    """
    Lit le fichier décrivant les actifs de stockage à l'emplacement donné et renvoie un dictionnaire contenant les
    instances correspondantes de DonneesEntree.ActifStockage.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant les actifs de stockage

    Retours
    -------
    dict
        dictionnaire contenant les instances de DonneesEntree.ActifStockage indexées par leurs clés
    """

    data_frame_actifs_stockage = pd.read_csv(chemin_fichier, sep=";")
    dict_actifs_stockage = dict()
    for ligne in data_frame_actifs_stockage.index:
        cle = data_frame_actifs_stockage.loc[ligne, "type"]
        cout_fixe_construction = data_frame_actifs_stockage.loc[ligne, "CC_MW"] * data_frame_actifs_stockage.loc[ligne, "puissance"]
        cout_fixe_maintenance = data_frame_actifs_stockage.loc[ligne, "CF_MW"] * data_frame_actifs_stockage.loc[ligne, "puissance"]
        duree_construction = data_frame_actifs_stockage.loc[ligne, "duree_const"]
        duree_vie = data_frame_actifs_stockage.loc[ligne, "duree_vie"]
        taux_actualisation = data_frame_actifs_stockage.loc[ligne, "taux_actu"]
        gisement_max = data_frame_actifs_stockage.loc[ligne, "gisement_max"]
        ajoutable = data_frame_actifs_stockage.loc[ligne, "ajoutable"]
        demantelable = data_frame_actifs_stockage.loc[ligne, "demantelable"]
        puissance_nominale_charge = data_frame_actifs_stockage.loc[ligne, "puissance"]
        puissance_nominale_decharge = data_frame_actifs_stockage.loc[ligne, "puissance"]
        rendement_charge = data_frame_actifs_stockage.loc[ligne, "rend_ch"]
        rendement_decharge = data_frame_actifs_stockage.loc[ligne, "rend_dech"]
        capacite = data_frame_actifs_stockage.loc[ligne, "stock_max_MWh"]
        stock_initial = data_frame_actifs_stockage.loc[ligne, "etat_stock"]
        cout_variable = data_frame_actifs_stockage.loc[ligne, "CV"]
        duree = capacite / puissance_nominale_charge

        # granularité d'investissement facultative
        granularite_investissement = 1
        try:
            granularite_investissement = int(data_frame_actifs_stockage.loc[ligne, "granularite_investissement"])
        except (KeyError, ValueError):
            pass

        # granularité de demantelement facultative
        granularite_demantelement = 1
        try:
            granularite_demantelement = int(data_frame_actifs_stockage.loc[ligne, "granularite_demantelement"])
        except (KeyError, ValueError):
            pass

        # limite de construction annuelle facultative
        limite_construction_annuelle = 'aucune'
        try:
            limite_construction_annuelle = int(
                data_frame_actifs_stockage.loc[ligne, "limite_construction_annuelle"])
        except (KeyError, ValueError):
            pass

        # délai de fermeture facultatif
        delai_fermeture = 1
        try:
            delai_fermeture = int(data_frame_actifs_stockage.loc[ligne, "delai_fermeture"])
        except (KeyError, ValueError):
            pass

        # exigence de rentabilité la première année facultative
        exigence_rentabilite_premiere_annee = 0
        try:
            exigence_rentabilite_premiere_annee = data_frame_actifs_stockage.loc[ligne, "exigence_rentabilite_premiere_annee"] * data_frame_actifs_stockage.loc[ligne, "puissance"]
        except (KeyError, ValueError):
            pass
        
        actif_stockage = DonneesEntree.ActifStockage(cle, cout_fixe_construction, cout_fixe_maintenance, duree_construction, duree_vie, taux_actualisation, gisement_max, ajoutable, demantelable, granularite_investissement, granularite_demantelement, limite_construction_annuelle, delai_fermeture, exigence_rentabilite_premiere_annee, puissance_nominale_charge, puissance_nominale_decharge, rendement_charge, rendement_decharge, capacite, stock_initial, cout_variable,duree)
        dict_actifs_stockage[cle] = actif_stockage
    return dict_actifs_stockage

def lecture_fichier_variations_couts_construction(chemin_fichier, parametres_simulation, dict_actifs_pilotables, dict_actifs_ENR, dict_actifs_stockage):
    """
    Lit le fichier décrivant les variations des coûts fixes de construction et modifie en conséquence les attributs
    correspondants dans les actifs.

    Les variations de coûts fixes de construction seront considérées nulles si le fichier n'existe pas ou si la valeur
    n'est pas spécifiée dans le fichier.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant les variations des coûts fixes de construction
    parametres_simulation : DonneesEntree.ParametresSimulation
        paramètres de simulation à utiliser
    dict_actifs_pilotables : dict
        dictionnaire contenant les actifs pilotables indexés par leurs clés
    dict_actifs_ENR : dict
        dictionnaire contenant les actifs ENR indexés par leurs clés
    dict_actifs_stockage : dict
        dictionnaire contenant les actifs de stockage indexés par leurs clés
    """

    data_frame_variations_couts_construction = pd.DataFrame()
    try:
        data_frame_variations_couts_construction = pd.read_csv(chemin_fichier, sep=';', index_col=0)
    except(pd.errors.EmptyDataError, FileNotFoundError):
        pass

    liste_tous_actifs = list(dict_actifs_pilotables.values()) + list(dict_actifs_ENR.values()) + list(dict_actifs_stockage.values())

    nombre_annees = parametres_simulation.horizon_simulation + parametres_simulation.horizon_prevision
        
    for actif in liste_tous_actifs:
        variations_cout_construction_actif = np.zeros(nombre_annees)

        for annee in range(nombre_annees):
            variation_cout_construction_actif_annee = 0
            try:
                variation_cout_construction_actif_annee = float(data_frame_variations_couts_construction.loc[actif.cle].iat[annee])
            except (KeyError, ValueError):
                pass

            variations_cout_construction_actif[annee] = variation_cout_construction_actif_annee

        actif.tableau_variations_cout_construction = variations_cout_construction_actif

# ######################### fonctions de lecture des fichiers de paramètres ##################################

def lecture_fichier_parametres_simulation(chemin_fichier):
    """
    Lit le fichier décrivant les paramètres de simulation à l'emplacement donné et renvoie l'instance de
    DonneesEntree.ParametresSimulation correspondante.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant les paramètres de simulation

    Retours
    -------
    DonneesEntree.ParametresSimulation
        paramètres de simulation
    """

    df_param_simu = pd.read_csv(chemin_fichier, sep=";",index_col=0)

    parametres_simulation = DonneesEntree.ParametresSimulation(df_param_simu)
    
   
    return parametres_simulation
    
def lecture_fichier_parametres_ponderation(chemin_fichier):
    """
    Lit le fichier décrivant les pondérations des scénarios météos à l'emplacement donné et renvoie l'instance de
    DonneesEntree.ParametresPonderation correspondante.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant les paramètres de simulation

    Retours
    -------
    DonneesEntree.ParametresPonderation
        paramètres de pondération
    """

    df_param_ponderation = pd.read_csv(chemin_fichier, sep=";",index_col=0)
    
    #Vérification que la pondération est bien normalisée et normalisation si besoin
    if sum(df_param_ponderation['value']) != 1 :
        norm = sum(df_param_ponderation['value'])
        df_param_ponderation['value'] = df_param_ponderation['value']/norm  

    #parametres_ponderation = DonneesEntree.ParametresPonderation(df_param_ponderation)
    
   
    return df_param_ponderation

def lecture_fichier_parametres_optimisation(chemin_fichier):
    """
    Lit le fichier décrivant les paramètres d'optimisation à l'emplacement donné et renvoie l'instance de
    DonneesEntree.ParametresOptimisation correspondante.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant les paramètres d'optimisation

    Retours
    -------
    DonneesEntree.ParametresOptimisation
        paramètres d'optimisation
    """

    data_frame_parametres_optimisation = pd.read_csv(chemin_fichier, sep=";")
    fenetre_optimisation = data_frame_parametres_optimisation["fenetre_optimisation"].iloc[0]
    vision_supplementaire = data_frame_parametres_optimisation["vision_supplementaire"].iloc[0]
    parametres_optimisation = DonneesEntree.ParametresOptimisation(fenetre_optimisation, vision_supplementaire)
    return parametres_optimisation


# ######################### fonctions de lecture des fichiers du parc ##################################

def lecture_fichier_registre(chemin_fichier, donnees_entree):
    """
    Lit le fichier décrivant un registre d'ouvertures ou de fermetures à l'emplacement donné et renvoie les données
    correspondantes.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant le registre d'ouvertures ou de fermetures
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser

    Retours
    -------
    dict
        dictionnaire contenant, pour chaque actif, le tableau du nombre d'ouvertures ou de fermetures annuelles
    """

    data_frame_registre = pd.read_csv(chemin_fichier, sep=";", index_col=0)

    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation
    horizon_prevision = donnees_entree.parametres_simulation.horizon_prevision

    registre = dict()
    for actif in donnees_entree.tous_actifs():

        registre_actif = np.zeros(horizon_simulation + horizon_prevision + actif.duree_construction + actif.duree_vie)

        # remplissage du registre initial si des données sont fournies pour l'actif et les dates concernées
        try:
            serie_registre_actif_initial = data_frame_registre.loc[actif.cle]

            for annee in range(horizon_simulation + horizon_prevision):
                try:
                    registre_actif[annee] = serie_registre_actif_initial[annee]
                except IndexError:
                    pass
        except KeyError:
            pass
            #print("ATTENTION : %s -> le fichier %s n'a pas été pris en compte." %(actif.cle,chemin_fichier))

        registre[actif.cle] = registre_actif

    return registre


def lecture_fichier_parc_initial(chemin_fichier, donnees_entree):
    """
    Lit le fichier décrivant le parc initial à l'emplacement donné et renvoie les données correspondantes.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant le parc initial
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser

    Retours
    -------
    dict
        dictionnaire contenant, pour chaque actif, nombre d'unités présentes dans le parc initial
    """

    data_frame_parc_initial = pd.read_csv(chemin_fichier, sep=";", index_col=0)

    parc_initial = dict()
    for actif in donnees_entree.tous_actifs():
        nombre_initial_actif = 0

        try:
            nombre_initial_actif = data_frame_parc_initial.loc[actif.cle].iat[0]
        except(KeyError, IndexError):
            pass

        parc_initial[actif.cle] = nombre_initial_actif

    return parc_initial


# ######################### fonctions de lecture des fichiers d'appels d'offres ##################################

# attention, ces fonctions n'ont pas de retour et modifient directement les données d'entrée précédemment lues

def lecture_fichier_mix_cible(chemin_fichier, donnees_entree):
    """
    Lit le fichier décrivant le mix cible à l'emplacement donné et renvoie les données correspondantes.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant le mix cible
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser

    Retours
    -------
    dict
        dictionnaire contenant, pour chaque actif, le tableau annuel du nombre d'unités ciblé
    """

    data_frame_mix_cible = pd.read_csv(chemin_fichier, sep=";", index_col=0)

    mix_cible = dict()
    nombre_annees = donnees_entree.parametres_simulation.horizon_simulation + donnees_entree.parametres_simulation.horizon_prevision
    for actif in donnees_entree.tous_actifs():

        tableau_nombres_unites_cible = np.zeros(nombre_annees)

        for annee in range(nombre_annees):
            nombre_unites_cible = 0
            try:
                nombre_unites_cible = data_frame_mix_cible.loc[actif.cle].iat[annee]
            except(KeyError, IndexError):
                pass

            tableau_nombres_unites_cible[annee] = nombre_unites_cible

        mix_cible[actif.cle] = tableau_nombres_unites_cible

    donnees_entree.mix_cible = mix_cible


def lecture_fichier_parametres_contrat_parfait(chemin_fichier, donnees_entree):
    """
    Lit le fichier décrivant les paramètres des contrats parfaits à l'emplacement donné et fixe la valeur des attributs
    de classe pertinents.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant les paramètres de contrat parfait
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    """

    data_frame_parametres_contrat_parfait = pd.read_csv(chemin_fichier, sep=";", index_col=0)

    for actif in donnees_entree.tous_actifs():
        nombre_heures_fonctionnement_historique = 0

        try:
            nombre_heures_fonctionnement_historique = data_frame_parametres_contrat_parfait.loc[actif.cle, "nombre_heures_fonctionnement_historique"]
        except(KeyError, IndexError):
            pass

        # modification de la variable de classe de ContratParfait
        Contrats.ContratParfait.dict_nombre_heures_fonctionnement_historique[actif.cle] = nombre_heures_fonctionnement_historique

    cout_variable_equivalent = data_frame_parametres_contrat_parfait["cout_variable_equivalent"].iat[0]
    # modification de la variable de classe de ContratParfait
    Contrats.ContratParfait.cout_variable_equivalent = cout_variable_equivalent




# ######################### fonctions de lecture des fichiers du mécanisme de capacité ##################################

# attention, ces fonctions n'ont pas de retour et modifient directement les données d'entrée précédemment lues

def lecture_fichier_capacite_cible(chemin_fichier, donnees_entree):
    """
    Lit le fichier décrivant l'anticipation du besoin de capacité à l'emplacement donné et renvoie les données correspondantes.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant le mix cible
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser

    Retours
    -------
    dict
        dictionnaire contenant, pour chaque actif, le tableau annuel de la capacité cible
    """

    data_frame_capacite_cible = pd.read_csv(chemin_fichier, sep=";", index_col=0)

    capacite_cible = dict()

    for annee in data_frame_capacite_cible.index :

        capacite_cible[annee] = data_frame_capacite_cible.at[annee, "capacite_cible"]

    donnees_entree.capacite_cible = capacite_cible


def lecture_fichier_actifs_eligibles(chemin_fichier, donnees_entree):
    """
    Lit le fichier décrivant l'anticipation du besoin de capacité à l'emplacement donné et renvoie les données correspondantes.

    Paramètres
    ----------
    chemin_fichier : str
        chemin du fichier décrivant le mix cible
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser

    Retours
    -------
    data_frame_actifs_eligibles_mecapa : DataFrame
        df contenant pour tous les actifs s'ils sont éligibles au mécanisme de capacité, ainsi que s'ils sont ajoutables et/ou démantelable et leur gisement annuel et totale
    """

    data_frame_actifs_eligibles_mecapa = pd.read_csv(chemin_fichier, sep=";", index_col=0)
    
    for cle_actif in data_frame_actifs_eligibles_mecapa.index : 
        if data_frame_actifs_eligibles_mecapa.at[cle_actif, 'gisement_annuel'] == 'inf' :
            data_frame_actifs_eligibles_mecapa.at[cle_actif, 'gisement_annuel'] = np.inf
        if data_frame_actifs_eligibles_mecapa.at[cle_actif, 'gisement_total'] == 'inf' :
            data_frame_actifs_eligibles_mecapa.at[cle_actif, 'gisement_total'] = np.inf
            
        actif = donnees_entree.trouve_actif(cle_actif)
        eligible = data_frame_actifs_eligibles_mecapa.at[actif.cle, "eligible"]
        
        actif.eligible_mecanisme_capacite = eligible

        data_frame_actifs_eligibles_mecapa.at[actif.cle, "ajoutable"] = actif.ajoutable
        data_frame_actifs_eligibles_mecapa.at[actif.cle, "demantelable"] = actif.demantelable
    
    print("\n\nDescription du mécanisme de capacité\t")
    print(data_frame_actifs_eligibles_mecapa)
    donnees_entree.data_frame_actifs_eligibles_mecapa = data_frame_actifs_eligibles_mecapa
    

# ################################ fonction de lecture globale  #########################################

def lecture_generale(nom_dossier_donnees, callType):
    """
    Lit le dossier de données d'entrée ayant le nom passé en paramètre dans le dossier instances et renvoie les
    instances de DonneesEntree.DonneesEntree et DonneesSimilation.DonneesSimilation correspondantes.

    Paramètres
    ----------
    nom_dossier_donnees : str
        nom du dossier de données d'entrée dans le dossier instances
    callType : str
        'mix_cible' pour les données nécessaires au calcul du mix cible

    Retours
    -------
    DonneesEntree.DonneesEntree
        données d'entrée à utiliser pour la simulation
    DonneesSimilation.DonneesSimilation
        données de simulation à utiliser pour la simulation
    """

    chemin_dossier = pjoin( os.path.dirname(os.getcwd()) , 'instances' , nom_dossier_donnees)
    
    # Unzip if zipped file
    if nom_dossier_donnees[-4:] == ".zip":
        from zipfile import ZipFile
        with ZipFile(chemin_dossier, 'r') as z:
            z.extractall(chemin_dossier[0:-4])
        chemin_dossier = pjoin( os.path.dirname(os.getcwd()) , 'instances' , nom_dossier_donnees[0:-4] )

    # ###################### #
    # lecture des paramètres #
    # ###################### #
    chemin_parametres = pjoin(chemin_dossier , "Parametres")
    parametres_optimisation = lecture_fichier_parametres_optimisation(pjoin(chemin_parametres,"parametres_optim.csv"))
    parametres_simulation = lecture_fichier_parametres_simulation(pjoin(chemin_parametres , "parametres_simulation.csv"))
    df_parametres_ponderation = lecture_fichier_parametres_ponderation(pjoin(chemin_parametres, "parametres_ponderation.csv"))

    # ################## #
    # lecture des actifs #
    # ################## #
    chemin_actifs = pjoin(chemin_dossier , "Actifs")

    dict_actifs_ENR = dict()
    try :
        dict_actifs_ENR = lecture_fichier_actifs_ENR(pjoin(chemin_actifs,"actifs_enr.csv"))
    except(pd.errors.EmptyDataError, FileNotFoundError):
        print("pas d'actifs ENR")

    dict_actifs_pilotables = dict()
    try:
        dict_actifs_pilotables = lecture_fichier_actifs_pilotables(pjoin(chemin_actifs, "actifs_pilot.csv"))
    except(pd.errors.EmptyDataError, FileNotFoundError):
        print("pas d'actifs pilotables")

    dict_actifs_stockage = dict()
    try:
        dict_actifs_stockage = lecture_fichier_actifs_stockage(pjoin(chemin_actifs,"actifs_stockage.csv"))
    except(pd.errors.EmptyDataError, FileNotFoundError):
        print("pas d'actifs de stockage")

    lecture_fichier_variations_couts_construction(pjoin(chemin_actifs, "variations_couts_construction.csv"), parametres_simulation, dict_actifs_pilotables, dict_actifs_ENR, dict_actifs_stockage)


    nombre_annees = parametres_simulation.horizon_simulation
    nb_meteo = parametres_simulation.nb_meteo
   
   
    # ##################### #
    # lecture des ambiances #
    # ##################### #


    chemin_ambiances = pjoin(chemin_dossier,"Ambiances")  

    liste_dossiers_ambiances = [dossier for dossier in os.listdir(chemin_ambiances) if not os.path.isfile(pjoin(chemin_ambiances,dossier))]
        

    ambiances = {}
    
    for amb in liste_dossiers_ambiances :
    
        ambiances[amb] = {}
        
        for n in range(nombre_annees):
        
            ambiances[amb][n] = {}
            
            rep_annee = pjoin(chemin_dossier,"Ambiances",amb,"Annee_%d"%n)

            # couts combustibles 
            
            path_couts_comb = pjoin(rep_annee,"couts_combustibles_et_carbone.csv")
            ambiances[amb][n]["couts_combustibles"] = pd.read_csv(path_couts_comb,sep=";",index_col=0)
            
            for met in range(nb_meteo):
            
                ambiances[amb][n]["meteo_%d"%met] = {}
            
                rep_meteo = pjoin(chemin_dossier,"Ambiances",amb,"Annee_%d"%n,"meteo_%d"%met)
                
                # Demande
                
                path_demande = pjoin(rep_meteo,"demande.csv")
                ambiances[amb][n]["meteo_%d"%met]["demande"] = pd.read_csv(path_demande,sep=";",index_col=0)
                
                # EnR
                
                path_fc = pjoin(rep_meteo,"facteurs_production_ENR.csv")
                ambiances[amb][n]["meteo_%d"%met]["fc"] = pd.read_csv(path_fc,sep=";",index_col=0)
                
                # Dispo
                
                path_dispo = pjoin(rep_meteo,"disponibilite_pilot.csv")
                ambiances[amb][n]["meteo_%d"%met]["dispo"] = pd.read_csv(path_dispo,sep=";",index_col=0)

    # ############################## #
    # lecture de l'ambiance realisee #
    # ############################## #
    
    chemin_realisation = pjoin(chemin_dossier,"Realisation")  

    realisation = {}
    
        
    rep_real = pjoin(chemin_dossier,"Realisation")

    # couts combustibles 
    
    path_couts_comb = pjoin(rep_real,"couts_combustibles_et_carbone.csv")
    realisation["couts_combustibles"] = pd.read_csv(path_couts_comb,sep=";",index_col=0)
    
    for met in range(nb_meteo):
    
        realisation["meteo_%d"%met] = {}
    
        rep_meteo = pjoin(chemin_dossier,"Realisation","meteo_%d"%met)
        
        # Demande
        
        path_demande = pjoin(rep_meteo,"demande.csv")
        realisation["meteo_%d"%met]["demande"] = pd.read_csv(path_demande,sep=";",index_col=0)
        
        # EnR
        
        path_fc = pjoin(rep_meteo,"facteurs_production_ENR.csv")
        realisation["meteo_%d"%met]["fc"] = pd.read_csv(path_fc,sep=";",index_col=0)

        # Dispo
            
        path_dispo = pjoin(rep_meteo,"disponibilite_pilot.csv")
        realisation["meteo_%d"%met]["dispo"] = pd.read_csv(path_dispo,sep=";",index_col=0)


    donnees_entree = DonneesEntree.DonneesEntree(dict_actifs_pilotables, dict_actifs_ENR, dict_actifs_stockage, ambiances, realisation, parametres_optimisation, parametres_simulation, df_parametres_ponderation)
    donnees_entree.chemin_dossier = chemin_dossier   
    

    # vérification de la compatibilité entre horizon de prévision et durées de construction
    duree_construction_max = 0
    for actif in donnees_entree.tous_actifs():
        duree_construction_max = max(duree_construction_max, actif.duree_construction)

    if donnees_entree.parametres_simulation.horizon_prevision < duree_construction_max + 1:
        print("L'horizon de prévision est trop court pour couvrir la durée de construction la plus longue.")
        print("Horizon de prévision fixé à %d ans."%(duree_construction_max + 1))
        donnees_entree.parametres_simulation.horizon_prevision = duree_construction_max + 1

    # ########################### #
    # lecture des données du parc #
    # ########################### #

    chemin_parc = pjoin(chemin_dossier ,"Parc")

    parc_initial = lecture_fichier_parc_initial(pjoin(chemin_parc ,"parc_initial.csv"), donnees_entree)

    registre_ouvertures = lecture_fichier_registre(pjoin(chemin_parc, "registre_ouvertures.csv"), donnees_entree)

    registre_fermetures = lecture_fichier_registre(pjoin(chemin_parc, "registre_fermetures.csv"), donnees_entree)

    parc = DonneesSimulation.Parc(parc_initial, registre_ouvertures, registre_fermetures, donnees_entree)

    donnees_simulation = DonneesSimulation.DonneesSimulation(parc)
    
    
    # #################################### #
    # lecture des données du parc anticipé #
    # #################################### #

    
    if parametres_simulation.anticipation_parc_exogene :
    
    
        donnees_simulation.dico_parcs_anticipes = {}
        
        for ambiance in liste_dossiers_ambiances :

            chemin_parc_anticipation = pjoin(chemin_dossier,"Parc_Anticipation",ambiance)
            
        
            parc_initial_anticipation = lecture_fichier_parc_initial(pjoin( chemin_parc_anticipation,"parc_initial.csv" ), donnees_entree)
            registre_ouvertures_anticipation = lecture_fichier_registre(pjoin( chemin_parc_anticipation,"registre_ouvertures.csv" ), donnees_entree)
            registre_fermetures_anticipation = lecture_fichier_registre(pjoin( chemin_parc_anticipation,"registre_fermetures.csv"), donnees_entree)
            
            
            parc_anticipation = DonneesSimulation.Parc(parc_initial_anticipation, registre_ouvertures_anticipation, registre_fermetures_anticipation, donnees_entree)
            
            donnees_simulation.dico_parcs_anticipes[ambiance] = parc_anticipation

    
    # ################################################ #
    # lecture éventuelle des données d'appels d'offres #
    # ################################################ #

    if (donnees_entree.parametres_simulation.architecture == "AOCLT"):
    
        # lecture param_ao
    
        param_ao_path = pjoin(chemin_dossier,"AppelsOffres","parametres_appels_offres.csv")

        df_param_ao = pd.read_csv(param_ao_path, sep=";", index_col=0)

        for tech in df_param_ao.index :
        
            if donnees_entree.parametres_simulation.horizon_prevision <= df_param_ao.at[tech,"horizon_appels_offres"] :
            
                horizon_appels_offres_corrige = donnees_entree.parametres_simulation.horizon_prevision - 1            
                df_param_ao.at[tech,"horizon_appels_offres"] = horizon_appels_offres_corrige
                
                print("L'horizon d'appels d'offres choisi pour %s est trop long par rapport à l'horizon de prévision.\nSa valeur est réduite à %d"%(tech,horizon_appels_offres_corrige))            

        donnees_entree.df_param_ao = df_param_ao
                    
        # lecture mix cible
        
        param_mix_cible = pjoin(chemin_dossier,"AppelsOffres","mix_cible.csv")
        lecture_fichier_mix_cible(param_mix_cible, donnees_entree)
        
        # lecture des paramètres du type de contrat choisi par l'utilisateur
        
        types_contrat_present = np.unique(df_param_ao["type_contrat"].values)
        
        if "contrat_parfait" in types_contrat_present :
        
            param_perfect_contract_path = pjoin(chemin_dossier,"AppelsOffres", "parametres_contrat_parfait.csv")
            lecture_fichier_parametres_contrat_parfait(param_perfect_contract_path,donnees_entree)
        
        if "contrat_pour_difference" in types_contrat_present : 
        
            param_cfd_path = pjoin(chemin_dossier,"AppelsOffres", "parametres_contrat_pour_difference.csv")            
            donnees_entree.df_param_cfd = pd.read_csv(param_cfd_path,sep=";",index_col=0)
            
    # ####################################################### #
    # lecture éventuelle des données du mécanisme de capacité #
    # ####################################################### #

    if (donnees_entree.parametres_simulation.mecanisme_capacite):
    
        # lecture param_mecapa
    
        param_mecapa_path = pjoin(chemin_dossier,"MecanismeCapacite","parametres_mecanisme_capacite.csv")

        df_param_mecapa = pd.read_csv(param_mecapa_path, sep=";", index_col=0)
        df_param_mecapa.at['horizon_enchere', "value"] = int(df_param_mecapa.at['horizon_enchere', "value"])
        df_param_mecapa.at['critere_besoin_capacitaire', "value"] = int(df_param_mecapa.at['critere_besoin_capacitaire', "value"])
        df_param_mecapa.at['budget_annuel_investissement', "value"] = float(df_param_mecapa.at['budget_annuel_investissement', "value"])
        df_param_mecapa.at['capacite_maximale_investissement', "value"] = float(df_param_mecapa.at['capacite_maximale_investissement', "value"])   
        if df_param_mecapa.at['MM_CT', "value"] == "True" : df_param_mecapa.at['MM_CT', "value"] = True
        else : df_param_mecapa.at['MM_CT', "value"] = False
        

        if donnees_entree.parametres_simulation.horizon_prevision < df_param_mecapa.at["horizon_enchere","value"] :
            
            horizon_mecanisme_capacite_corrige = donnees_entree.parametres_simulation.horizon_prevision - 1            
            df_param_mecapa.at["horizon_enchere","value"] = horizon_mecanisme_capacite_corrige
            
            print("L'horizon du mécanisme de capacité choisi est trop long par rapport à l'horizon de prévision.\nSa valeur est réduite à %d"%(horizon_mecanisme_capacite_corrige))            

        donnees_entree.df_param_mecapa = df_param_mecapa
                    
        # lecture du besoin en capacité
        
        capacite_cible_path = pjoin(chemin_dossier,"MecanismeCapacite","capacite_cible.csv")
        lecture_fichier_capacite_cible(capacite_cible_path, donnees_entree)
        
        # lecture des actifs eligibles au mécanisme de capacité 
        
        actifs_eligibles_path = pjoin(chemin_dossier,"MecanismeCapacite","actifs_eligibles.csv")
        lecture_fichier_actifs_eligibles(actifs_eligibles_path, donnees_entree)
        
        # lecture des paramètres du type de contrat choisi par l'utilisateur
        


    return donnees_entree, donnees_simulation


# ################################ fonction de lecture pour la génération de mix cible  #########################################

def lecture_fichier_contraintes_trajectoire(chemin_fichier, donnees_entree):
    data_frame_contraintes_trajectoire = pd.read_csv(chemin_fichier, sep=";")

    liste_contraintes_trajectoire = []

    for indice_ligne in data_frame_contraintes_trajectoire.index:
        liste_actifs_concernes = []
        chaine_caracteres_actifs_concernes = str(data_frame_contraintes_trajectoire.loc[indice_ligne, "actifs_concernes"])
        liste_cles_actifs_concernes = chaine_caracteres_actifs_concernes.split()
        for cle_actif in liste_cles_actifs_concernes:
            try:
                actif = donnees_entree.trouve_actif(cle_actif)
                liste_actifs_concernes.append(actif)
            except KeyError:
                print("La clé d'actif %s n'a pas été reconnue et ne peut être prise en compte dans la contrainte %d." % (cle_actif, indice_ligne))

        type_contrainte = str(data_frame_contraintes_trajectoire.loc[indice_ligne, "type_contrainte"])
        if not (type_contrainte in ["borne_inferieure", "egalite", "borne_superieure"]):
            print("Le type de contrainte %s n'est pas reconnu, la contrainte %d sera ignorée" % (type_contrainte, indice_ligne))
            continue

        grandeur_concernee = str(data_frame_contraintes_trajectoire.loc[indice_ligne, "grandeur_concernee"])
        if not (grandeur_concernee in ["capacite_installee", "energie_productible","nb_unit"]):
            print("La grandeur %s n'est pas reconnu, la contrainte %d sera ignorée" % (grandeur_concernee, indice_ligne))
            continue

        nombre_annees = donnees_entree.parametres_simulation.horizon_simulation + donnees_entree.parametres_simulation.horizon_prevision
        tableau_valeurs_second_membre = np.zeros(nombre_annees)
        for annee in range(nombre_annees):
            valeur_second_membre_annee = 0
            try:
                valeur_second_membre_annee = float(data_frame_contraintes_trajectoire.loc[indice_ligne, "annee_%d"%annee])
            except (KeyError, IndexError):
                pass
            tableau_valeurs_second_membre[annee] = valeur_second_membre_annee

        nom_contrainte = "contrainte_%d"%indice_ligne
        try:
            nom_contrainte = data_frame_contraintes_trajectoire.loc[indice_ligne, "nom"]
        except (KeyError, IndexError):
            pass

        contrainte_trajectoire = GenerationMixCible.ContrainteTrajectoire(nom_contrainte, liste_actifs_concernes, type_contrainte, grandeur_concernee, tableau_valeurs_second_membre)
        liste_contraintes_trajectoire.append(contrainte_trajectoire)

    return liste_contraintes_trajectoire


# ################################ fonction de lecture pour la génération de mix optimal  #########################################

def lecture_fichier_contraintes_mix(chemin_fichier, donnees_entree):
    data_frame_contraintes_mix = pd.read_csv(chemin_fichier, sep=";")

    liste_contraintes_mix = []

    for indice_ligne in data_frame_contraintes_mix.index:
        liste_actifs_concernes = []
        chaine_caracteres_actifs_concernes = str(data_frame_contraintes_mix.loc[indice_ligne, "actifs_concernes"])
        liste_cles_actifs_concernes = chaine_caracteres_actifs_concernes.split()
        for cle_actif in liste_cles_actifs_concernes:
            try:
                actif = donnees_entree.trouve_actif(cle_actif)
                liste_actifs_concernes.append(actif)
            except KeyError:
                print("La clé d'actif %s n'a pas été reconnue et ne peut être prise en compte dans la contrainte %d." % (cle_actif, indice_ligne))

        type_contrainte = str(data_frame_contraintes_mix.loc[indice_ligne, "type_contrainte"])
        if not (type_contrainte in ["borne_inferieure", "egalite", "borne_superieure"]):
            print("Le type de contrainte %s n'est pas reconnu, la contrainte %d sera ignorée" % (type_contrainte, indice_ligne))
            continue

        grandeur_concernee = str(data_frame_contraintes_mix.loc[indice_ligne, "grandeur_concernee"])
        if not (grandeur_concernee in ["capacite_installee", "energie_productible"]):
            print("La grandeur %s n'est pas reconnu, la contrainte %d sera ignorée" % (grandeur_concernee, indice_ligne))
            continue

        valeur_second_membre = float(data_frame_contraintes_mix.loc[indice_ligne, "valeur_second_membre"])

        nom_contrainte = "contrainte_%d"%indice_ligne
        try:
            nom_contrainte = data_frame_contraintes_mix.loc[indice_ligne, "nom"]
        except (KeyError, IndexError):
            pass

        contrainte_mix = GenerationMixOptimal.ContrainteMix(nom_contrainte, liste_actifs_concernes, type_contrainte, grandeur_concernee, valeur_second_membre)
        liste_contraintes_mix.append(contrainte_mix)

    return liste_contraintes_mix

