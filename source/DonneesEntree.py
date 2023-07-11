# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import numpy as np
import pandas as pd
import sys
import os

import Lecture
import DonneesSimulation

# #### CLASSES D'ACTIFS ####

class Actif:
    """
    Classe représentant un type d'actifs et contenant les caractéristiques de la technologie correspondnate. Cette
    classe est supposée être abstraite et aucune instance ne devrait être construite hors des classes qui en héritent.

    Attributs de classe
    -------------------
    categorie : str
        chaîne de caractères identifiant la classe de l'actif

    Attributs
    ---------
    cle : str
        chaîne de caractères servant à identifier l'actif, elle est notamment utilisée dans les dictionnaires
    puissance : float
        puissance maximale fournie par une unité de l'actif
    cout_fixe_construction : float
        cout de construction de référence d'une unité de l'actif
    cout_fixe_maintenance : float
        cout de maintenance annuel d'une unité de l'actif
    duree_construction : int
        nombre d'années de construction
    duree_vie : int
        nombre d'années de fonctionnement
    taux_actualisation : float
        taux à utiliser pour actualiser les revenus de l'actif, notamment pour les calculs de VAN
    gisement_max : float
        limite de puissance installée
    ajoutable : bool
        booléen indiquant si l'actif peut être ajouté au parc
    demantelable : bool
        booléen indiquant si l'actif peut être retiré du parc
    granularite_investissement : int
        granularité d'investissement
    granularite_demantelement : int
        granularité de démantèlement
    limite_construction_annuelle : int
        le nombre maximum d'unités de l'actif construites une même année
    delai_fermeture : int
        nombre d'années consécutives de non-rentabilité d'une unité de l'actif nécessaires avant de la démanteler
    tableau_variations_cout_construction : np.array
        tableau contenant, pour chaque année, la variation du coût fixe de construction en pourcentage par rapport au
        coût fixe de construction de référence
    """

    categorie = "Abstrait"

    def __init__(self, cle, puissance, cout_fixe_construction, cout_fixe_maintenance, duree_construction, duree_vie, taux_actualisation, gisement_max, ajoutable, demantelable, granularite_investissement, granularite_demantelement, limite_construction_annuelle, delai_fermeture, exigence_rentabilite_premiere_annee):
        self.cle = cle
        self.puissance = puissance
        self._cout_fixe_construction = cout_fixe_construction
        self.cout_fixe_maintenance = cout_fixe_maintenance
        self.duree_construction = duree_construction
        self.duree_vie = duree_vie
        self.taux_actualisation = taux_actualisation
        self.gisement_max = gisement_max
        self.ajoutable = ajoutable
        self.demantelable = demantelable
        self.granularite_investissement = granularite_investissement
        self.granularite_demantelement = granularite_demantelement
        self.limite_construction_annuelle = limite_construction_annuelle
        self.delai_fermeture = delai_fermeture
        self.exigence_rentabilite_premiere_annee = exigence_rentabilite_premiere_annee
        
        # l'éligibilité de l'actif au mécanisme de capacité sera initialisée ulterieurement
        self.eligible_mecanisme_capacite = None
        # le tableau des variations du coût de construction sera initialisé ultérieurement
        self.tableau_variations_cout_construction = None

    def cout_fixe_construction(self, annee):
        return self._cout_fixe_construction * (1 + self.tableau_variations_cout_construction[annee]/100)
        
            
        return puissance 


class ActifPilotable(Actif):
    """
    Cette classe représente un actif pilotable.

    Attributs de classe
    -------------------
    categorie : str
        chaîne de caractères identifiant la classe de l'actif

    Attributs
    ---------
    puissance_nominale : float
        puissance nominale d'une unité de l'actif
    rendement : float
        rendement, compris entre 0 et 1
    emission_carbone : float
        carbone émis par MWh produit
    """

    categorie = "Pilotable"

    def __init__(self, cle, cout_fixe_construction, cout_fixe_maintenance, duree_construction, duree_vie, taux_actualisation, gisement_max, ajoutable, demantelable, granularite_investissement, granularite_demantelement, limite_construction_annuelle, delai_fermeture, exigence_rentabilite_premiere_annee, puissance_nominale, rendement, emission_carbone, combustible):
        super().__init__(cle, puissance_nominale, cout_fixe_construction, cout_fixe_maintenance, duree_construction, duree_vie, taux_actualisation, gisement_max, ajoutable, demantelable, granularite_investissement, granularite_demantelement, limite_construction_annuelle, delai_fermeture, exigence_rentabilite_premiere_annee)
        self.puissance_nominale = puissance_nominale
        self.rendement = rendement
        self.emission_carbone = emission_carbone
        self.combustible = combustible
        self.puissance = puissance_nominale
        
        # l'éligibilité de l'actif au mécanisme de capacité sera initialisée ulterieurement
        self.eligible_mecanisme_capacite = None
         

class ActifENR(Actif):
    """
    Cette classe représente un actif renouvelable.

    Attributs de classe
    -------------------
    categorie : str
        chaîne de caractères identifiant la classe de l'actif

    Attributs
    ---------
    puissance_reference : float
        puissance de référence d'une unité de l'actif
    cout_variable : float
        coût variable
    """

    categorie = "ENR"

    def __init__(self, cle, cout_fixe_construction, cout_fixe_maintenance, duree_construction, duree_vie, taux_actualisation, gisement_max, ajoutable, demantelable, granularite_investissement, granularite_demantelement, limite_construction_annuelle, delai_fermeture, exigence_rentabilite_premiere_annee, puissance_reference, cout_variable):
        super().__init__(cle, puissance_reference, cout_fixe_construction, cout_fixe_maintenance, duree_construction, duree_vie, taux_actualisation, gisement_max, ajoutable, demantelable, granularite_investissement, granularite_demantelement, limite_construction_annuelle, delai_fermeture, exigence_rentabilite_premiere_annee)
        self.puissance_reference = puissance_reference
        self.cout_variable = cout_variable
        self.puissance = puissance_reference
        
        # l'éligibilité de l'actif au mécanisme de capacité sera initialisée ulterieurement
        self.eligible_mecanisme_capacite = None


class ActifStockage(Actif):
    """
    Cette classe représente un actif de stockage.

    Attributs de classe
    -------------------
    categorie : str
        chaîne de caractères identifiant la classe de l'actif

    Attributs
    ---------
    puissance_nominale_charge : float
        puissance nominale en charge d'une unité de l'actif
    puissance_nominale_charge : float
        puissance nominale en décharge d'une unité de l'actif
    rendement_charge : float
        rendement en charge, compris entre 0 et 1
    rendement_decharge : float
        rendement en décharge, compris entre 0 et 1
    capacite : float
        volume d'énergie maximal stocké par une unité
    stock_initial : float
        fraction de la capacité en stock au début de chaque année, compris entre 0 et 1
    cout_variable : float
        coût variable
    """

    categorie = "Stockage"

    def __init__(self, cle, cout_fixe_construction, cout_fixe_maintenance, duree_construction, duree_vie, taux_actualisation, gisement_max, ajoutable, demantelable, granularite_investissement, granularite_demantelement, limite_construction_annuelle, delai_fermeture, exigence_rentabilite_premiere_annee, puissance_nominale_charge, puissance_nominale_decharge, rendement_charge, rendement_decharge, capacite, stock_initial, cout_variable,duree):
        super().__init__(cle, puissance_nominale_decharge, cout_fixe_construction, cout_fixe_maintenance, duree_construction, duree_vie, taux_actualisation, gisement_max, ajoutable, demantelable, granularite_investissement, granularite_demantelement, limite_construction_annuelle, delai_fermeture, exigence_rentabilite_premiere_annee)
        self.puissance_nominale_charge = puissance_nominale_charge
        self.puissance_nominale_decharge = puissance_nominale_decharge
        self.rendement_charge = rendement_charge
        self.rendement_decharge = rendement_decharge
        self.capacite = capacite
        self.stock_initial = stock_initial
        self.cout_variable = cout_variable
        self.duree = duree
        self.puissance = puissance_nominale_decharge
        
        # l'éligibilité de l'actif au mécanisme de capacité sera initialisée ulterieurement
        self.eligible_mecanisme_capacite = None


# #### CLASSES DE PARAMETRES ####

class ParametresOptimisation:
    """
    Cette classe regroupe les paramètres spécifiques à la résolution des problèmes de dispatch.

    Attributs
    ---------
    fenetre_optimisation : int
        taille, en nombre d'heures, d'une subdivision de l'année, doit être un diviseur de 8760
    vision_supplementaire : int
        nombre d'heures de la fenêtre suivante à intégrer dans un dispatch partiel pour créer des superpositions
        entre les plages couvertes par les différents sous-problèmes
    """

    def __init__(self, fenetre_optimisation, vision_supplementaire):
        self.fenetre_optimisation = fenetre_optimisation
        self.vision_supplementaire = vision_supplementaire
        

class ParametresPonderation:
    """
    Cette classe regroupe les paramètres spécifiques à la pondération des scénarios météos.

    Attributs
    ---------
    ponderation_x : float
        ponderation affectée au scénario météo x. Il y a autant d'attribut que de scénarios météos
    """

    def __init__(self, df_param_ponderation):
    
        for indice_ponderation in df_param_ponderation.index :
            
            val = df_param_ponderation.at[indice_ponderation, "value"]
            setattr(self, indice_ponderation, val)
        

class ParametresSimulation:
    """
    Cette classe regroupe les paramètres généraux d'une simulation.

    Attributs
    ---------
    horizon_simulation : int
        nombre d'années simulées
    horizon_prevision : int
        nombre d'années futures que les acteurs sont capables d'anticiper
    architecture : str
        type de market design simulé, valeurs possibles : "EOM", "AOCLT"
    limite_capacite : float
        budget annuel en puissance consacré à l'investissement
    limite_argent : float
        budget annuel en argent consacré à l'investissement
    sortie_complete : bool
        booléen indiquant si l'utilisateur souhaite une sortie détaillée
    VOLL : float
        valeur de la VOLL
    plafond_prix : float
        valeur maximale du prix spot
    quantile_meteo : float
        paramètre du quantile à utiliser si VAN_equivalente a pour valeur "quantile"
    VAN_equivalente : str
        fonction à appliquer aux VAN des différents scénarios météo pour obtenir la VAN équivalente, valeurs possibles :
        "moyenne", "médiane", "minimum", "maximum", "quantile"
    critere_investissement : str
        critère à utiliser pour la prise de décision d'investissement, valeurs possibles : "PI", "VAN_MW"
    certificats_verts : bool
        booléen indiquant si les certificats verts sont pris en compte dans les revenus des ENR
    certificats_verts_au_productible : bool
        booléen indiquant si l'utilisateur souhaite que les certificats verts soient comptabilisés pour l'énergie
        productible au lieu de l'énergie produite dans les revenus des ENR
    sequence_investissement : bool
        booleen indiquant si la séquence d'investissement doit être effectuée
    sequence_demantelement : bool
        booleen indiquant si la séquence de démantèlement doit être effectuée
    contrainte_rentabilite_premiere_annee : bool
        booleen indiquant si le revenu équivalent lors de la première année de fonctionnement d'une unité doit être
        positif pour décider de la construire
    nb_meteo : int
        integer indiquant le nombre de scénario météo pris en compte dans la simulation 
    critere_risque : str
        string indiquant la méthode utilisée pour prendre en compte l'aversion au risque des investisseurs 
        par défaut, les investisseurs sont considérés neutre face au risque
    """

    def __init__(self, df_param_simu):
             
        df_default_values = pd.read_csv("param_default_values.csv",sep=";",index_col=0)
        
        for param in df_default_values.index :
       
            if param in df_param_simu.index : 

                val = df_param_simu.at[param,"value"]
            else : 
                val = df_default_values.at[param,"default_value"]
                print("parametres_simulation : setting [%s] default value for %s"%(str(val),param))

            param_type = df_default_values.at[param,"type"]
            
            if param_type == "boolean":
                if type(val) != "bool":
                    if val.lower() == "false":
                        val = False
                    elif val.lower() == "true":
                        val = True
            elif param_type == "float":
                val = np.float(val)
            elif param_type == "int":
                val = np.int(val)
            else :
                val = str(val)

            setattr(self,param,val)
    
# #### CLASSES D'AMBIANCES ####

class Meteo:
    """
    Cette classe regroupe les données décrivant une "météo".

    Attributs
    ---------
    nom : str
        nom de la météo
    _tableau_demande : np.array
        tableau contenant les volumes d'énergie demandés à chaque heure de l'année et pour chaque année représentée
    _dict_facteurs_production_actifs_ENR : dict
        dictionnaire contenant, pour chaque type d'actif renouvelable, le tableau des facteurs de production à chaque
        heure de l'année

    Méthodes
    --------
    demande(self, annee, heure)
        Renvoie le volume d'énergie demandée pour l'heure et l'année données.
    demande_annuelle(self, annee)
        Renvoie le tableau des volumes d'énergie demandés pour chaque heure de l'année données.
    facteur_production_ENR(self, cle_actif_ENR, heure)
        Renvoie le facteur de production de l'actif ENR correspondant à la clé pour l'heure spécifiée.
    facteurs_production_ENR(self, cle_actif_ENR)
        Renvoie le tableau des facteurs de production de l'actif ENR correspondant à la clé.
    """

    def __init__(self, nom, tableau_demande, dict_facteurs_production_actifs_ENR):
        self.nom = nom
        self._tableau_demande = tableau_demande
        self._dict_facteurs_production_actifs_ENR = dict_facteurs_production_actifs_ENR

    def demande(self, annee, heure):
        """
        Renvoie le volume d'énergie demandée pour l'heure et l'année données.

        Paramètres
        ----------
        annee : int
            année à laquelle on veut connaître la demande, comptée en partant de l'année de la météo
        heure : int
            heure à laquelle on veut connaître la demande

        Retours
        -------
        float
            volume d'énergie demandé
        """
        return self._tableau_demande[annee][heure]  #!!! revoir

    def demande_annuelle(self, annee):
        """
        Renvoie le tableau des volumes d'énergie demandés pour chaque heure de l'année données.

        Paramètres
        ----------
        annee : int
            année à laquelle on veut connaître la demande, comptée en partant de l'année de la météo

        Retours
        -------
        np.array
            volumes d'énergie demandé
        """
        return self._tableau_demande[annee]

    def facteur_production_ENR(self, cle_actif_ENR, heure):
        """
        Renvoie le facteur de production de l'actif ENR correspondant à la clé pour l'heure spécifiée.

        Paramètres
        ----------
        cle_actif_ENR : str
            clé de l'actif ENR dont on veut connaître le facteur de production
        heure : int
            heure à laquelle on veut connaître le facteur de production

        Retours
        -------
        float
            facteur de production
        """
        return self._dict_facteurs_production_actifs_ENR[cle_actif_ENR][heure]

    def facteurs_production_ENR(self, cle_actif_ENR):
        """
        Renvoie le tableau des facteurs de production de l'actif ENR correspondant à la clé.

        Paramètres
        ----------
        cle_actif_ENR : str
            clé de l'actif ENR dont on veut connaître le facteur de production

        Retours
        -------
        np.array
            tableau des facteurs de production
        """
        return self._dict_facteurs_production_actifs_ENR[cle_actif_ENR]




class DonneesAnnuelles:
    """
    Cette classe regroupe les données d'une année au sein d'une ambiance.

    Attributs
    ---------
    _prix_carbone : float
        prix du CO2
    _prix_certificats_verts : float
        prix des certificats verts pour les ENR
    _dict_prix_combustible_actifs_pilotables : dict
        dictionnaire contenant les prix des combustibles pour les actifs pilotables
    _liste_meteos : list
        liste contenant les différentes instances de Meteo possibles

    Méthodes
    --------
    prix_carbone(self, annee)
        Renvoie le prix du CO2.
    prix_certificats_verts(self, annee)
        Renvoie le prix des certificats verts.
    prix_combustible(self, actif_pilotable, annee)
        Renvoie le prix du combustible de l'actif correspondant à la clé donnée.
    nombre_meteos(self)
        Renvoie le nombre de météos dans _liste_meteos.
    """

    def __init__(self, prix_carbone, prix_certificats_verts, dict_prix_combustibles_actifs_pilotables, liste_meteos):
        self._prix_carbone = prix_carbone
        self._prix_certificats_verts = prix_certificats_verts       
        self._dict_prix_combustible_actifs_pilotables = dict_prix_combustibles_actifs_pilotables
        self._liste_meteos = liste_meteos

    def prix_carbone(self, annee):
        """
        Renvoie le prix du CO2.

        Paramètres
        ----------
        annee : int
            année à laquelle on veut connaître le prix du carbone, comptée à partir de l'année des données annuelles

        Retours
        -------
        float
            prix du CO2
        """

        return self._prix_carbone[annee]

    def prix_certificats_verts(self, annee):
        """
        Renvoie le prix des certificats verts.

        Paramètres
        ----------
        annee : int
            année à laquelle on veut connaître le prix des REC, comptée à partir de l'année des données annuelles

        Retours
        -------
        float
            prix des certificats verts
        """
        return self._prix_certificats_verts[annee]

    def prix_combustible(self, actif_pilotable, annee):
        """
        Renvoie le prix du combustible de l'actif correspondant à la clé donnée.

        Paramètres
        ----------
        actif_pilotable : ActifPilotable
            clé de l'actif pilotable dont on souhaite connaître le prix du combustible
        annee : int
            année à laquelle on veut connaître le prix du combustible, comptée à partir de l'année des données annuelles

        Retours
        -------
        float
            prix du combustible
        """

        return self._dict_prix_combustible_actifs_pilotables[actif_pilotable.combustible][annee]

    def nombre_meteos(self):
        """
        Renvoie le nombre de météos dans _liste_meteos.

        Retours
        -------
        int
            nombre de météos
        """
        return len(self._liste_meteos)

    def __getitem__(self, indice_meteo):
        return self._liste_meteos[indice_meteo]


class Ambiance:
    """
    Cette classe représente une ambiance.

    Attributs
    ---------
    nom : str
        nom de l'ambiance
    _liste_donnees_annuelles : list
        liste contenant les instances de DonneesAnnuelles
    """

    def __init__(self, nom, liste_donnees_annuelles):
        self.nom = nom
        self._liste_donnees_annuelles = liste_donnees_annuelles

    def __getitem__(self, annee):
        return self._liste_donnees_annuelles[annee]


# #### CLASSE DE DONNEES D'ENTREE ####

class DonneesEntree:
    """
    Cette classe regroupe les données résultant de la lecture des fichiers d'entrée.

    Les données stockées dans cette structure sont supposées être constantes au cours d'une simulation et ne devraient
    pas être modifiées à partir du moment où les données d'entrée ont été lues.

    Attributs
    ---------
    dict_actifs_pilotables : dict
        dictionnaire contenant les instances d'ActifPilotable
    dict_actifs_ENR : dict
        dictionnaire contenant les instances d'ActifENR
    dict_actifs_stockage : dict
        dictionnaire contenant les instances d'ActifStockage
    tableau_ambiances : np.array
        tableau contenant les instances d'Ambiance
    ambiance_realisee : Ambiance
        instance d'Ambiance à utiliser pour la réalisation
    parametres_optimisation : ParametresOptimisation
        paramètres d'optimisation
    parametres_simulation : ParametresSimulation
        paramètres de simulation
    parametres_appels_offres : ParametresAppelsOffres
        paramètres d'appels d'offres
    mix_cible : dict
        dictionnaire contenant, pour chaque actif, le tableau annuel du nombre d'unités cible
    """

    def __init__(self, dict_actifs_pilotables, dict_actifs_ENR, dict_actifs_stockage, ambiances, realisation, parametres_optimisation, parametres_simulation, df_parametres_ponderation):
        self.dict_actifs_pilotables = dict_actifs_pilotables
        self.dict_actifs_ENR = dict_actifs_ENR
        self.dict_actifs_stockage = dict_actifs_stockage
        self.ambiances = ambiances
        self.realisation = realisation
        self.parametres_optimisation = parametres_optimisation
        self.parametres_simulation = parametres_simulation
        self.df_parametres_ponderation = df_parametres_ponderation

        # initialisation des paramètres facultatifs pour les AOCLT
        self.parametres_appels_offres = None
        self.mix_cible = dict()

        # initialisation des paramètres facultatifs pour le mécanisme de capacité
        self.parametres_mecanisme_capacite = None
        self.capacite_cible = dict()

    def trouve_actif(self, cle_actif):
        """
        Retourne l'actif correspondant à la clé passée en argument et provoque une erreur si la clé n'existe pas.

        Paramètres
        ----------
        cle_actif : str
            clé de l'actif recherché

        Retours
        -------
        Actif
            actif correspondant à la clé
        """

        # recherche parmi les actifs pilotables
        try:
            actif = self.dict_actifs_pilotables[cle_actif]
            return actif
        except KeyError:
            # recherche parmi les actifs ENR
            try:
                actif = self.dict_actifs_ENR[cle_actif]
                return actif
            except KeyError:
                # recherche parmi les actifs de stockage
                try:
                    actif = self.dict_actifs_stockage[cle_actif]
                    return actif
                except KeyError:
                    raise KeyError("Tentative d'accès à un actif avec une clé inexistante")

    def actifs_pilotables(self):
        """
        Générateur énumérant les actifs pilotables.

        Retours
        -------
        ActifPilotable
            actif pilotable
        """

        for cle, actif in self.dict_actifs_pilotables.items():
            yield actif

    def actifs_ENR(self):
        """
        Générateur énumérant les actifs ENR.

        Retours
        -------
        ActifENR
            actif renouvelable
        """
        for cle, actif in self.dict_actifs_ENR.items():
            yield actif

    def actifs_stockage(self):
        """
        Générateur énumérant les actifs de stockage.

        Retours
        -------
        ActifStockage
            actif de stockage
        """
        for cle, actif in self.dict_actifs_stockage.items():
            yield actif

    def tous_actifs(self):
        """
        Générateur énumérant tous les actifs.

        Retours
        -------
        Actif
            actif
        """
        for cle, actif in self.dict_actifs_pilotables.items():
            yield actif
        for cle, actif in self.dict_actifs_ENR.items():
            yield actif
        for cle, actif in self.dict_actifs_stockage.items():
            yield actif

    def actifs_hors_stockage(self):
        """
        Générateur énumérant tous les actifs sauf ceux de stockage.

        Retours
        -------
        Actif
            actif
        """
        for cle, actif in self.dict_actifs_pilotables.items():
            yield actif
        for cle, actif in self.dict_actifs_ENR.items():
            yield actif

    
    def get_parc_anticipation(self):
    
        dico_parcs_anticipes_boucle = {}
        
        for ambiance in self.ambiances :    

            chemin_parc_anticipation = os.path.join(self.chemin_dossier,"Parc_Anticipation",ambiance)               
            parc_initial_anticipation = Lecture.lecture_fichier_parc_initial(os.path.join( chemin_parc_anticipation,"parc_initial.csv" ), self)
            registre_ouvertures_anticipation = Lecture.lecture_fichier_registre(os.path.join( chemin_parc_anticipation,"registre_ouvertures.csv" ), self)
            registre_fermetures_anticipation = Lecture.lecture_fichier_registre(os.path.join( chemin_parc_anticipation,"registre_fermetures.csv"), self)     
                                
            parc_anticipation = DonneesSimulation.Parc(parc_initial_anticipation, registre_ouvertures_anticipation, registre_fermetures_anticipation, self)    
        
            dico_parcs_anticipes_boucle[ambiance] = parc_anticipation                                     
    
        return dico_parcs_anticipes_boucle
        
 
    def mise_en_coherence_parc(self,annee,dico_parcs_anticipes_boucle,parc,add_current_investment=False,add_current_divestment=False):
       
        """
        
        Met en cohérence un dico de parcs anticipés avec le parc réel pour une année donnée
        
        Paramètres
        ----------
        annee : int
            année à partir de laquelle on veut mettre les parcs en cohérence
        dico_parcs_anticipes_boucle : dico de parc
            parcs anticipes a mettre en coherence
        parc : parc
            parc reel
         add_current_investment : bool
            parametre indiquant si l'on veut ajouter les investissement des parcs anticipes pour l'annee courante
            (utile pour la boucle de demantelemt sequentielle ou l'on a besoin de connaitre les investissement
            qui vont etre pris pour prendre la "bonne" decision)

        Retours
        -------
        dico_df_nb_unites_ambiances
            dico de DataFrame comportant pour chaque type d'actif le nombre d'unites pour chaque annee       
        
        
        """

        df_parc = parc.get_df_nb_unites()
                          
        dico_df_nb_unites_ambiances = {}
        
        for ambiance in self.ambiances :
        
            df_nb_unites = pd.DataFrame()
            
            parc_ambiance = dico_parcs_anticipes_boucle[ambiance]
            
            df_parc_ambiance = parc_ambiance.get_df_nb_unites()
            df_rythme_parc_ambiance = df_parc_ambiance.diff().fillna(df_parc_ambiance)
            
            df_diff = df_parc_ambiance - df_parc

            for actif in self.tous_actifs():
            
                # pour toutes les annees de 0 a l'annee cible, le nombre d'unites
                # correspond au nombre reel d'unites
                
                for n in range(annee+1):
                
                    df_nb_unites.at[n,actif.cle] = df_parc.at[n,actif.cle]

                # pour l'annee cible, on ajoute eventuellement les investissements et déclassements correspondant au parc
                # anticipe
                
                if add_current_investment : 
                    if actif.ajoutable and not actif.demantelable :
                        df_nb_unites.at[annee,actif.cle] = df_nb_unites.at[annee,actif.cle] + df_rythme_parc_ambiance.at[annee,actif.cle]
                if add_current_divestment :
                    if not actif.ajoutable and actif.demantelable :
                        if df_nb_unites.at[annee,actif.cle] >= df_parc_ambiance.at[annee,actif.cle]:
                            nb_unite_a_fermer = df_nb_unites.at[annee,actif.cle] -  df_parc_ambiance.at[annee,actif.cle]
                            df_nb_unites.at[annee,actif.cle] = df_nb_unites.at[annee,actif.cle] - nb_unite_a_fermer
                        
                for n in range(annee+1,self.parametres_simulation.horizon_simulation):           
                                       
                    # si une techno  est demantelable mais pas ajoutable, on veille a ce que
                    # le parc anticipe ne declasse pas moins vite que ce que les durees de vie permettent
                    # (par exemple en cas de retard au declassement)
                                       
                    if actif.demantelable and not actif.ajoutable  :
                    
                        val_rythme = df_nb_unites.at[n-1,actif.cle] + df_rythme_parc_ambiance.at[n,actif.cle]
                        val_reelle = df_parc.at[n,actif.cle]
                        val_min = np.min([val_rythme,val_reelle])
                        
                        df_nb_unites.at[n,actif.cle] = val_min
                        
                    else :
                    
                        df_nb_unites.at[n,actif.cle] = df_nb_unites.at[n-1,actif.cle] + df_rythme_parc_ambiance.at[n,actif.cle]
                                                        
                        
            df_nb_unites = df_nb_unites.clip(lower=0,upper=None)
            dico_df_nb_unites_ambiances[ambiance] = df_nb_unites

    
        return dico_df_nb_unites_ambiances
        
        
    def calcul_capacite_cible(self, parc_ambiance, nom_ambiance) : 
        """
        
        Calcul la capacité cible nécessaire à partir du parc anticipé 
        
        Paramètres
        ----------
        parc_ambiance : DonneesSimulation.Parc
            parc anticipé dans l'ambiance en question
        nom_ambiance : str
            nom de l'ambiance en question

        Retours
        -------
        capacite_cible_ambiance : list
            liste du besoin de capacité estimée pour l'ensemble des années de la simulation à partir du parc anticipé      
           
        """
        capacite_cible_ambiance = []

        nb_meteo = self.parametres_simulation.nb_meteo
        
        df_param_mecapa = self.df_param_mecapa
        critere_besoin_capacitaire = df_param_mecapa.at['critere_besoin_capacitaire', "value"] # C'est le critère de dimensionnement, 3h/an généralement 
        
        data_frame_actifs_eligibles_mecapa = self.data_frame_actifs_eligibles_mecapa
        liste_actifs_non_eligibles_mecapa = []
        for actif in self.tous_actifs() : 
        
            try : 
                if not data_frame_actifs_eligibles_mecapa.at[actif.cle, 'eligible'] :
                    liste_actifs_non_eligibles_mecapa.append(actif.cle)
            except KeyError :
                liste_actifs_non_eligibles_mecapa.append(actif.cle)
        
        ambiance = self.ambiances[nom_ambiance]
        
        df_derating_factor = pd.DataFrame()
        df_nb_unites = parc_ambiance.get_df_nb_unites().loc[0:]
        
        # les fichiers de demande et les fichiers de chronique de disponibilité sont identiques dans chaque années car ils contiennent toutes les années, il suffit donc d'en regarder un seul
        for annee in ambiance :
            
            demande_residuelle_annee = pd.DataFrame()
            
            for meteo in range(nb_meteo) : 
                
                demande_brute_annee_meteo = ambiance[annee]["meteo_%d"%meteo]["demande"]["Annee_%d"%annee].copy()
                dispo_pilot_meteo = ambiance[annee]["meteo_%d"%meteo]["dispo"]
                facteur_charge_enr_meteo = ambiance[annee]["meteo_%d"%meteo]["fc"]
                
                demande_residuelle_annee_meteo = pd.DataFrame()
                demande_residuelle_annee_meteo["demande_residuelle"] = demande_brute_annee_meteo
                for cle_actif in liste_actifs_non_eligibles_mecapa : 
                    actif = self.trouve_actif(cle_actif)
                    disponibilite = pd.DataFrame([1 for k in range(8760)], columns = ["Annee_%d"%annee])["Annee_%d"%annee]
                    
                    if actif.categorie == "Pilotable":
                        try :
                            disponibilite = dispo_pilot_meteo["%s_%d"%(cle_actif, annee)]
                        except KeyError:
                            pass
                    elif actif.categorie == "ENR":
                        try : 
                            disponibilite = facteur_charge_enr_meteo["%s_%d"%(cle_actif, annee)]
                        except KeyError:
                            pass
                        
                    nbr_unite_actif_annee = df_nb_unites.at[annee, cle_actif]
                    puissance = 0
                    if actif.categorie == "Stockage":
                        puissance = actif.puissance_nominale_decharge
                    elif actif.categorie == "Pilotable":
                        puissance = actif.puissance_nominale
                    elif actif.categorie == "ENR":
                        puissance = actif.puissance_reference
                    

                    demande_residuelle_annee_meteo["demande_residuelle"] -=  nbr_unite_actif_annee * puissance * disponibilite
                    demande_residuelle_annee_meteo[cle_actif] = disponibilite
                
                for i in range(self.df_parametres_ponderation.at[meteo, "nb_scenario_represente"]) :     
                    demande_residuelle_annee = pd.concat([demande_residuelle_annee, demande_residuelle_annee_meteo], ignore_index = True)
                    
            demande_residuelle_annee_sort =  demande_residuelle_annee.sort_values(ascending = False, by="demande_residuelle", ignore_index = True)  
            nb_scenario = sum(self.df_parametres_ponderation["nb_scenario_represente"])
            capa_annee = demande_residuelle_annee_sort.iloc[critere_besoin_capacitaire*nb_scenario]["demande_residuelle"]
            df_derating_factor[annee] = demande_residuelle_annee_sort.iloc[critere_besoin_capacitaire * nb_scenario][1:]

            capacite_cible_ambiance.append(capa_annee)    
            
        return capacite_cible_ambiance, df_derating_factor
                    