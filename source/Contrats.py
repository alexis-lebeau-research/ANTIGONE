# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import numpy as np
import IndicateursEconomiques
import DonneesSimulation
import statistics as stat

import sys
import os

import pandas as pd

class ContratAbstrait:
    """
    Cette classe est la base de toutes les classes de contrats, elle est supposée être abstraite et ne devrait pas
    être insanciée autrement que par les classes qui en héritent.

    Attributs de classe
    -------------------
    categorie : str
        chaîne de caractères identifiant la classe de contrat

    Attributs
    ---------
    annee_emission : int
        année d'émission du contrat
    annee_debut : int
        année de début du contrat
    annee_fin : int
        année de fin du contrat, non incluse dans la durée du contrat

    Méthodes
    --------
    calcul_revenu_annuel(self, actif, annee, resultat_annuel, donnees_simulation)
        Calcule le revenu d'une unité de la technologie actif sous le contrat considéré pour l'ambiance,
        l'année et le résultat de dispatch donnés.
    """

    categorie = "contrat_abstrait"

    def __init__(self, annee_emission, annee_debut, annee_fin):
        self.annee_emission = annee_emission
        self.annee_debut = annee_debut
        self.annee_fin = annee_fin

    def calcul_revenu_annuel(self, actif, annee, resultat_annuel, donnees_entree):
        """
        Calcule le revenu d'une unité de la technologie actif sous le contrat considéré pour l'année, les données
        annuelles et le résultat de dispatch donnés.

        Chaque classe de contrat qui hérite de ContratAbstrait doit normalement réimplémenter cette méthode selon ses
        spécificités. Cette implémentation par défaut renvoie le revenu marché hors contrat.

        Paramètres
        ----------
        actif : DonneesEntree.Actif
            type d'actif pour lequel on veut connaître le revenu unitaire
        annee : int
            année dont on veut connaître le revenu
        resultat_annuel : DispatchV0.ResultatAnnuel
            résultat de dispatch à utiliser, il devrait correspondre à l'année données
        donnees_entree : DonneesEntree.DonneesEntree
            données d'entrée à utiliser

        Retours
        -------
        float
            valeur du revenu
        """
        return IndicateursEconomiques.calcul_revenu_annuel_hors_contrat(actif, resultat_annuel, donnees_entree)

    def calcul_cout_annuel(self, actif, annee, resultat_annuel, donnees_entree):
        """
        Calcule le coût du contrat pour l'agence de régulation lorsqu'une unité de la technologie actif en bénéficie
        pour l'année, les données annuelles et le résultat de dispatch donnés.

        Chaque classe de contrat qui hérite de ContratAbstrait doit normalement réimplémenter cette méthode selon ses
        spécificités. Cette implémentation par défaut renvoie 0.

        Paramètres
        ----------
        actif : DonneesEntree.Actif
            type d'actif pour lequel on veut connaître le revenu unitaire
        annee : int
            année dont on veut connaître le revenu
        resultat_annuel : DispatchV0.ResultatAnnuel
            résultat de dispatch à utiliser, il devrait correspondre à l'ambiance et à l'année données
        donnees_entree : DonneesEntree.DonneesEntree
            données d'entrée à utiliser

        Retours
        -------
        float
            coût du contrat
        """
        return 0


class ContratParfait(ContratAbstrait):
    """
    Cette classe représente un contrat parfait.

    Attributs de classe
    -------------------
    categorie : str
        chaîne de caractères identifiant la classe de contrat
    dict_nombre_heures_fonctionnement_historique : dict
        dictionnaire contenant un nombre d'heures de fonctionnement historique pour chaque type d'actif
    cout_variable_equivalent : str
        fonction à appliquer aux coûts variables des différentes ambiances pour calculer le coût variable équivalent,
        valeurs possibles : "Med", "Min", "Max", "Moy"

    Attributs
    ---------
    montant_remuneration : float
        estimation du LCOE calculée au moment de l'émission du contrat

    Méthodes de classe
    ------------------
    calcul_revenu_annuel(self, actif, ambiance, annee, resultat_annuel, donnees_simulation)
        Calcule le revenu d'une unité de la technologie actif sous le contrat considéré pour l'année et le résultat de
        dispatch donnés.
    calcul_cout_annuel(self, actif, annee, resultat_annuel, donnees_entree)
        Calcule le coût du contrat pour l'agence de régulation lorsqu'une unité de la technologie actif en bénéficie
        pour l'année et le résultat de dispatch donnés.
    calcul_LCOE(cls, actif, annee_courante, donnees_entree)
        Calcule une estimation à l'année courante du LCOE pour une unité de l'actif donné.
    """

    categorie = "contrat_parfait"

    cout_variable_equivalent = None

    # attribut de classe qui sera initialisé, si nécessaire, lors de la lecture des fichiers de données
    dict_nombre_heures_fonctionnement_historique = dict()

    def __init__(self, montant_remuneration, annee_emission, annee_debut, annee_fin):
        super().__init__(annee_emission, annee_debut, annee_fin)
        self.montant_remuneration = montant_remuneration

    def calcul_revenu_annuel(self, actif, annee, resultat_annuel, donnees_entree):
        """
        Calcule le revenu d'une unité de la technologie actif sous le contrat considéré pour l'année et le résultat de
        dispatch donnés.

        Paramètres
        ----------
        actif : DonneesEntree.Actif
            type d'actif pour lequel on veut connaître le revenu unitaire
        annee : int
            année dont on veut connaître le revenu
        resultat_annuel : DispatchV0.ResultatAnnuel
            résultat de dispatch à utiliser, il devrait correspondre à l'année données
        donnees_entree : DonneesEntree.DonneesEntree
            données d'entrée à utiliser

        Retours
        -------
        float
            valeur du revenu
        """
        if not(self.annee_debut <= annee < self.annee_fin):
            return IndicateursEconomiques.calcul_revenu_annuel_hors_contrat(actif, resultat_annuel, donnees_entree)
        # le contrat parfait garantit que l'unité est exactement rentable, le revenu est donc 0
        return 0

    def calcul_cout_annuel(self, actif, annee, resultat_annuel, donnees_entree):
        """
        Calcule le coût du contrat pour l'agence de régulation lorsqu'une unité de la technologie actif en bénéficie
        pour l'année et le résultat de dispatch donnés.

        Paramètres
        ----------
        actif : DonneesEntree.Actif
            type d'actif pour lequel on veut connaître le revenu unitaire
        annee : int
            année dont on veut connaître le revenu
        resultat_annuel : DispatchV0.ResultatAnnuel
            résultat de dispatch à utiliser, il devrait correspondre à l'année données
        donnees_entree : DonneesEntree.DonneesEntree
            données d'entrée à utiliser

        Retours
        -------
        float
            coût du contrat
        """

        if not(self.annee_debut <= annee < self.annee_fin):
            return 0

        revenu_hors_contrat = IndicateursEconomiques.calcul_revenu_annuel_hors_contrat(actif, resultat_annuel, donnees_entree)
        cout_annuel = -revenu_hors_contrat

        return cout_annuel

    @classmethod
    def calcul_LCOE(cls, actif, annee_courante, donnees_entree):
        """
        Calcule une estimation à l'année courante du LCOE pour une unité de l'actif donné.

        Il s'agit d'une méthode de classe qui devrait être appelée avant la création d'une instance de ContratParfait.

        Paramètres
        ----------
        actif : DonneesEntree.Actif
            type d'actif pour lequel on veut connaître le LCOE
        annee_courante : int
            année à laquelle on réalise l'estimation
        donnees_entree : DonneesEntree.DonneesEntree
            données d'entrée à utiliser

        Retours
        -------
        float
            valeur estimée du LCOE
        """
        liste_couts_variables = []
        for indice_ambiance in range(len(donnees_entree.tableau_ambiances)):
            ambiance = donnees_entree.tableau_ambiances[indice_ambiance]
            cout_variable_actif = 0
            if actif.categorie == "Pilotable":
                cout_variable_actif = 1 / actif.rendement * ambiance[annee_courante].prix_combustible(actif, 0) + \
                                      ambiance[annee_courante].prix_carbone(0) * actif.emission_carbone
            elif actif.categorie == "ENR":
                cout_variable_actif = actif.cout_variable - ambiance[annee_courante].prix_certificats_verts(0)
            elif actif.categorie == "Stockage":
                cout_variable_actif = actif.cout_variable

            liste_couts_variables.append(cout_variable_actif)

        cout_variable_equivalent_actif = 0
        parametre_cout_variable_equivalent = cls.cout_variable_equivalent
        if (parametre_cout_variable_equivalent == "mediane"):
            cout_variable_equivalent_actif = stat.median(liste_couts_variables)
        elif (parametre_cout_variable_equivalent == "minimum"):
            cout_variable_equivalent_actif = min(liste_couts_variables)
        elif (parametre_cout_variable_equivalent == "maximum"):
            cout_variable_equivalent_actif = max(liste_couts_variables)
        elif (parametre_cout_variable_equivalent == "moyenne"):
            cout_variable_equivalent_actif = stat.mean(liste_couts_variables)
        else:
            # par défaut on prend la moyenne
            cout_variable_equivalent_actif = stat.mean(liste_couts_variables)

        puissance = actif.puissance

        LCOE = cout_variable_equivalent_actif
        nombre_heures_fonctionnement_historique = cls.dict_nombre_heures_fonctionnement_historique[actif.cle]
        if (nombre_heures_fonctionnement_historique > 0):
            LCOE += (actif.cout_fixe_maintenance + IndicateursEconomiques.calcul_investissement_annualise(actif, annee_courante)) / (
                        puissance * nombre_heures_fonctionnement_historique)
        else:
            LCOE = float("inf")

        return LCOE


class ContratPourDifference(ContratAbstrait):
    """
    Cette classe représente un contrat pour différence.

    Attributs de classe
    -------------------
    categorie : str
        chaîne de caractères identifiant la classe de contrat
    dict_volumes_contractuels : dict
        dictionnaires contenant, pour chaque type d'actif, le volume d'énergie à fournir en ruban à chaque heure de
        l'année pendant la durée du contrat
    duree : int
        durée du contrat en années


    Attributs
    ---------
    volume_contractuel : float
        volume d'énergie à fournir en ruban à chaque heure de l'année pendant la durée du contrat
    prix_contractuel : float
        prix fixe de l'énergie correspondant au volume contractuel tout au long de la durée du contrat

    Méthodes
    --------
    calcul_revenu_annuel(self, actif, ambiance, annee, resultat_annuel, donnees_simulation)
        Calcule le revenu d'une unité de la technologie actif sous le contrat considéré pour l'année et le résultat de
        dispatch donnés.
    calcul_cout_annuel(self, actif, annee, resultat_annuel, donnees_entree)
        Calcule le coût du contrat pour l'agence de régulation lorsqu'une unité de la technologie actif en bénéficie
        pour l'année et le résultat de dispatch donnés.
    calcul_prix_annulation_VAN(cls, actif, matrice_resultats_annuels, annee_debut_resultats, donnees_entree,
    donnees_simulation)
        Calcule la valeur du prix contractuel qui annule la VAN équivalente d'une unité de l'actif sous un contrat pour
        différence.
    """

    categorie = "contrat_pour_difference"

    # attributs de classe qui seront initialisés, si nécessaire, lors de la lecture des fichiers de données
    dict_volumes_contractuels = dict()
    duree = 0

    def __init__(self, volume_contractuel, prix_contractuel, annee_emission, annee_debut, annee_fin):
        super().__init__(annee_emission, annee_debut, annee_fin)
        self.volume_contractuel = volume_contractuel
        self.prix_contractuel = prix_contractuel

    def calcul_revenu_annuel(self, actif, annee, resultat_annuel, donnees_entree):
        """
        Calcule le revenu d'une unité de la technologie actif sous le contrat considéré pour l'année et le résultat de
        dispatch donnés.

        Paramètres
        ----------
        actif : DonneesEntree.Actif
            type d'actif pour lequel on veut connaître le revenu unitaire
        annee : int
            année dont on veut connaître le revenu
        resultat_annuel : DispatchV0.ResultatAnnuel
            résultat de dispatch à utiliser, il devrait correspondre à l'ambiance et à l'année données
        donnees_entree : DonneesEntree.DonneesEntree
            données d'entrée à utiliser

        Retours
        -------
        float
            valeur du revenu
        """
        if not(self.annee_debut <= annee < self.annee_fin):
            return IndicateursEconomiques.calcul_revenu_annuel_hors_contrat(actif, resultat_annuel, donnees_entree)

        revenu_annuel = IndicateursEconomiques.calcul_revenu_annuel_hors_contrat(actif, resultat_annuel, donnees_entree)
        revenu_annuel += self.volume_contractuel * np.sum(self.prix_contractuel - resultat_annuel.cout_marginal)

        return revenu_annuel

    def calcul_cout_annuel(self, actif, annee, resultat_annuel, donnees_entree):
        """
        Calcule le coût du contrat pour l'agence de régulation lorsqu'une unité de la technologie actif en bénéficie
        pour l'année et le résultat de dispatch donnés.

        Paramètres
        ----------
        actif : DonneesEntree.Actif
            type d'actif pour lequel on veut connaître le revenu unitaire
        annee : int
            année dont on veut connaître le revenu
        resultat_annuel : DispatchV0.ResultatAnnuel
            résultat de dispatch à utiliser, il devrait correspondre à l'ambiance et à l'année données
        donnees_entree : DonneesEntree.DonneesEntree
            données d'entrée à utiliser

        Retours
        -------
        float
            coût du contrat
        """
        if not(self.annee_debut <= annee < self.annee_fin):
            return 0

        cout_annuel = self.volume_contractuel * np.sum(self.prix_contractuel - resultat_annuel.cout_marginal)

        return cout_annuel
    
    @classmethod
    def calcul_prix_annulation_VAN(cls, actif, matrice_resultats_annuels, annee_debut_resultats, donnees_entree, donnees_simulation):
        """
        Calcule la valeur du prix contractuel qui annule la VAN équivalente d'une unité de l'actif sous un contrat pour
        différence.

        La VAN équivalente d'une unité ayant un contrat pour différence peut s'exprimer comme fonction affine du prix
        contractuel. Il est donc possible, sous certaines hypothèses, de déterminer un prix contractuel qui annule la
        VAN équivalente, c'est ce que calcule cette méthode. Il s'agit d'une méthode de classe qui devrait être appelée
        avant la création d'une instance de ContratParfait.

        Paramètres
        ----------
        actif : DonneesEntree.Actif
            type d'actif pour lequel on veut connaître le prix d'annilation de la VAN
        matrice_resultats_annuels : list
            matrice indexée par [ambiance][annee][meteo] contenant des résultats de dispatchs supposés couvrir les
            premières années de fonctionnement d'une unité et servant à estimer les revenus
        annee_debut_resultats : int
            année à laquelle commencent les résultats de matrice_resultats_annuels
        donnees_entree : DonneesEntree.DonneesEntree
            données d'entrée à utiliser
        donnees_simulation : DonneesSimulation.DonneesSimulation
            données de simulation à utiliser

        Retours
        -------
        float
            prix contractuel annulant la VAN équivalente
        """
        
        df_param_ao = donnees_entree.df_param_ao
        df_param_cfd = donnees_entree.df_param_cfd

        if  df_param_cfd.at[actif.cle,"Type_Contrat"] == "fixe" :
            
            volume_contractuel = df_param_cfd.at[actif.cle,"volume_contractuel"]
            
            if not(volume_contractuel > 0):
                # cas où le volume contractuel n'a pas de sens
                return 0

        # on suppose que l'année de début des résultats est la première année de fonctionnement de l'unité
                
        
        annee_courante = donnees_simulation.annee_courante
        taux_actualisation = actif.taux_actualisation
        facteur_amo = (1 / (1 + taux_actualisation))
        cout_fixe_construction = actif.cout_fixe_construction(annee_courante)
        fom = actif.cout_fixe_maintenance
        duree_construction = actif.duree_construction
        duree_vie = actif.duree_vie
        duree_contrat = np.min([df_param_cfd.at[actif.cle,"duree"], duree_vie])
        horizon_prevision = donnees_entree.parametres_simulation.horizon_prevision
        horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation
        duree_avant_fonctionnement = annee_debut_resultats - annee_courante
        annuite = IndicateursEconomiques.calcul_investissement_IDC_annualise(actif,annee_courante)

        
        nb_annee_resultats = len(matrice_resultats_annuels[0])

        annee_fin_contrat_theorique = (annee_debut_resultats + duree_contrat).astype(int)
        annee_fin_vie_theorique = annee_debut_resultats + duree_vie
           
        Extrapolation = df_param_cfd.at[actif.cle,"extrapolation"]
        
        if Extrapolation :
        
            annee_fin_calcul_npv = annee_fin_vie_theorique
            annee_fin_contrat = annee_fin_contrat_theorique
            
        else : 
        
            annee_fin_calcul_npv = np.min([annee_fin_vie_theorique,
                                    annee_courante+horizon_prevision,
                                    horizon_simulation]).astype(int)
            
            annee_fin_contrat = np.min([annee_fin_contrat_theorique,
                                    annee_courante+horizon_prevision,
                                    horizon_simulation]).astype(int)

        
        # lists where will be stored weather scenario results (raw + weather-weighted)
        
        list_df_ao_meteo = []
        list_df_ao_meteo_pond = []
        
        for idx_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
            
            df_ao_meteo = pd.DataFrame(index=range(annee_debut_resultats,annee_fin_calcul_npv))
            
            for annee in range(annee_debut_resultats,annee_fin_calcul_npv):
                   
                idxN = annee - annee_debut_resultats
                df_ao_meteo.at[annee,"idx_annee"] = int(idxN)
                df_ao_meteo.at[annee,"facteur_amo"] = facteur_amo**(annee-annee_courante)
                df_ao_meteo.at[annee,"annuite_capex"] = annuite
                df_ao_meteo.at[annee,"fom"] = fom
                       
          
                if annee < annee_debut_resultats + nb_annee_resultats : 
                    dispatch = matrice_resultats_annuels[0][idxN][idx_meteo]
                    df_ao_meteo.at[annee,"extrapolated"] = False
                else : 
                    dispatch = matrice_resultats_annuels[0][-1][idx_meteo]
                    df_ao_meteo.at[annee,"extrapolated"] = True 
                    
                nb_unites = dispatch.compte_unites[actif.cle]         

                prod_unitaire = dispatch.production[actif.cle] / nb_unites
                df_ao_meteo.at[annee,"prod_unitaire"] = prod_unitaire.sum()
                
                prix_capte = (prod_unitaire*dispatch.cout_marginal).sum() / prod_unitaire.sum()
                df_ao_meteo.at[annee,"prix_capte"] = prix_capte

                
                if actif.categorie == "ENR":

                    ecretement_unitaire = dispatch.ecretement[actif.cle] / nb_unites              
                    df_ao_meteo.at[annee,"ecretement_unitaire"] = ecretement_unitaire.sum()
                    df_ao_meteo.at[annee,"productible_unitaire"] = ecretement_unitaire.sum() +  prod_unitaire.sum()

                    df_ao_meteo.at[annee,"revenus_spot_unitaire"] = (prod_unitaire*dispatch.cout_marginal).sum()
                    
                    cout_variable_actif = actif.cout_variable
                    
                    if cout_variable_actif > 0 : 
                        sys.exit("to-do")                
                    
                if actif.categorie == "Stockage":
                
                    charge_unitaire = dispatch.charge[actif.cle] / nb_unites
                    df_ao_meteo.at[annee,"charge_unitaire"] = charge_unitaire.mean()
                    prix_capte_charge = (charge_unitaire*dispatch.cout_marginal).sum() / charge_unitaire.sum()
                    df_ao_meteo.at[annee,"prix_capte_charge"] = prix_capte_charge
                    df_ao_meteo.at[annee,"cout_charge"] = (charge_unitaire*dispatch.cout_marginal).sum()

                    df_ao_meteo.at[annee,"revenus_spot_unitaire"] = (prod_unitaire*dispatch.cout_marginal).sum() - df_ao_meteo.at[annee,"cout_charge"]
                                          
                    
                if annee < annee_fin_contrat :
               
                    
                    type_contrat = df_param_cfd.at[actif.cle,"Type_Contrat"]
                    
                    if type_contrat == "production" :
                    
                        prod_contractuelle = prod_unitaire  

                        rev_vol_contrat = (dispatch.cout_marginal*prod_contractuelle).sum()
                        df_ao_meteo.at[annee,"rev_vol_contrat"] = rev_vol_contrat
                        
                        mismatch = (dispatch.cout_marginal*(prod_contractuelle-prod_unitaire)).sum()
                        df_ao_meteo.at[annee,"mismatch"] = mismatch    

                        
                        volume_contractuel_annuel = prod_contractuelle.sum()            
                         
                                                          
                    elif type_contrat == "productible" :
                    
                        prod_contractuelle = prod_unitaire + ecretement_unitaire

                        rev_vol_contrat = (dispatch.cout_marginal*prod_contractuelle).sum()
                        df_ao_meteo.at[annee,"rev_vol_contrat"] = rev_vol_contrat

                        mismatch = (dispatch.cout_marginal*(prod_contractuelle-prod_unitaire)).sum()
                        df_ao_meteo.at[annee,"mismatch"] = mismatch    
                        
                        volume_contractuel_annuel = prod_contractuelle.sum()    
                        
                    elif type_contrat == "fixe":


                        prod_contractuelle  =[volume_contractuel for h in range(8760)]

                        rev_vol_contrat = volume_contractuel*dispatch.cout_marginal.sum()
                        df_ao_meteo.at[annee,"rev_vol_contrat"] = rev_vol_contrat

                        mismatch = (dispatch.cout_marginal*(prod_contractuelle-prod_unitaire)).sum()
                        df_ao_meteo.at[annee,"mismatch"] = mismatch    
                        
                        volume_contractuel_annuel = 8760 * volume_contractuel   
                            
                    df_ao_meteo.at[annee,"volume_contractuel"] = volume_contractuel_annuel                  
                    df_ao_meteo.at[annee,"contractual_period"] = 1                
                    df_ao_meteo.at[annee,"merchant_tail_period"] = 0                
                                 
                if annee >= annee_fin_contrat :
                                 
                    df_ao_meteo.at[annee,"contractual_period"] = 0            
                    df_ao_meteo.at[annee,"merchant_tail_period"] = 1     

            
            
            list_df_ao_meteo.append(df_ao_meteo.copy())
            
            pond = donnees_entree.df_parametres_ponderation.at[idx_meteo,"value"]
            
            list_df_ao_meteo_pond.append(df_ao_meteo.copy()*pond)


        df_ao = sum(list_df_ao_meteo_pond)
                       

        
        # version 2
        
        
        somme_capex = (df_ao["facteur_amo"]*df_ao["annuite_capex"]).sum()
        somme_fom = (df_ao["facteur_amo"]*df_ao["fom"]).sum()
        
        mismatch = (df_ao["facteur_amo"]*df_ao["contractual_period"]*df_ao["mismatch"]).sum()
        merchant_tail_neutre = (df_ao["facteur_amo"]*df_ao["merchant_tail_period"]*df_ao["revenus_spot_unitaire"]).sum()




        if not donnees_entree.parametres_simulation.risk_aversion_lt : 
            print("pas d'aversion au risque")
            merchant_tail = merchant_tail_neutre
        else : 
            print("aversion au risque")
            alpha = donnees_entree.parametres_simulation.coefficient_risque
            esp_utilite = 1 + (1/(2*alpha))*(np.exp(-2*alpha)-1)
            merchant_tail = -(merchant_tail_neutre/alpha)*np.log(1-esp_utilite)  
            
            print("merchant tail neutre ", merchant_tail_neutre)
            print("merchant tail EC ", merchant_tail)
 



        somme_vol_contrat = (df_ao["facteur_amo"]*df_ao["contractual_period"]*df_ao["volume_contractuel"]).sum()
        
        prix = (somme_capex+somme_fom+mismatch-merchant_tail)/somme_vol_contrat
        
        if actif.categorie == "Stockage":   
            prix += (df_ao["facteur_amo"]*df_ao["cout_charge"]*df_ao["contractual_period"]).sum() / somme_vol_contrat
            
        print("Prix ", prix)
        
        
 
        #### Calcul Cash Flow Contractuel

        for idx_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
        
            df_ao_meteo = list_df_ao_meteo[idx_meteo]
            
            for annee in range(annee_debut_resultats,annee_fin_calcul_npv):

                idxN = annee - annee_debut_resultats
        
                if annee < annee_debut_resultats + nb_annee_resultats : 
                    dispatch = matrice_resultats_annuels[0][idxN][idx_meteo]
                else : 
                    dispatch = matrice_resultats_annuels[0][-1][idx_meteo]

                nb_unites = dispatch.compte_unites[actif.cle]         
                prod_unitaire = dispatch.production[actif.cle] / nb_unites
                
                    
                if annee < annee_fin_contrat :

              
                    if df_param_cfd.at[actif.cle,"Type_Contrat"] == "production" :
                    
                        prod_contractuelle =  prod_unitaire

                    elif df_param_cfd.at[actif.cle,"Type_Contrat"] == "productible" :

                        ecretement_unitaire = dispatch.ecretement[actif.cle] / nb_unites        
                    
                        prod_contractuelle =  prod_unitaire + ecretement_unitaire
                     
                    elif df_param_cfd.at[actif.cle,"Type_Contrat"] == "fixe" :
                    
                        prod_contractuelle = volume_contractuel

                    cash_flow = (( prix - dispatch.cout_marginal)*prod_contractuelle).sum()                                           
                    df_ao_meteo.at[annee,"cash_flow_cfd"] = cash_flow 

            pond = donnees_entree.df_parametres_ponderation.at[idx_meteo,"value"]
            list_df_ao_meteo_pond[idx_meteo] = df_ao_meteo * pond


        df_ao = sum(list_df_ao_meteo_pond)
        
        dossier_sortie = donnees_entree.dossier_sortie 
        folder_df = os.path.join(dossier_sortie,"annee_"+ str(annee_courante),"AO_" + str(annee_debut_resultats))
        
        if not os.path.exists(folder_df):
            os.makedirs(folder_df)
            
        path_df = os.path.join(folder_df,"df_AO_%s.csv"%(actif.cle))
        df_ao.to_csv(path_df,sep=";")
        
        for idx_meteo in range(donnees_entree.parametres_simulation.nb_meteo):
            path_df = os.path.join(folder_df,"df_AO_%s_meteo_%d.csv"%(actif.cle,idx_meteo))
            list_df_ao_meteo[idx_meteo].to_csv(path_df,sep=";")        
        
        return prix