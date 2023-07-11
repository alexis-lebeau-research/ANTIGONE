# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import sys
import os
import pulp
import numpy as np
import pandas as pd
import time
from threading import Thread

from pathlib import Path


class ProblemeDispatchPartiel(pulp.LpProblem):
    """
    Problème de dispatch sur une partie de l'année.

    Cette classe représente un sous-problème de dispatch couvrant une certaine fenêtre horaire de l'année, elle hérite
    de la classe de problème linéaire de pulp.
    Pour calculer un dispatch annuel, on résoudra plusieurs fois ce sous-problème, en changeant des contraintes, afin
    d'avoir un dispatch sur l'ensemble de l'année, qui est quasi-optimal dans le cas général.

    Attributs
    ---------
    nombre_heures : int
        nombre d'heures que couvre le problème
    puissance_produite : dict
        dictionnaire stockant, pour chaque type d'actif, les variables de puissances produites à chaque heure
    defaillance : pulp.LpVariable.dict
        dictionnaire contenant les variables des puissances non-fournies à chaque heure
    stock : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, les variables de stock
    puissance_charge : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, les variables de puissance de charge
    puissance_decharge : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, les variables de puissance de décharge
    liste_contraintes_satisfaction_demande : list
        liste les contraintes imposant la satisfactionde la demande à chaque heure
    contraintes_continuite_stock : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, la liste des contraintes imposant la continuité du
        stock d'une heure sur l'autre.

    Méthodes
    --------
    mise_a_jour_second_membre(self, donnees_entree, compte_unites, annee_courante, meteo, annee, heure_debut,
    stock_depart, contraindre_stock = False, heure_contrainte = None, stock_contraint = None)
        Adapte les contraintes du problème à la fenêtre horaire définie par heure_debut. L'intérêt de cette méthode est
        qu'elle permet de calculer plusieurs dispatchs partiels sans avoir besoin de construire de nouvelles instances
        de problèmes linéaires à chaque fois, ce qui serait coûteux en temps de calcul.
    """

    def __init__(self, donnees_entree, compte_unites,  donnees_dispatch, annee,donnees_couts_var,nombre_heures):    
    
    
        super().__init__("Dispatch_partiel", pulp.LpMinimize)
        

        self.nombre_heures = nombre_heures

        # ######### #
        # VARIABLES #
        # ######### #

        # valeurs de la production des actifs hors stockage
        self.puissance_produite = dict()
        for actif in donnees_entree.actifs_pilotables():
            self.puissance_produite[actif.cle] = pulp.LpVariable.dict("puissance_produite_%s" % (actif.cle), range(nombre_heures), lowBound=0, upBound=0, cat="Continuous")
        for actif in donnees_entree.actifs_ENR():
            # borne supérieure initialisée à zéro pour les ENR, elle sera mise à jour selon la météo à chaque étape
            self.puissance_produite[actif.cle] = pulp.LpVariable.dict("puissance_produite_%s" % (actif.cle), range(nombre_heures), lowBound=0, upBound=0, cat="Continuous")

        # valeur de la défaillance, non bornée supérieurement
        self.defaillance = pulp.LpVariable.dict("defaillance", range(nombre_heures), lowBound=0, upBound=None, cat="Continuous")

        # valeurs de stock pour chaque type d'actif de stockage à chaque pas de temps
        # attention au décalage des heures
        self.stock = dict()
        for actif_stockage in donnees_entree.actifs_stockage():
            self.stock[actif_stockage.cle] = pulp.LpVariable.dict("stock_%s" % (actif_stockage.cle), range(1, nombre_heures+1), lowBound=0, upBound=None, cat="Continuous")

        # valeurs de puissances de charge pour chaque type d'actif de stockage à chaque pas de temps
        self.puissance_charge = dict()
        for actif_stockage in donnees_entree.actifs_stockage():
            self.puissance_charge[actif_stockage.cle] = pulp.LpVariable.dict("puissance_charge_%s" % (actif_stockage.cle), range(nombre_heures), lowBound=0, upBound=actif_stockage.puissance_nominale_charge * compte_unites[actif_stockage.cle], cat="Continuous")

        # valeurs de puissances de decharge pour chaque type d'actif de stockage à chaque pas de temps
        self.puissance_decharge = dict()

            
        for actif_stockage in donnees_entree.actifs_stockage():
            self.puissance_decharge[actif_stockage.cle] = pulp.LpVariable.dict("puissance_decharge_%s" % (actif_stockage.cle), range(nombre_heures), lowBound=0, upBound=actif_stockage.puissance_nominale_decharge * compte_unites[actif_stockage.cle], cat="Continuous")        
            
        #### Indicatrices (unités de 1 MW)
        
        
        if donnees_entree.parametres_simulation.indicatrice :
        
            for actif in donnees_entree.actifs_pilotables():  
                self.puissance_produite["indic_"+actif.cle] = pulp.LpVariable.dict("puissance_produite_indic_%s" % (actif.cle), range(nombre_heures), lowBound=0, upBound=1, cat="Continuous")
                
            for actif in donnees_entree.actifs_ENR():
                # borne supérieure initialisée à zéro pour les ENR, elle sera mise à jour selon la météo à chaque étape
                self.puissance_produite["indic_"+actif.cle] = pulp.LpVariable.dict("puissance_produite_indic_%s" % (actif.cle), range(nombre_heures), lowBound=0, upBound=0, cat="Continuous")
     
            for actif_stockage in donnees_entree.actifs_stockage():
                self.stock["indic_"+actif_stockage.cle] = pulp.LpVariable.dict("stock_indic_%s" % (actif_stockage.cle), range(1, nombre_heures+1), lowBound=0, upBound=actif_stockage.duree, cat="Continuous")
     
                self.puissance_charge["indic_"+actif_stockage.cle] = pulp.LpVariable.dict("puissance_charge_indic_%s" % (actif_stockage.cle), range(nombre_heures), lowBound=0, upBound=1, cat="Continuous")
                
                self.puissance_decharge["indic_"+actif_stockage.cle] = pulp.LpVariable.dict("puissance_decharge_indic_%s" % (actif_stockage.cle), range(nombre_heures), lowBound=0, upBound=1, cat="Continuous")
                
    
        # ########### #
        # CONTRAINTES #
        # ########### #

        # contrainte de satisfaction de la demande
        self.liste_contraintes_satisfaction_demande = []
        for heure in range(nombre_heures):
        
            puissance_produite_heure = pulp.lpSum([self.puissance_produite[actif.cle][heure] for actif in donnees_entree.actifs_hors_stockage()])
            puissance_charge_heure = pulp.lpSum([self.puissance_charge[actif.cle][heure] for actif in donnees_entree.actifs_stockage()])
            puissance_decharge_heure = pulp.lpSum([self.puissance_decharge[actif.cle][heure] for actif in donnees_entree.actifs_stockage()])
            
            defaillance_heure = self.defaillance[heure]
            
            
            ### Indicatrices
            if donnees_entree.parametres_simulation.indicatrice :            
                puissance_produite_heure += pulp.lpSum([self.puissance_produite["indic_"+actif.cle][heure] for actif in donnees_entree.actifs_hors_stockage()])
                puissance_charge_heure += pulp.lpSum([self.puissance_charge["indic_"+actif.cle][heure] for actif in donnees_entree.actifs_stockage()])
                puissance_decharge_heure += pulp.lpSum([self.puissance_decharge["indic_"+actif.cle][heure] for actif in donnees_entree.actifs_stockage()])


            ### Ecriture de la contrainte
            
            contrainte = pulp.LpConstraint(
                    e=puissance_produite_heure - puissance_charge_heure + puissance_decharge_heure + defaillance_heure,
                    sense=pulp.LpConstraintEQ,
                    rhs=0,  # second membre initialisé à 0
                    name="satisfaction_demande_%d" % heure
                )
            self.liste_contraintes_satisfaction_demande.append(contrainte)
            self.addConstraint(contrainte)



        # contrainte de continuité du stock
        self.contraintes_continuite_stock = dict()
        for actif_stockage in donnees_entree.actifs_stockage():
            contraintes_continuite_stock_actif = []
            # la contrainte de la première heure est traitée différemment car elle implique le stock de départ
            stock_1 = self.stock[actif_stockage.cle][1]
            puissance_charge_actif_0 = self.puissance_charge[actif_stockage.cle][0]
            puissance_decharge_actif_0 = self.puissance_decharge[actif_stockage.cle][0]
            contrainte = pulp.LpConstraint(
                    e=stock_1 - actif_stockage.rendement_charge * puissance_charge_actif_0 + 1 / actif_stockage.rendement_decharge * puissance_decharge_actif_0,
                    sense=pulp.LpConstraintEQ,
                    rhs=0,  # second membre initialisé à 0 sera mis à jour à chaque étape
                    name="continuite_stock_%s_0"%(actif_stockage.cle)
                )
            contraintes_continuite_stock_actif.append(contrainte)
            self.addConstraint(contrainte)

            # heures restantes
            capacite_installee = actif_stockage.capacite * compte_unites[actif_stockage.cle]
            for heure in range(1, nombre_heures):
                stock_heure = self.stock[actif_stockage.cle][heure]
                stock_heure_suivante = self.stock[actif_stockage.cle][heure+1]
                puissance_charge_actif_heure = self.puissance_charge[actif_stockage.cle][heure]
                puissance_decharge_actif_heure = self.puissance_decharge[actif_stockage.cle][heure]
                contrainte = pulp.LpConstraint(
                    e=stock_heure_suivante - stock_heure - actif_stockage.rendement_charge * puissance_charge_actif_heure + 1/actif_stockage.rendement_decharge * puissance_decharge_actif_heure,
                    sense=pulp.LpConstraintEQ,
                    rhs=0,
                    name="continuite_stock_%s_%d"%(actif_stockage.cle, heure)
                )
                contraintes_continuite_stock_actif.append(contrainte)
                self.addConstraint(contrainte)
            self.contraintes_continuite_stock[actif_stockage.cle] = contraintes_continuite_stock_actif

            
        # contrainte de continuité du stock pour les indicatrices
        if donnees_entree.parametres_simulation.indicatrice :             
            for actif_stockage in donnees_entree.actifs_stockage():
                contraintes_continuite_stock_actif = []
                # la contrainte de la première heure est traitée différemment car elle implique le stock de départ
                stock_1 = self.stock["indic_"+actif_stockage.cle][1]
                puissance_charge_actif_0 = self.puissance_charge["indic_"+actif_stockage.cle][0]
                puissance_decharge_actif_0 = self.puissance_decharge["indic_"+actif_stockage.cle][0]
                
                contrainte = pulp.LpConstraint(
                        e=stock_1 - actif_stockage.rendement_charge * puissance_charge_actif_0 + 1 / actif_stockage.rendement_decharge * puissance_decharge_actif_0,
                        sense=pulp.LpConstraintEQ,
                        rhs=0,  # second membre initialisé à 0 sera mis à jour à chaque étape
                        name="continuite_stock_indic_%s_0"%(actif_stockage.cle)
                    )
                contraintes_continuite_stock_actif.append(contrainte)
                self.addConstraint(contrainte)

                # heures restantes

                for heure in range(1, nombre_heures):
                
                    stock_heure = self.stock["indic_"+actif_stockage.cle][heure]
                    stock_heure_suivante = self.stock["indic_"+actif_stockage.cle][heure+1]
                    puissance_charge_actif_heure = self.puissance_charge["indic_"+actif_stockage.cle][heure]
                    puissance_decharge_actif_heure = self.puissance_decharge["indic_"+actif_stockage.cle][heure]
                    
                    contrainte = pulp.LpConstraint(
                        e=stock_heure_suivante - stock_heure - actif_stockage.rendement_charge * puissance_charge_actif_heure + 1/actif_stockage.rendement_decharge * puissance_decharge_actif_heure,
                        sense=pulp.LpConstraintEQ,
                        rhs=0,
                        name="continuite_stock_indic_%s_%d"%(actif_stockage.cle, heure)
                    )
                    contraintes_continuite_stock_actif.append(contrainte)
                    self.addConstraint(contrainte)
                self.contraintes_continuite_stock["indic_"+actif_stockage.cle] = contraintes_continuite_stock_actif            


        # contrainte stock_max
        self.contraintes_max_stock = dict()
        
        for actif_stockage in donnees_entree.actifs_stockage():
        
            contraintes_max_stock_actif = []
        
            bound = actif_stockage.capacite * compte_unites[actif_stockage.cle]
            
            for heure in range(1,nombre_heures+1):
            
                stock_heure = self.stock[actif_stockage.cle][heure]
                
                contrainte = pulp.LpConstraint(
                    e=stock_heure,
                    sense=pulp.LpConstraintLE,
                    rhs=bound,
                    name="max_energie_stock_%s_%d"%(actif_stockage.cle, heure)
                )

                contraintes_max_stock_actif.append(contrainte)
                self.addConstraint(contrainte)
            
            self.contraintes_max_stock[actif_stockage.cle] = contraintes_max_stock_actif
        
            
        # ################# #
        # FONCTION OBJECTIF #
        # ################# #
        
        
        
        fonction_objectif = pulp.lpSum([donnees_entree.parametres_simulation.plafond_prix * self.defaillance[heure] for heure in range(nombre_heures) ])
        
        for actif_ENR in donnees_entree.actifs_ENR() :
        
            fonction_objectif += pulp.lpSum([actif_ENR.cout_variable * self.puissance_produite[actif_ENR.cle][heure] for heure in range(nombre_heures) ])
            
        for actif_pilotable in donnees_entree.actifs_pilotables() :
       
            combu = actif_pilotable.combustible
            rend = actif_pilotable.rendement
            coef_emi = actif_pilotable.emission_carbone
            
            cout_combu = donnees_couts_var.at[combu,"Annee_%d"%annee ]
            cout_carbone = donnees_couts_var.at["cout_CO2","Annee_%d"%annee ]
            
            cout_var =  ((1/rend)*cout_combu) + (coef_emi*cout_carbone) 


            fonction_objectif += pulp.lpSum([cout_var * self.puissance_produite[actif_pilotable.cle][heure] for heure in range(nombre_heures) ])
            
        for actif_stockage in donnees_entree.actifs_stockage() :
         
            fonction_objectif += pulp.lpSum([actif_stockage.cout_variable * self.puissance_decharge[actif_stockage.cle][heure] for heure in range(nombre_heures)]  )
            
        # ajout des indicatrices

        
        if donnees_entree.parametres_simulation.indicatrice :  
            for actif_ENR in donnees_entree.actifs_ENR() :
            
                fonction_objectif += pulp.lpSum([actif_ENR.cout_variable * self.puissance_produite["indic_"+actif_ENR.cle][heure] for heure in range(nombre_heures) ])
                
            for actif_pilotable in donnees_entree.actifs_pilotables() :
           
                combu = actif_pilotable.combustible
                rend = actif_pilotable.rendement
                coef_emi = actif_pilotable.emission_carbone
                
                cout_combu = donnees_couts_var.at[combu,"Annee_%d"%annee ]
                cout_carbone = donnees_couts_var.at["cout_CO2","Annee_%d"%annee ]
                
                cout_var =  ((1/rend)*cout_combu) + (coef_emi*cout_carbone) 


                fonction_objectif += pulp.lpSum([cout_var * self.puissance_produite["indic_"+actif_pilotable.cle][heure] for heure in range(nombre_heures) ])
                
            for actif_stockage in donnees_entree.actifs_stockage() :
             
                fonction_objectif += pulp.lpSum([actif_stockage.cout_variable * self.puissance_decharge["indic_"+actif_stockage.cle][heure] for heure in range(nombre_heures)]  )

        
        self.setObjective(fonction_objectif)

    def mise_a_jour_second_membre(self, donnees_entree, compte_unites, donnees_dispatch, annee,donnees_couts_var, heure_debut, stock_depart, contraindre_stock = False, heure_contrainte = None, stock_contraint = None):
        """
        Met à jour les contraintes pour les adapter à la fenêtre horaire sur laquelle on veut calculer le prochain
        dispatch partiel.

        Paramètres
        ---------
        heure_debut : int
            première heure de la fenêtre couverte par le problème
        stock_depart : dict
            dictionnaire contenant, pour chaque type d'actif de stockage, la valeur du stock à l'heure heure_debut
        contraindre_stock : bool
            booléen indiquant si la valeur du stock à une heure particulière doit être contrainte
        heure_contrainte : int
            heure à laquelle le stock doit être contraint
        stock_contraint : dict
            dictionnaire contenant, pour chaque type d'actif de stockage, la valeur du stock à imposer
        """

        # mise à jour de la première contraintes de continuité du stock avec le nouveau stock de départ
        for actif_stockage in donnees_entree.actifs_stockage():

            stock_depart_actif = stock_depart[actif_stockage.cle]
            contraintes_continuite_stock_actif_0 = self.contraintes_continuite_stock[actif_stockage.cle][0]
            contraintes_continuite_stock_actif_0.changeRHS(RHS=stock_depart_actif)

            # contrainte sur l'indicatrice
            if donnees_entree.parametres_simulation.indicatrice :             
            
                if compte_unites[actif_stockage.cle] > 0 :
                    taux_remplissage = stock_depart_actif / ( actif_stockage.capacite * compte_unites[actif_stockage.cle] )
                else : 
                    taux_remplissage = 0 
                    
                stock_depart_actif_indicatrice =  taux_remplissage * actif_stockage.duree
                contraintes_continuite_stock_actif_0_indicatrice = self.contraintes_continuite_stock["indic_"+actif_stockage.cle][0]
                contraintes_continuite_stock_actif_0_indicatrice.changeRHS(RHS=stock_depart_actif_indicatrice)
            

        # mise à jour des bornes des puissances produites par les actifs ENR qui dépend de la météo
        for actif_ENR in donnees_entree.actifs_ENR():
            puissance_produite_actif_ENR = self.puissance_produite[actif_ENR.cle]
            nombre_unites_installees = compte_unites[actif_ENR.cle]

            if donnees_entree.parametres_simulation.indicatrice :  
                puissance_produite_actif_ENR_indicatrice = self.puissance_produite["indic_"+actif_ENR.cle]

            for heure in range(self.nombre_heures):
                puissance_disponible = 0
                if heure_debut+heure < 8760:
                    puissance_disponible = nombre_unites_installees * actif_ENR.puissance_reference * donnees_dispatch["fc"].at[ heure_debut + heure,actif_ENR.cle+"_%d"%annee]
                    
                    if donnees_entree.parametres_simulation.indicatrice :  
                        puissance_disponible_indicatrice = donnees_dispatch["fc"].at[ heure_debut + heure,actif_ENR.cle+"_%d"%annee]
                    
                puissance_produite_actif_ENR[heure].bounds(low=0, up=puissance_disponible)
                if donnees_entree.parametres_simulation.indicatrice :  
                    puissance_produite_actif_ENR_indicatrice[heure].bounds(low=0,up=puissance_disponible_indicatrice)
                    
                    
        # mise à jour des pmax pour les pilotables
        
        for actif in donnees_entree.actifs_pilotables():
        
            puissance_produite = self.puissance_produite[actif.cle]
            
            p_inst = actif.puissance_nominale * compte_unites[actif.cle]
            
            for heure in range(self.nombre_heures):

                

                if heure_debut+heure < 8760:
                
                    col = actif.cle+"_%d"%annee
                    if col in donnees_dispatch["dispo"].columns:
                        puissance_disponible = p_inst * donnees_dispatch["dispo"].at[heure_debut+heure,col]
                    else :
                        puissance_disponible = p_inst
                        
                else :
                    puissance_disponible = 0
                    
                puissance_produite[heure].bounds(low=0,up=puissance_disponible)
                
        
        # mise à jour du second membre des contraintes de satisfaction de la demande
        for heure in range(self.nombre_heures):
            demande = 0
            if heure_debut+heure < 8760:
                # si l'heure considérée est comprise dans l'année, on lui attribue la valeur correspondante
                # au delà de la fin de l'année, la demande reste nulle
                demande = donnees_dispatch["demande"].at[ heure_debut + heure,"Annee_%d"%annee]

            self.liste_contraintes_satisfaction_demande[heure].changeRHS(RHS=demande)

        # si une contrainte doit être imposée sur la valeur du stockage pour une des heures de la fenêtre,
        # les bornes du stock sont "reserrées" à la même valeur
        if contraindre_stock:
            for actif_stockage in donnees_entree.actifs_stockage():
                stock_contraint_actif = stock_contraint[actif_stockage.cle]
                self.stock[actif_stockage.cle][heure_contrainte].bounds(low=stock_contraint_actif, up=stock_contraint_actif)

                if donnees_entree.parametres_simulation.indicatrice :  
                    taux_contrainte = stock_contraint_actif / ( actif_stockage.capacite * compte_unites[actif_stockage.cle] )
                    self.stock["indic_"+actif_stockage.cle][heure_contrainte].bounds(low=taux_contrainte * actif_stockage.duree , up=taux_contrainte * actif_stockage.duree)

class ResultatAnnuel:
    """
    Cette classe sythétise les informations résultant d'un calcul de dispatch annuel.

    Attributs
    ---------
    cout_total : float
        somme des valeurs objectif des problèmes de dispatch partiels résolus pour couvrir l'ensemble de l'année
    production : dict
        dictionnaire contenant, pour chaque type d'actif, le tableau horaire de l'énergie produite
    stockage : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, le tableau horaire de l'énergie stockée
    cout_marginal : np.array
        tableau contenant les coûts marginaux horaires
    charge : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, le tableau horaire de l'énergie utilisée pour
        charger les unités de stockage
    decharge : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, le tableau horaire de l'énergie fournie par la
        décharge des unités de stockage
    defaillance : np.array
        tableau contenant la quantité horaire d'énergie non-fournie
    ecretement : dict
        dictionnaire contenant, pour chaque type d'actif renouvelable, la quantité d'énergie productible non-utilisée
    compte_unites : dict
        dictionnaire contenant, pour chaque type d'actif, le nombre d'unités présentes dans le parc au moment du calcul
    ambiance : DonneesEntree.Ambiance
        ambiance pour laquelle le résultat a été calculé
    annee_courante : int
        année courante pour laquelle le résultat a été calculé
    meteo : DonneesEntree.Meteo
        météo pour laquelle le résultat a été calculé
    annee : int
        année pour laquelle le résultat a été calculé
    """

    def __init__(self,donnees_entree, cout_total, production, cout_marginal, stockage, charge, decharge, defaillance, ecretement, compte_unites,donnees_dispatch,donnees_couts_var,annee_courante,annee,variable_duale_stockage,demande):
    
        self.donnees_entree = donnees_entree
        
        self.cout_total = cout_total
        self.production = production
        self.stockage = stockage
        self.cout_marginal = cout_marginal
        self.charge = charge
        self.decharge = decharge
        self.ecretement = ecretement
        self.defaillance = defaillance
        self.demande = demande
        
        self.variable_duale_stockage = variable_duale_stockage

        # mémorisation du nombre d'unités de chaque actif dans le parc à l'année correspondant au resultat
        # utile pour déterminer les valeurs de production, stock, charge ou décharge par unité
        self.compte_unites = compte_unites

        # mémorisation de l'ambiance, année courante, météo et année pour lesquelles le résultat a été calculé

        self.annee_courante = annee_courante
        self.annee = annee
        self.donnees_dispatch = donnees_dispatch
        self.donnees_couts_var = donnees_couts_var
          
        # creation du dataframe
        
        self.build_df_data()
        self.build_df_cv()
        
        
        if donnees_entree.parametres_simulation.filtre_propagation :
            self.filtre_cm()
        
    def production_unitaire(self, cle_actif):
        """
        Renvoie le tableau horaire de l'énergie produite par une unité de l'actif correspondant à
        cle_actif, en supposant que la production est répartie équitablement entre les unités.

        Paramètres
        ----------
        cle_actif : str
            clé de l'actif

        Retours
        -------
        np.array
            tableau de la production horaire d'une unité de l'actif
        """

        nombre_unites = self.compte_unites[cle_actif]
        if(nombre_unites > 0):
            return self.production[cle_actif]/nombre_unites
        # si le nombre d'unités est 0, on renvoie directement le vecteur de production qui devrait être uniformément nul
        return self.production[cle_actif]

    def build_df_data(self):

        data_frame_resultat_annuel = pd.DataFrame(index=range(8760))
        
        data_frame_resultat_annuel["demande"] = self.demande
        data_frame_resultat_annuel["cout_marginal"] = self.cout_marginal
        data_frame_resultat_annuel["defaillance"] = self.defaillance

        for cle_actif, production_actif in self.production.items():
            data_frame_resultat_annuel["production %s"%cle_actif] = production_actif

        for cle_actif, stockage_actif in self.stockage.items():
            data_frame_resultat_annuel["stockage %s"%cle_actif] = stockage_actif
            
        for cle_actif, vd_stockage in self.variable_duale_stockage.items():
            data_frame_resultat_annuel["VU %s"%cle_actif] = vd_stockage

        for cle_actif, charge_actif in self.charge.items():
            data_frame_resultat_annuel["charge %s"%cle_actif] = charge_actif

        for cle_actif, decharge_actif in self.decharge.items():
            data_frame_resultat_annuel["decharge %s"%cle_actif] = decharge_actif

        for cle_actif, ecretement_actif in self.ecretement.items():
            data_frame_resultat_annuel["ecretement %s" % cle_actif] = ecretement_actif

    
        self.data_frame_resultat_annuel = data_frame_resultat_annuel
    
        return None

    
    def build_df_cv(self):

        annee = self.annee
        donnees_entree = self.donnees_entree
        
        df_cv = pd.DataFrame()

        df_cv.at["ecretement","CV"] = 0
               
        df_cv.at["VoLL","CV"] = donnees_entree.parametres_simulation.plafond_prix
        
        for actif_stockage in donnees_entree.actifs_stockage():
        
            cle = actif_stockage.cle
            
            # a voir pour implementer si choix de rendement non symetriques
            
            rendement = actif_stockage.rendement_charge  
            
            df_cv.at["VoLL charge "+cle,"CV"] = donnees_entree.parametres_simulation.plafond_prix * rendement
        
        cv_max = 0
        
        for actif_pilotable in donnees_entree.actifs_pilotables() : 
            cle = actif_pilotable.cle
            
            combu = actif_pilotable.combustible
            rend = actif_pilotable.rendement
            coef_emi = actif_pilotable.emission_carbone
            
            cout_combu = self.donnees_couts_var.at[combu,"Annee_%d"%annee ]
            cout_carbone = self.donnees_couts_var.at["cout_CO2","Annee_%d"%annee ]
            
            cv =  ((1/rend)*cout_combu) + (coef_emi*cout_carbone) 

            df_cv.at[cle,"CV"] = cv
            
            if cv > cv_max :
                cv_max = cv

            for actif_stockage in donnees_entree.actifs_stockage():
            
                cle_stockage = actif_stockage.cle
                
                # a voir pour implementer si choix de rendement non symetriques
                
                rendement = (actif_stockage.rendement_charge*actif_stockage.rendement_decharge)
            
                df_cv.at[cle+" decharge "+cle_stockage,"CV"] = cv / rendement                    
                df_cv.at[cle+" charge "+cle_stockage,"CV"] = cv * rendement                    

                if (cv / rendement) > cv_max :
                    cv_max = cv/ rendement

        for actif_ENR in donnees_entree.actifs_ENR():
            cle = actif_ENR.cle
            df_cv.at[cle,"CV"] = float(actif_ENR.cout_variable)
        for actif_stockage in donnees_entree.actifs_stockage():
            cle = actif_stockage.cle
            df_cv.at[cle,"CV"] = float(actif_stockage.cout_variable)        
            
        df_cv["CV_round"] = df_cv.round(decimals=2)
        
        self.df_cv = df_cv
        self.cv_max = cv_max
        
        
        return None
        
    def filtre_cm(self):
        
        annee = self.annee
        donnees_entree = self.donnees_entree
       
        df_cv = self.df_cv
        df_dispatch = self.data_frame_resultat_annuel
        
        # on travaille avec des cm arrondis à 2 decimales
        
        df_dispatch["cm_round"] = df_dispatch["cout_marginal"].round(decimals=2)
        df_dispatch["cm_filtre"] = df_dispatch["cout_marginal"].round(decimals=2)
        
        
        cv_max = self.cv_max
        

        # on détecte tous les évènements

        cond_1 = df_dispatch["cm_round"] > cv_max
        
        df_pics_prix =  df_dispatch[cond_1]
               
        list_of_df = np.split(df_pics_prix, np.flatnonzero(np.diff(df_pics_prix.index) != 1) + 1)
        
        
        for df_tmp in list_of_df : 
            
            cond_2 = df_tmp["defaillance"] == 0.0
            
            for idx in df_tmp[cond_2].index:
                
                df_dispatch.at[idx,"cm_filtre"] = cv_max
                
        
        self.cout_marginal_brute = self.cout_marginal
        self.cout_marginal = df_dispatch["cm_filtre"].values
        
        
        return None
        
def DispatchAnnuel(donnees_entree, compte_unites, donnees_dispatch, donnees_couts_var,annee_courante,annee,writeLP ,LP_name):
    """
    Calcule le dispatch annuel et renvoie le résultat annuel correspondant.

    Paramètres
    ----------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser pour le dispatch
    compte_unites : dict
        dictionnaire indiquant, pour chaque type d'actif, le nombre d'unités présentes dans le parc
    donnees_dispatch : dico contenant les données (cout combustibles, demande, facteurs de charge)

    annee : int
        année pour laquelle on calcule le dispatch, peut être postérieure à annee_courante dans le cas d'une anticpation

    Retours
    -------
    ResultatAnnuel
        résultat de dispatch annuel
    """


    fenetre_optimisation = donnees_entree.parametres_optimisation.fenetre_optimisation
    vision_supplementaire = donnees_entree.parametres_optimisation.vision_supplementaire
    nombre_optimisations_partielles = 8760//fenetre_optimisation

    # structures dans lesquelles seront stockés les résultats de l'optimisation pour revoyer un résultat annuel
    cout_total = 0
    production = dict()
    for actif in donnees_entree.tous_actifs():
        production[actif.cle] = np.zeros(8760)
        if donnees_entree.parametres_simulation.indicatrice :  
            production["indic_"+actif.cle] = np.zeros(8760)
        
    cout_marginal = np.zeros(8760)
    defaillance = np.zeros(8760)
    ecretement = dict()
    stockage = dict()
    charge = dict()
    decharge = dict()
    variable_duale_stockage = {}
    demande = donnees_dispatch["demande"]["Annee_%d"%annee]
    
    for actif_stockage in donnees_entree.actifs_stockage():
        # initialisation des valeurs du stockage à zéro sauf pour la première heure de l'année où le stockage est imposé
        # par les données d'entrée
        # ce tableau sera mis à jour et utilisé à chaque étape pour garantir la continuité du stock entre les fenêtres

        stockage[actif_stockage.cle] = np.zeros(8760)
        charge[actif_stockage.cle] = np.zeros(8760)
        decharge[actif_stockage.cle] = np.zeros(8760)

        if donnees_entree.parametres_simulation.indicatrice :  
            stockage["indic_"+actif_stockage.cle] = np.zeros(8760)
            charge["indic_"+actif_stockage.cle] = np.zeros(8760)
            decharge["indic_"+actif_stockage.cle] = np.zeros(8760)
        
        variable_duale_stockage[actif_stockage.cle] = np.zeros(8760)
        
    for actif_ENR in donnees_entree.actifs_ENR():
        # initialisation des valeurs de l'écrêtement pour les énergies renouvelables
        ecretement[actif_ENR.cle] = np.zeros(8760)

    # initialisation de l'instance de problème d'optimisation qui sera mise à jour et réutilisée à chaque étape
    # (la création de problème et l'ajout de contraintes étant couteux en temps, réutiliser la même instance
    # en changeant le second membre est avantageux)
    probleme_dispatch_partiel = ProblemeDispatchPartiel(donnees_entree, compte_unites,  donnees_dispatch, annee,donnees_couts_var, fenetre_optimisation + vision_supplementaire)

    # variable utilisée pour assurer la continuité de la quantité d'énergie stockée d'une fenêtre à l'autre
    stock_depart = dict()
    # variable utilisée à la dernière étape pour contraindre la valeure du stock final
    stock_final = dict()
    for actif_stockage in donnees_entree.actifs_stockage():
        capacite_installee = actif_stockage.capacite * compte_unites[actif_stockage.cle]
        stock_depart[actif_stockage.cle] = actif_stockage.stock_initial * capacite_installee
        stock_final[actif_stockage.cle] = actif_stockage.stock_initial * capacite_installee
        
    dossier_sortie = donnees_entree.dossier_sortie 
    


        
    for etape in range(nombre_optimisations_partielles):
    
        heure_debut = max(etape * fenetre_optimisation, 0)
        heure_fin = min(heure_debut + fenetre_optimisation + vision_supplementaire, 8760)

        # mise à jour du second membre du problème avant résolution
        # contrainte de l'état de stock final si l'étape en cours est la dernière
        if(etape == nombre_optimisations_partielles - 1):
            probleme_dispatch_partiel.mise_a_jour_second_membre(donnees_entree, compte_unites,donnees_dispatch, annee,donnees_couts_var, etape*fenetre_optimisation, stock_depart, contraindre_stock=True, heure_contrainte=fenetre_optimisation, stock_contraint=stock_final)
        else:
            probleme_dispatch_partiel.mise_a_jour_second_membre(donnees_entree, compte_unites, donnees_dispatch, annee,donnees_couts_var, etape*fenetre_optimisation, stock_depart)

        # résolution

       
        
        if donnees_entree.parametres_simulation.solver == "cplex" : 
            solver = pulp.CPLEX_CMD(path=donnees_entree.parametres_simulation.solver_path)
       
        if donnees_entree.parametres_simulation.solver == "glpk" : 
            solver = pulp.GLPK_CMD(path=donnees_entree.parametres_simulation.solver_path,msg=0)       

    
        probleme_dispatch_partiel.solve(solver)


 
        #print("status : ", pulp.LpStatus[probleme_dispatch_partiel.status])
        
        if not (probleme_dispatch_partiel.status == 1) :
            print("Pas faisable")
            print("annee ",annee)
            print("etape ",etape)
            print("annee courante",annee_courante)
            
            if writeLP : 
            
                folder_path = os.path.join(dossier_sortie,"LP","annee_courante_%d"%annee_courante,"annee_%d"%annee)
                Path(folder_path).mkdir(parents=True, exist_ok=True)
                path_LP = os.path.join(folder_path,"%s_%s.lp"%(LP_name,str(etape)))       
                probleme_dispatch_partiel.writeLP(path_LP)

            
            sys.exit()
        
        
        # ajout de la valeur objectif au cout total
        cout_total += pulp.value(probleme_dispatch_partiel.objective)

        # enregistrement de la production des actifs hors stockage
        for actif in donnees_entree.actifs_hors_stockage():
            production_actif = production[actif.cle]
            variables_puissance_produite_actif = probleme_dispatch_partiel.puissance_produite[actif.cle]
            for heure in range(heure_debut, heure_fin):
                heure_etape = heure - heure_debut
                production_actif[heure] = variables_puissance_produite_actif[heure_etape].value()
                if donnees_entree.parametres_simulation.indicatrice :  
                    production["indic_"+actif.cle][heure] = probleme_dispatch_partiel.puissance_produite["indic_"+actif.cle][heure_etape].value()
        
        # enregistrement des valeurs du stockage, charge et décharge des actifs de stockage
        for actif_stockage in donnees_entree.actifs_stockage():
            stockage_actif = stockage[actif_stockage.cle]
            production_actif = production[actif_stockage.cle]
            charge_actif = charge[actif_stockage.cle]
            decharge_actif = decharge[actif_stockage.cle]
            variables_puissance_charge_actif = probleme_dispatch_partiel.puissance_charge[actif_stockage.cle]
            variables_puissance_decharge_actif = probleme_dispatch_partiel.puissance_decharge[actif_stockage.cle]
            variables_stock_actif = probleme_dispatch_partiel.stock[actif_stockage.cle]
            for heure in range(heure_debut, heure_fin):
                heure_etape = heure-heure_debut
                if(heure + 1 < 8760):
                    stockage_actif[heure + 1] = variables_stock_actif[heure_etape+1].value()
                    variable_duale_stockage[actif_stockage.cle][heure+1] =  probleme_dispatch_partiel.contraintes_max_stock[actif_stockage.cle][heure_etape].pi
                    
                production_actif[heure] = variables_puissance_decharge_actif[heure_etape].value()
                charge_actif[heure] = variables_puissance_charge_actif[heure_etape].value()
                decharge_actif[heure] = variables_puissance_decharge_actif[heure_etape].value()
                
          
                # indicatrices
                if donnees_entree.parametres_simulation.indicatrice :  
                    production["indic_"+actif_stockage.cle][heure] = probleme_dispatch_partiel.puissance_decharge["indic_"+actif_stockage.cle][heure_etape].value()
                    decharge["indic_"+actif_stockage.cle][heure] = probleme_dispatch_partiel.puissance_decharge["indic_"+actif_stockage.cle][heure_etape].value()
                    charge["indic_"+actif_stockage.cle][heure] = probleme_dispatch_partiel.puissance_charge["indic_"+actif_stockage.cle][heure_etape].value()
                
        # enregistrement des coûts marginaux d'après les variables duales de la contrainte de satisfaction de la demande
        for heure in range(heure_debut, heure_fin):
            heure_etape = heure - heure_debut
            cout_marginal[heure] = probleme_dispatch_partiel.liste_contraintes_satisfaction_demande[heure_etape].pi

        # enregistrement de la défaillance
        for heure in range(heure_debut, heure_fin):
            heure_etape = heure - heure_debut
            defaillance[heure] = probleme_dispatch_partiel.defaillance[heure_etape].value()

        # enregistrement des valeurs de l'écrêtement
        for actif_ENR in donnees_entree.actifs_ENR():
            puissance_produite_actif = probleme_dispatch_partiel.puissance_produite[actif_ENR.cle]
            ecretement_actif = ecretement[actif_ENR.cle]
            for heure in range(heure_debut, heure_fin):
                heure_etape = heure - heure_debut
                puissance_produite_actif_heure = puissance_produite_actif[heure_etape]
                ecretement_actif[heure] = puissance_produite_actif_heure.getUb() - puissance_produite_actif_heure.value()

        # mise à jour de la variable de stock de départ pour l'étape suivante
        if (heure_debut + fenetre_optimisation < 8760):
            for actif_stockage in donnees_entree.actifs_stockage():
                stock_depart[actif_stockage.cle] = stockage[actif_stockage.cle][heure_debut + fenetre_optimisation]
    


    
    resultat_annuel = ResultatAnnuel(donnees_entree,cout_total, production, cout_marginal, stockage, charge, decharge, defaillance, ecretement, compte_unites, donnees_dispatch,donnees_couts_var,annee_courante,annee,variable_duale_stockage,demande)
    
    
    return resultat_annuel



class ThreadDispatchAnnuel(Thread):
    """
    Cette classe est un thread consacré au calcul d'un dispatch annuel qui hérite de la classe Thread.

    Attributs
    ---------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser pour le dispatch
    compte_unites : dict
        dictionnaire indiquant, pour chaque type d'actif, le nombre d'unités présentes dans le parc
    ambiance : DonneesEntree.Ambiance
        ambiance à utiliser pour le calcul de dispatch
    annee_courante : int
        année à laquelle est calculé le dispatch
    meteo : DonneesEntree.Meteo
        meteo à utiliser pour le dispatch
    annee : int
        année pour laquelle on calcule le dispatch, peut être postérieure à annee_courante dans le cas d'une anticpation
    resultat_annuel : ResultatAnnuel
        résultat du dispatch, l'attribut est initialisé à None et est effectivement calculé lorsque la méthode run() est
        appelée

    Méthodes
    --------
    run(self) :
        Réimplémentation de la méthode run() nécessaire pour les classes héritant de Tread, cette méthode n'est pas
        supposée être appelée directement par l'utilisateur.
    """

    def __init__(self, donnees_entree, compte_unites, donnees_dispatch,donnees_couts_var,annee_courante,annee_anticipee,writeLP=False,LP_name="LP"):
        Thread.__init__(self)
        
        self.donnees_entree = donnees_entree
        self.compte_unites = compte_unites
        self.donnees_dispatch = donnees_dispatch
        self.donnees_couts_var = donnees_couts_var
        self.annee_courante = annee_courante
        self.annee = annee_anticipee
       
        self.resultat_annuel = None
        self.writeLP = writeLP
        self.LP_name = LP_name

    def run(self):
        """
        Réimplémentation de la méthode run() de la classe Tread. Cette méthode effectue le calcul du dispatch
        correspondant aux attributs donnees_entree, compte_unites, ambiance, annee_courante, meteo et annee avec la
        fonction DispatchAnnuel() et place le résultat dans l'attribut resultat_annuel.
        """

        self.resultat_annuel = DispatchAnnuel(self.donnees_entree, self.compte_unites, self.donnees_dispatch, self.donnees_couts_var,self.annee_courante, self.annee,self.writeLP ,self.LP_name)
