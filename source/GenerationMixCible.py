# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import sys
import os

import pulp
import numpy as np

import IndicateursEconomiques


class ContrainteTrajectoire:
    def __init__(self, nom, liste_actifs_concernes, type_contrainte, grandeur_concernee, tableau_valeurs_second_membre):
        self.nom = nom
        self.liste_actifs_concernes = liste_actifs_concernes
        self.type_contrainte = type_contrainte
        self.grandeur_concernee = grandeur_concernee
        self.tableau_valeurs_second_membre = tableau_valeurs_second_membre


class ProblemeGenerationMixCible(pulp.LpProblem):
    """
    Problème de génération de mix cible.

    Cette classe représente un problème d'optimisation calculant un mix cible qui minimise les coûts en partant d'un
    certain parc initial et en fixant la trajectoire de certains actifs, elle hérite de la classe de problème linéaire
    de pulp.


    Attributs
    ---------
    nombre_unites : dict
        dictionnaire contenant, pour chaque actif et pour chaque année, les variables de nombre d'unités présentes dans
        le parc
    nombre_unites_ouvertes : dict
        dictionnaire contenant, pour chaque actif et pour chaque année, les variables de nombre d'unités ouvertes
    nombre_unites_fermees : dict
        dictionnaire contenant, pour chaque actif et pour chaque année, les variables de nombre d'unités fermées
    production : dict
        dictionnaire contenant, pour chaque type d'actif, les variables de quantité d'énergie produite pour chaque
        année, pour chaque météo et à chaque heure
    defaillance : pulp.LpVariable.dict
        dictionnaire contenant les variables des puissances non-fournies pour chaque année, pour chaque météo et à
        chaque heure
    stock : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, les variables de stock
    puissance_charge : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, les variables de puissance de charge
    puissance_decharge : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, les variables de puissance de décharge
    dict_contraintes_personnalisees : dict
        dictionnaire contenant les contraintes personnalisées imposées par l'utilisateur
    cout_production : pulp.LpAffineExpression
        expression du coût de production en fonction des variables du problème
    cout_defaillance : pulp.LpAffineExpression
        expression du coût de défaillance en fonction des variables du problème
    cout_maintenance : pulp.LpAffineExpression
        expression du coût de maintenance en fonction des variables du problème
    cout_construction : pulp.LpAffineExpression
        expression du coût de construction en fonction des variables du problème
    cout_total : pulp.LpAffineExpression
        expression du coût total en fonction des variables du problème
    """

    def __init__(self, donnees_entree, donnees_simulation, liste_contraintes_trajectoire, type_optim, df_co2_quota,taux_actualisation = 0):

        super().__init__("Generation_mix_cible", pulp.LpMinimize)

        #nombre_annees = donnees_entree.parametres_simulation.horizon_simulation + donnees_entree.parametres_simulation.horizon_prevision
        nombre_annees = donnees_entree.parametres_simulation.horizon_simulation # AL

        parc_initial = dict()
        for actif in donnees_entree.tous_actifs():
            parc_initial[actif.cle] = donnees_simulation.parc.nombre_unites(actif.cle, 0)

        # ######### #
        # VARIABLES #
        # ######### #

        # initialisation des variables de nombre d'unités
        self.nombre_unites = dict()
        
        
        if type_optim == "LP":
        
            for actif in donnees_entree.tous_actifs():
                self.nombre_unites[actif.cle] = pulp.LpVariable.dict("nombre_unites_%s" % (actif.cle), range(nombre_annees), lowBound=0, cat="Continuous")

            # initialisation des variables de nombres d'unités construites et démantelées
            self.nombre_unites_ouvertes = dict()
            self.nombre_unites_fermees = dict()

            for actif in donnees_entree.tous_actifs():
                limite_construction_annuelle = None
                if not(actif.limite_construction_annuelle == 'aucune'):
                    limite_construction_annuelle = actif.limite_construction_annuelle

                self.nombre_unites_ouvertes[actif.cle] = pulp.LpVariable.dict("nombre_unites_ouvertes_%s" % (actif.cle), range(nombre_annees), lowBound=0, upBound=limite_construction_annuelle, cat="Continuous")
                self.nombre_unites_fermees[actif.cle] = pulp.LpVariable.dict("nombre_unites_fermees_%s" % (actif.cle), range(nombre_annees), lowBound=0, cat="Continuous")
            
            # initialisation des variables de nombre d'unités et de nombre d'unités fermées parmi celles dont l'ouvertures
            # est contrainte
            self.nombre_unites_ouverture_forcee_fermees = dict()
            self.nombre_unites_ouverture_forcee = dict()
            for actif in donnees_entree.tous_actifs():
                self.nombre_unites_ouverture_forcee_fermees[actif.cle] = pulp.LpVariable.dict("nombre_unites_ouverture_forcee_fermees_%s" % (actif.cle), range(nombre_annees), lowBound=0, cat="Continuous")
                self.nombre_unites_ouverture_forcee[actif.cle] = pulp.LpVariable.dict("nombre_unites_ouverture_forcee_%s" % (actif.cle), range(nombre_annees), lowBound=0, cat="Continuous")

        if type_optim == "MIP":
        
            for actif in donnees_entree.tous_actifs():
                self.nombre_unites[actif.cle] = pulp.LpVariable.dict("nombre_unites_%s" % (actif.cle), range(nombre_annees), lowBound=0, cat="Integer")

            # initialisation des variables de nombres d'unités construites et démantelées
            self.nombre_unites_ouvertes = dict()
            self.nombre_unites_fermees = dict()

            for actif in donnees_entree.tous_actifs():
                limite_construction_annuelle = None
                if not(actif.limite_construction_annuelle == 'aucune'):
                    limite_construction_annuelle = actif.limite_construction_annuelle

                self.nombre_unites_ouvertes[actif.cle] = pulp.LpVariable.dict("nombre_unites_ouvertes_%s" % (actif.cle), range(nombre_annees), lowBound=0, upBound=limite_construction_annuelle, cat="Integer")
                self.nombre_unites_fermees[actif.cle] = pulp.LpVariable.dict("nombre_unites_fermees_%s" % (actif.cle), range(nombre_annees), lowBound=0, cat="Integer")
            
            # initialisation des variables de nombre d'unités et de nombre d'unités fermées parmi celles dont l'ouvertures
            # est contrainte
            self.nombre_unites_ouverture_forcee_fermees = dict()
            self.nombre_unites_ouverture_forcee = dict()
            for actif in donnees_entree.tous_actifs():
                self.nombre_unites_ouverture_forcee_fermees[actif.cle] = pulp.LpVariable.dict("nombre_unites_ouverture_forcee_fermees_%s" % (actif.cle), range(nombre_annees), lowBound=0, cat="Integer")
                self.nombre_unites_ouverture_forcee[actif.cle] = pulp.LpVariable.dict("nombre_unites_ouverture_forcee_%s" % (actif.cle), range(nombre_annees), lowBound=0, cat="Integer")
        
                   
        
        # initialisation des variables de production des actifs hors stockage
        self.production = dict()
        for actif_hors_stockage in donnees_entree.actifs_hors_stockage():
            production_actif = []
            for annee in range(nombre_annees):
                production_actif_annee = []
                donnees_annuelles = donnees_entree.ambiance_realisee[annee]
                for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                    production_actif_annee_meteo = pulp.LpVariable.dict("production_%s_annee_%d_meteo_%d" % (actif_hors_stockage.cle, annee, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                    production_actif_annee.append(production_actif_annee_meteo)
                production_actif.append(production_actif_annee)
            self.production[actif_hors_stockage.cle] = production_actif

        # initialisation des variables de stock, puissance de charge et puissance de décharge des actifs de stockage
        self.stock = dict()
        self.puissance_charge = dict()
        self.puissance_decharge = dict()
        for actif_stockage in donnees_entree.actifs_stockage():
            stock_actif = []
            puissance_charge_actif = []
            puissance_decharge_actif = []
            for annee in range(nombre_annees):
                stock_actif_annee = []
                puissance_charge_actif_annee = []
                puissance_decharge_actif_annee = []
                donnees_annuelles = donnees_entree.ambiance_realisee[annee]
                for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                    stock_actif_annee_meteo = pulp.LpVariable.dict("stock_%s_annee_%d_meteo_%d" % (actif_stockage.cle, annee, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                    puissance_charge_actif_annee_meteo = pulp.LpVariable.dict("puissance_charge_%s_annee_%d_meteo_%d" % (actif_stockage.cle, annee, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                    puissance_decharge_actif_annee_meteo = pulp.LpVariable.dict("puissance_decharge_%s_annee_%d_meteo_%d" % (actif_stockage.cle, annee, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                    stock_actif_annee.append(stock_actif_annee_meteo)
                    puissance_charge_actif_annee.append(puissance_charge_actif_annee_meteo)
                    puissance_decharge_actif_annee.append(puissance_decharge_actif_annee_meteo)
                stock_actif.append(stock_actif_annee)
                puissance_charge_actif.append(puissance_charge_actif_annee)
                puissance_decharge_actif.append(puissance_decharge_actif_annee)
            self.stock[actif_stockage.cle] = stock_actif
            self.puissance_charge[actif_stockage.cle] = puissance_charge_actif
            self.puissance_decharge[actif_stockage.cle] = puissance_decharge_actif

        # initialisation des variables de défaillance
        self.defaillance = []
        for annee in range(nombre_annees):
            defaillance_annee = []
            donnees_annuelles = donnees_entree.ambiance_realisee[annee]
            for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                defaillance_annee_meteo = pulp.LpVariable.dict("defaillance_annee_%d_meteo_%d" % (annee, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                defaillance_annee.append(defaillance_annee_meteo)
            self.defaillance.append(defaillance_annee)

        # ########### #
        # CONTRAINTES #
        # ########### #

        # contraintes d'évolution du nombre d'unités
        for actif in donnees_entree.tous_actifs():
            nombre_unites_actif = self.nombre_unites[actif.cle]
            nombre_unites_ouvertes_actif = self.nombre_unites_ouvertes[actif.cle]
            nombre_unites_fermees_actif = self.nombre_unites_fermees[actif.cle]
            for annee in range(nombre_annees):
                if annee == 0:
                    # à l'année 0, les unités du parc initial sont ajoutées
                    contrainte = pulp.LpConstraint(
                        e=nombre_unites_actif[annee] - nombre_unites_ouvertes_actif[annee] + nombre_unites_fermees_actif[annee],
                        sense=pulp.LpConstraintEQ,
                        rhs=parc_initial[actif.cle],
                        name="evolution_nombre_unites_%s_%d" % (actif.cle, annee)
                    )
                    self.addConstraint(contrainte)

                else:
                    contrainte = pulp.LpConstraint(
                        e=nombre_unites_actif[annee] - nombre_unites_actif[annee - 1] - nombre_unites_ouvertes_actif[annee] + nombre_unites_fermees_actif[annee],
                        sense=pulp.LpConstraintEQ,
                        rhs=0,
                        name="evolution_nombre_unites_%s_%d" % (actif.cle, annee)
                    )
                    self.addConstraint(contrainte)

        # contraintes de trajectoire CO2
        
        self.liste_contrainte_CO2 = {}
        
        for annee in range(nombre_annees):

            quota = df_co2_quota.at["Annee_"+str(annee),"CO2_quota"]
            
            if quota < np.inf :
            
                print("ecriture des contraintes quota CO2")
                     
                for indice_meteo in range(donnees_annuelles.nombre_meteos()):

                    somme_emissions = pulp.lpSum([self.production[actif.cle][annee][indice_meteo][heure]*actif.emission_carbone for actif in donnees_entree.actifs_pilotables() for heure in range(8760) ])
                    
                    contrainte = pulp.LpConstraint(
                        e=somme_emissions,
                        sense=pulp.LpConstraintLE,
                        rhs=quota,
                        name="contrainte_co2_annee_%s_meteo_%s" % (str(annee),str(indice_meteo))
                        )
                    
                    self.addConstraint(contrainte)
                    self.liste_contrainte_CO2[annee] = contrainte

            else :
                print("pas d'ecriture de contraintes quota CO2")
                    
        # contraintes de trajectoire imposées par l'utilisateur
        self.dict_contraintes_personnalisees = dict()
        for contrainte_trajectoire in liste_contraintes_trajectoire:

            liste_contraintes_personnalisees_annuelles = []

            sens_contrainte = None
            nom_contrainte_trajectoire = contrainte_trajectoire.nom

            if contrainte_trajectoire.type_contrainte == "egalite":
                sens_contrainte = pulp.LpConstraintEQ
            elif contrainte_trajectoire.type_contrainte == "borne_inferieure":
                sens_contrainte = pulp.LpConstraintGE
            elif contrainte_trajectoire.type_contrainte == "borne_superieure":
                sens_contrainte = pulp.LpConstraintLE

            for annee in range(nombre_annees):
                variables_nombre_unites_et_facteurs = []
                donnees_annuelles = donnees_entree.ambiance_realisee[annee]
                for actif in contrainte_trajectoire.liste_actifs_concernes:
                    nombre_unites_actif_annee = self.nombre_unites[actif.cle][annee]

                    facteur = actif.puissance
                    if contrainte_trajectoire.grandeur_concernee == "energie_productible":
                        if actif.categorie == "ENR":
                            liste_energies_productibles = []
                            for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                                meteo = donnees_annuelles[indice_meteo]
                                liste_energies_productibles.append(actif.puissance * np.sum(meteo.facteurs_production_ENR(actif.cle)))
                            facteur = sum(liste_energies_productibles)/len(liste_energies_productibles)
                        else:
                            facteur = 8760 * actif.puissance
                            
                    if contrainte_trajectoire.grandeur_concernee == "nb_unit":
                        facteur = 1 

                    variables_nombre_unites_et_facteurs.append((nombre_unites_actif_annee, facteur))

                second_membre = contrainte_trajectoire.tableau_valeurs_second_membre[annee]
                
                if contrainte_trajectoire.grandeur_concernee == "energie_productible":
                    liste_demandes = []
                    for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                        meteo = donnees_annuelles[indice_meteo]
                        liste_demandes.append(np.sum(meteo.demande_annuelle(0)))
                    second_membre = sum(liste_demandes) / len(liste_demandes) * contrainte_trajectoire.tableau_valeurs_second_membre[annee] / 100

                contrainte = pulp.LpConstraint(
                    e=pulp.lpSum([facteur*nombre_unites for nombre_unites, facteur in variables_nombre_unites_et_facteurs]),
                    sense=sens_contrainte,
                    rhs=second_membre,
                    name="contrainte_trajectoire_%s_annee_%d" % (nom_contrainte_trajectoire, annee)
                )
                self.addConstraint(contrainte)
                liste_contraintes_personnalisees_annuelles.append(contrainte)
            self.dict_contraintes_personnalisees[nom_contrainte_trajectoire] = liste_contraintes_personnalisees_annuelles

        # contraintes de satisfaction de la demande
        self.contraintes_satisfaction_demande = []
        for annee in range(nombre_annees):
            contraintes_satisfaction_demande_annee = []
            donnees_annuelles = donnees_entree.ambiance_realisee[annee]
            for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                contraintes_satisfaction_demande_annee_meteo = []
                meteo = donnees_annuelles[indice_meteo]
                for heure in range(8760):
                    somme_productions = pulp.lpSum([production_actif[annee][indice_meteo][heure] for cle_actif, production_actif in self.production.items()])
                    somme_puissances_charge = pulp.lpSum([puissance_charge_actif[annee][indice_meteo][heure] for cle_actif, puissance_charge_actif in self.puissance_charge.items()])
                    somme_puissances_decharge = pulp.lpSum([puissance_decharge_actif[annee][indice_meteo][heure] for cle_actif, puissance_decharge_actif in self.puissance_decharge.items()])
                    demande = meteo.demande(0, heure)
                    defaillance = self.defaillance[annee][indice_meteo][heure]
                    contrainte = pulp.LpConstraint(
                        e=somme_productions - somme_puissances_charge + somme_puissances_decharge + defaillance,
                        sense=pulp.LpConstraintEQ,
                        rhs=demande,
                        name="satisfaction_demande_annee_%d_meteo_%d_heure_%d" % (annee, indice_meteo, heure)
                    )
                    self.addConstraint(contrainte)
                    contraintes_satisfaction_demande_annee_meteo.append(contrainte)
                contraintes_satisfaction_demande_annee.append(contraintes_satisfaction_demande_annee_meteo)
            self.contraintes_satisfaction_demande.append(contraintes_satisfaction_demande_annee)

        # contraintes de continuité du stock
        for actif_stockage in donnees_entree.actifs_stockage():
            stock_actif = self.stock[actif_stockage.cle]
            puissance_decharge_actif = self.puissance_decharge[actif_stockage.cle]
            puissance_charge_actif = self.puissance_charge[actif_stockage.cle]
            for annee in range(nombre_annees):
                donnees_annuelles = donnees_entree.ambiance_realisee[annee]
                for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                    for heure in range(8760):
                        stock = stock_actif[annee][indice_meteo][heure]
                        stock_suivant = stock_actif[annee][indice_meteo][(heure+1)%8760]
                        puissance_charge = puissance_charge_actif[annee][indice_meteo][heure]
                        puissance_decharge = puissance_decharge_actif[annee][indice_meteo][heure]
                        contrainte = pulp.LpConstraint(
                            e= stock_suivant - stock + puissance_decharge * 1 / actif_stockage.rendement_decharge - puissance_charge * actif_stockage.rendement_charge,
                            sense=pulp.LpConstraintEQ,
                            rhs=0,
                            name="continuite_stock_%s_annee_%d_meteo_%d_heure_%d" % (actif_stockage.cle, annee, indice_meteo, heure)
                        )
                        self.addConstraint(contrainte)

        # contrainte sur la valeur du stock de départ
        # ceci revient à contraindre également le stock d'arrivée étant donné le "cycle" formé par les contraintes de
        # continuité du stock
        
        # for actif_stockage in donnees_entree.actifs_stockage():
            # stock_actif = self.stock[actif_stockage.cle]
            # nombre_unites_actif = self.nombre_unites[actif_stockage.cle]
            # for annee in range(nombre_annees):
                # donnees_annuelles = donnees_entree.ambiance_realisee[annee]
                # for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                    # stock_depart = stock_actif[annee][indice_meteo][0]
                    # valeur_contrainte = nombre_unites_actif[annee] * actif_stockage.capacite * actif_stockage.stock_initial
                    # contrainte = pulp.LpConstraint(
                        # e=stock_depart - valeur_contrainte,
                        # sense=pulp.LpConstraintEQ,
                        # rhs=0,
                        # name="stock_initial_%s_annee_%d_meteo_%d" % (actif_stockage.cle, annee, indice_meteo)
                    # )
                    # self.addConstraint(contrainte)

        # contrainte de borne supérieure sur la production
        for actif in donnees_entree.actifs_hors_stockage():
            production_actif = self.production[actif.cle]
            nombre_unites_actif = self.nombre_unites[actif.cle]
            for annee in range(nombre_annees):
                donnees_annuelles = donnees_entree.ambiance_realisee[annee]
                for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                    meteo = donnees_annuelles[indice_meteo]
                    for heure in range(8760):
                        production = production_actif[annee][indice_meteo][heure]
                        borne_superieure_production = None
                        if(actif.categorie == "ENR"):
                            borne_superieure_production = nombre_unites_actif[annee] * actif.puissance * meteo.facteur_production_ENR(actif.cle, heure)
                        else:
                            borne_superieure_production = nombre_unites_actif[annee] * actif.puissance
                        contrainte = pulp.LpConstraint(
                            e=borne_superieure_production - production,
                            sense=pulp.LpConstraintGE,
                            rhs=0,
                            name="borne_superieure_production_%s_annee_%d_meteo_%d_heure_%d" % (actif.cle, annee, indice_meteo, heure)
                        )
                        self.addConstraint(contrainte)

        # contraintes de bornes supérieures sur le stock, la puissance de charge et la puissance de décharge
        for actif_stockage in donnees_entree.actifs_stockage():
            stock_actif = self.stock[actif_stockage.cle]
            puissance_charge_actif = self.puissance_charge[actif_stockage.cle]
            puissance_decharge_actif = self.puissance_decharge[actif_stockage.cle]

            nombre_unites_actif = self.nombre_unites[actif_stockage.cle]
            for annee in range(nombre_annees):
                borne_superieure_stock = nombre_unites_actif[annee] * actif_stockage.capacite
                borne_superieure_puissance_charge = nombre_unites_actif[annee] * actif_stockage.puissance_nominale_charge
                borne_superieure_puissance_decharge = nombre_unites_actif[annee] * actif_stockage.puissance_nominale_decharge

                donnees_annuelles = donnees_entree.ambiance_realisee[annee]
                for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                    for heure in range(8760):
                        stock = stock_actif[annee][indice_meteo][heure]
                        puissance_charge = puissance_charge_actif[annee][indice_meteo][heure]
                        puissance_decharge = puissance_decharge_actif[annee][indice_meteo][heure]

                        contrainte = pulp.LpConstraint(
                            e=borne_superieure_stock - stock,
                            sense=pulp.LpConstraintGE,
                            rhs=0,
                            name="borne_superieure_stock_%s_annee_%d_meteo_%d_heure_%d" % (actif_stockage.cle, annee, indice_meteo, heure)
                        )
                        self.addConstraint(contrainte)

                        contrainte = pulp.LpConstraint(
                            e=borne_superieure_puissance_charge - puissance_charge,
                            sense=pulp.LpConstraintGE,
                            rhs=0,
                            name="borne_superieure_puissance_charge_%s_annee_%d_meteo_%d_heure_%d" % (actif_stockage.cle, annee, indice_meteo, heure)
                        )
                        self.addConstraint(contrainte)

                        contrainte = pulp.LpConstraint(
                            e=borne_superieure_puissance_decharge - puissance_decharge,
                            sense=pulp.LpConstraintGE,
                            rhs=0,
                            name="borne_superieure_puissance_decharge_%s_annee_%d_meteo_%d_heure_%d" % (actif_stockage.cle, annee, indice_meteo, heure)
                        )
                        self.addConstraint(contrainte)

        # contraintes imposant que les actifs ne dépassent pas leur durée de vie
        for actif in donnees_entree.tous_actifs():
            duree_vie = actif.duree_vie
            nombre_unites_actif = self.nombre_unites[actif.cle]
            nombre_unites_fermees_actif = self.nombre_unites_fermees[actif.cle]
            for annee in range(max(0, nombre_annees - duree_vie)):
                # on impose que pour chaque année considérée, le nombre d'unités actives soit inférieur ou égal
                # au nombre de fermetures ayant lieu dans la période  équivalente à une durée de vie qui la suit
                # ce qui revient à s'assurer que chaque unité active peut se voir associer une fermeture sans dépasser
                # cette durée
                contrainte = pulp.LpConstraint(
                    e= pulp.lpSum([nombre_unites_fermees_actif[annee_future] for annee_future in range(annee, annee + duree_vie + 1)]) - nombre_unites_actif[annee],
                    sense=pulp.LpConstraintGE,
                    rhs=0,
                    name="non-depassement_duree_vie_%s_%d" % (actif.cle, annee)
                )
                self.addConstraint(contrainte)

        # contraintes de gisement
        for actif in donnees_entree.tous_actifs():
            if actif.gisement_max == "aucun" or not(actif.puissance > 0):
                # en l'absence de borne de gisement ou dans le cas où l'actif n'a pas une puissance stictement positive,
                # il n'y a aucune contrainte à imposer
                break

            nombre_max_unites_actif = np.floor(actif.gisement_max / actif.puissance)

            nombre_unites_actif = self.nombre_unites[actif.cle]

            for annee in range(nombre_annees):
                contrainte = pulp.LpConstraint(
                    e=nombre_unites_actif[annee],
                    sense=pulp.LpConstraintLE,
                    rhs=nombre_max_unites_actif,
                    name="limite_gisement_%s_%d" % (actif.cle, annee)
                )
                self.addConstraint(contrainte)

        # contraintes d'ouvertures forcées et de fermetures programmées initialement
        for actif in donnees_entree.tous_actifs():
        
            nombre_unites_ouverture_forcee_actif_reference = np.zeros(nombre_annees, dtype=int)
            for annee in range(nombre_annees):
                nombre_unites_ouverture_forcee_actif_reference[annee] = donnees_simulation.parc.nombre_unites(actif.cle, annee)

            nombre_unites_ouverture_forcee_ouvertes_actif = np.zeros(nombre_annees, dtype=int)
            for annee in range(nombre_annees):
                for unite in donnees_simulation.parc.unites_ouvertes(actif.cle, annee):
                    nombre_unites_ouverture_forcee_ouvertes_actif[unite.annee_ouverture] += 1
                    
                    
            # recuperation des variables PuLP        

            nombre_unites_actif = self.nombre_unites[actif.cle]
            nombre_unites_ouvertes_actif = self.nombre_unites_ouvertes[actif.cle]
            nombre_unites_fermees_actif = self.nombre_unites_fermees[actif.cle]

            nombre_unites_ouverture_forcee_actif = self.nombre_unites_ouverture_forcee[actif.cle]
            nombre_unites_ouverture_forcee_fermees_actif = self.nombre_unites_ouverture_forcee_fermees[actif.cle]

            for annee in range(nombre_annees):
                # contraintes analogues à celles pour l'évolution du nombre d'unités
                if annee == 0:
                    # à l'année 0, les unités du parc initial sont ajoutées
                    contrainte = pulp.LpConstraint(
                        e=nombre_unites_ouverture_forcee_actif[annee] + nombre_unites_ouverture_forcee_fermees_actif[annee],
                        sense=pulp.LpConstraintEQ,
                        rhs=parc_initial[actif.cle],
                        name="evolution_nombre_unites_ouverture_forcee_%s_%d" % (actif.cle, annee)
                    )
                    self.addConstraint(contrainte)
                else:
                    contrainte = pulp.LpConstraint(
                        e=nombre_unites_ouverture_forcee_actif[annee] - nombre_unites_ouverture_forcee_actif[annee - 1] + nombre_unites_ouverture_forcee_fermees_actif[annee],
                        sense=pulp.LpConstraintEQ,
                        rhs=nombre_unites_ouverture_forcee_ouvertes_actif[annee],
                        name="evolution_nombre_unites_ouverture_forcee_%s_%d" % (actif.cle, annee)
                    )
                    self.addConstraint(contrainte)

                # le nombre d'unités dont l'ouverture est forcée doit être inférieur à la trajectoire de référence
                # car on n'autorise pas à dépasser la date de fermeture programmée
                # en revanche on autorise à fermer les unités avant la date prévue
                nombre_unites_ouverture_forcee_actif[annee].bounds(0, nombre_unites_ouverture_forcee_actif_reference[annee])

                if annee > 0:
                    # le nombre d'ouvertures total est supérieur au nombre d'ouvertures d'unités dont l'ouverture est
                    # forcée, sauf pour l'année 0 où les unités dont l'ouverture est forcée constituent le parc initial
                    contrainte = pulp.LpConstraint(
                        e=nombre_unites_ouvertes_actif[annee],
                        sense=pulp.LpConstraintGE,
                        rhs=nombre_unites_ouverture_forcee_ouvertes_actif[annee],
                        name="borne_nombre_unites_ouvertes_%s_%d" % (actif.cle, annee)
                    )
                    self.addConstraint(contrainte)

                # le nombre de fermetures total est supérieur au nombre de fermetures d'unités dont l'ouverture est
                # forcée
                contrainte = pulp.LpConstraint(
                    e=nombre_unites_fermees_actif[annee] - nombre_unites_ouverture_forcee_fermees_actif[annee],
                    sense=pulp.LpConstraintGE,
                    rhs=0,
                    name="borne_nombre_unites_fermees_%s_%d" % (actif.cle, annee)
                )
                self.addConstraint(contrainte)

                
        # contraintes actif ajoutable
        
        for actif in donnees_entree.tous_actifs():
        
            if not actif.ajoutable :
                
                nombre_unites_ouvertes_actif = self.nombre_unites_ouvertes[actif.cle]
            
                for annee in range(nombre_annees):
                
                    contrainte = pulp.LpConstraint(
                        e=nombre_unites_ouvertes_actif[annee],
                        sense=pulp.LpConstraintEQ,
                        rhs=0,
                        name="Actif_non_ajoutable_%s_%d" % (actif.cle, annee)
                    )
                    self.addConstraint(contrainte)                
                        
        
        
        # ################# #
        # FONCTION OBJECTIF #
        # ################# #
               
        
        self.cout_production = pulp.lpSum([
            pulp.lpSum([
                pulp.lpSum([
                    pulp.lpSum([
                        pulp.lpSum([
                            (donnees_entree.ambiance_realisee[annee].prix_combustible(actif_pilotable, 0) / actif_pilotable.rendement + donnees_entree.ambiance_realisee[annee].prix_carbone(0) * actif_pilotable.emission_carbone) * self.production[actif_pilotable.cle][annee][indice_meteo][heure] for heure in range(8760)
                        ]) for indice_meteo in range(donnees_entree.ambiance_realisee[annee].nombre_meteos())
                    ]) / max(1, donnees_entree.ambiance_realisee[annee].nombre_meteos()) * 1 / (1 + taux_actualisation)**annee for annee in range(nombre_annees)
                ]) for actif_pilotable in donnees_entree.actifs_pilotables()
            ]),
            pulp.lpSum([
                pulp.lpSum([
                    pulp.lpSum([
                        pulp.lpSum([
                            actif_ENR.cout_variable * self.production[actif_ENR.cle][annee][indice_meteo][heure] for heure in range(8760)
                        ]) for indice_meteo in range(donnees_entree.ambiance_realisee[annee].nombre_meteos())
                    ]) / max(1, donnees_entree.ambiance_realisee[annee].nombre_meteos()) * 1 / (1 + taux_actualisation)**annee for annee in range(nombre_annees)
                ]) for actif_ENR in donnees_entree.actifs_ENR()
            ]),
            pulp.lpSum([
                pulp.lpSum([
                    pulp.lpSum([
                        pulp.lpSum([
                            actif_stockage.cout_variable * self.puissance_decharge[actif_stockage.cle][annee][indice_meteo][heure] for heure in range(8760)
                        ]) for indice_meteo in range(donnees_entree.ambiance_realisee[annee].nombre_meteos())
                    ]) / max(1, donnees_entree.ambiance_realisee[annee].nombre_meteos()) * 1 / (1 + taux_actualisation)**annee for annee in range(nombre_annees)
                ]) for actif_stockage in donnees_entree.actifs_stockage()])
            ])

        self.cout_defaillance = pulp.lpSum([
            pulp.lpSum([
                pulp.lpSum([
                    donnees_entree.parametres_simulation.plafond_prix * self.defaillance[annee][indice_meteo][heure] for heure in range(8760)
                ]) for indice_meteo in range(donnees_entree.ambiance_realisee[annee].nombre_meteos())
            ]) / max(1, donnees_entree.ambiance_realisee[annee].nombre_meteos()) * 1 / (1 + taux_actualisation)**annee for annee in range(nombre_annees)
        ])
        
            
        self.cout_construction = pulp.lpSum([
            pulp.lpSum([
                #IndicateursEconomiques.calcul_investissement_IDC_annualise(actif, max(0, annee - actif.duree_construction)) * 1 / (1 + taux_actualisation)**annee * sum([1 / (1 + taux_actualisation)**annee_future for annee_future in range(min(actif.duree_vie, nombre_annees - annee))]) * self.nombre_unites_ouvertes[actif.cle][annee] for annee in range(nombre_annees)
                IndicateursEconomiques.calcul_investissement_IDC_annualise(actif, max(0, annee - actif.duree_construction)) * 1 / (1 + taux_actualisation) ** annee * sum([1 / (1 + taux_actualisation) ** annee_future for annee_future in range(min(actif.duree_vie, nombre_annees - annee))]) * self.nombre_unites_ouvertes[actif.cle][annee] for annee in range(nombre_annees)
            ]) for actif in donnees_entree.tous_actifs()
        ])

        self.cout_maintenance = pulp.lpSum([
            pulp.lpSum([
                self.nombre_unites[actif.cle][annee] * actif.cout_fixe_maintenance * 1 / (1 + taux_actualisation)**annee for annee in range(nombre_annees)
            ]) for actif in donnees_entree.tous_actifs()
        ])

        self.cout_total = pulp.lpSum([self.cout_production, self.cout_defaillance, self.cout_construction, self.cout_maintenance])

        self.setObjective(self.cout_total)


def generation_mix_cible(donnees_entree, donnees_simulation, liste_contraintes_trajectoire, type_optim,df_co2_quota,taux_actualisation=0.0):
    """
    Génère un mix cible en optimisant les trajectoires des actifs non-contraints pour minimiser les coûts de
    construction, de production, de défaillance et de maintenance, éventuellement actualisés.

    Paramètres
    ----------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    liste_actifs_trajectoire_contraintes : list
        liste des actifs dont la trajectoire doit respecter le mix cible donné en entrée
    parc_initial : dict
        dictionnaire contenant, pour chaque actif, le nombre d'unités présentes dans le parc initialement
    taux_actualisation : float
        taux d'actualisation pour actualiser les coût payés chaque année

    Retours
    -------
    dict
        dictionnaire contenant, pour chaque actif, la trajectoire cible
    """

    probleme_genration_mix_cible = ProblemeGenerationMixCible(donnees_entree, donnees_simulation, liste_contraintes_trajectoire, type_optim,df_co2_quota,taux_actualisation)

    
    dossier_compte_rendu = donnees_entree.output_path   
    
    log_path = os.path.join(dossier_compte_rendu,"log.txt")

    solver = pulp.CPLEX_CMD(path="/opt/cplex/12.8/cplex/bin/x86-64_linux/cplex")
    
    path_lp = os.path.join(dossier_compte_rendu,"lp.lp")
    probleme_genration_mix_cible.writeLP(path_lp)
 
    probleme_genration_mix_cible.solve(solver)

    if not(probleme_genration_mix_cible.status == 1):
        print("/!\\ /!\\ LE PROBLEME N'A PAS PU ETRE RESOLU CORRECTEMENT /!\\ /!\\")
        print("status : ", probleme_genration_mix_cible.status)

    print("coût construction : ", probleme_genration_mix_cible.cout_construction.value())
    print("coût production : ", probleme_genration_mix_cible.cout_production.value())
    print("coût défaillance : ", probleme_genration_mix_cible.cout_defaillance.value())
    print("coût maintenance : ", probleme_genration_mix_cible.cout_maintenance.value())
    print("coût total : ", probleme_genration_mix_cible.cout_total.value())

    #nombre_annees = donnees_entree.parametres_simulation.horizon_simulation + donnees_entree.parametres_simulation.horizon_prevision
    nombre_annees = donnees_entree.parametres_simulation.horizon_simulation #+ donnees_entree.parametres_simulation.horizon_prevision

    for actif in donnees_entree.tous_actifs():
        print("nombre unités ", actif.cle, [probleme_genration_mix_cible.nombre_unites[actif.cle][annee].value() for annee in range(nombre_annees)])

    for actif in donnees_entree.tous_actifs():
        print("ouvertures ", actif.cle, [probleme_genration_mix_cible.nombre_unites_ouvertes[actif.cle][annee].value() for annee in range(nombre_annees)])

    for actif in donnees_entree.tous_actifs():
        print("fermetures ", actif.cle, [probleme_genration_mix_cible.nombre_unites_fermees[actif.cle][annee].value() for annee in range(nombre_annees)])

    for actif in donnees_entree.tous_actifs():
        print("unites forcees ", actif.cle, [probleme_genration_mix_cible.nombre_unites_ouverture_forcee[actif.cle][annee].value() for annee in range(nombre_annees)])

    for actif in donnees_entree.tous_actifs():
        print("unites forcees fermees ", actif.cle, [probleme_genration_mix_cible.nombre_unites_ouverture_forcee_fermees[actif.cle][annee].value() for annee in range(nombre_annees)])

    heures_defaillance = np.zeros(nombre_annees, dtype=int)
    volume_defaillance = np.zeros(nombre_annees)
    for annee in range(nombre_annees):
        heures_defaillance[annee] = sum([1 * (probleme_genration_mix_cible.defaillance[annee][0][heure].value() > 0) for heure in range(8760)])
        volume_defaillance[annee] = sum([probleme_genration_mix_cible.defaillance[annee][0][heure].value() for heure in range(8760)])
    print(heures_defaillance)
    print(volume_defaillance)

    ecretement = dict()
    for actif_renouvelable in donnees_entree.actifs_ENR():
        ecretement_actif = []
        for annee in range(nombre_annees):
            ecretement_actif_annee = sum([probleme_genration_mix_cible.nombre_unites[actif_renouvelable.cle][annee].value() * actif_renouvelable.puissance * donnees_entree.ambiance_realisee[annee][0].facteur_production_ENR(actif_renouvelable.cle, heure) - probleme_genration_mix_cible.production[actif_renouvelable.cle][annee][0][heure].value() for heure in range(8760)])
            ecretement_actif.append(ecretement_actif_annee)
        ecretement[actif_renouvelable.cle] = ecretement_actif
    print(ecretement)

    registre_couts = dict()
    registre_couts["cout_production"] = [probleme_genration_mix_cible.cout_production.value()]
    registre_couts["cout_defaillance"] = [probleme_genration_mix_cible.cout_defaillance.value()]
    registre_couts["cout_construction"] = [probleme_genration_mix_cible.cout_construction.value()]
    registre_couts["cout_maintenance"] = [probleme_genration_mix_cible.cout_maintenance.value()]
    registre_couts["cout_total"] = [probleme_genration_mix_cible.cout_total.value()]

    mix_cible = dict()
    registre_annuel = dict()
    
    for actif in donnees_entree.tous_actifs():
        trajectoire_actif = np.zeros(nombre_annees, dtype=int)
        
        capacite_installee_non_arrondie = np.zeros(nombre_annees, dtype=float)
        nb_ouverture_non_arrondie = np.zeros(nombre_annees, dtype=float)
        nb_fermeture_non_arrondie = np.zeros(nombre_annees, dtype=float)
          
        
        variables_nombres_unites_actif = probleme_genration_mix_cible.nombre_unites[actif.cle]
        variables_ouvertures = probleme_genration_mix_cible.nombre_unites_ouvertes[actif.cle]
        variables_fermetures = probleme_genration_mix_cible.nombre_unites_fermees[actif.cle]
        
        for annee in range(nombre_annees):
            trajectoire_actif[annee] = round(variables_nombres_unites_actif[annee].value(), 0)
            capacite_installee_non_arrondie[annee] = variables_nombres_unites_actif[annee].value()
            nb_ouverture_non_arrondie[annee] = variables_ouvertures[annee].value()
            nb_fermeture_non_arrondie[annee] = variables_fermetures[annee].value()
            
        mix_cible[actif.cle] = trajectoire_actif

        registre_annuel["capacite_installee_%s"%actif.cle] = capacite_installee_non_arrondie * actif.puissance
        registre_annuel["nb_unite_%s"%actif.cle] = capacite_installee_non_arrondie
        registre_annuel["nb_ouverture_%s"%actif.cle] = nb_ouverture_non_arrondie
        registre_annuel["nb_fermeture_%s"%actif.cle] = nb_fermeture_non_arrondie

        couts_variables = np.zeros(nombre_annees)
        for annee in range(nombre_annees):
            if actif.categorie == "Pilotable":
                couts_variables[annee] = donnees_entree.ambiance_realisee[annee].prix_combustible(actif, 0) / actif.rendement + donnees_entree.ambiance_realisee[annee].prix_carbone(0) * actif.emission_carbone
            elif actif.categorie in ["Stockage", "ENR"]:
                couts_variables[annee] = actif.cout_variable

        registre_annuel["couts_variables_%s" % actif.cle] = couts_variables

    # écriture des valeurs des variables duales des contraintes personnalisées
    for nom_contrainte_trajectoire, liste_contraintes_personnalisees_annuelles in probleme_genration_mix_cible.dict_contraintes_personnalisees.items():
        valeurs_variables_duales = np.array([contrainte.pi for contrainte in liste_contraintes_personnalisees_annuelles])
        registre_annuel["variables_duales_%s"%nom_contrainte_trajectoire] = valeurs_variables_duales
    
    
    variables_duales_CO2 = []
    
    for annee in range(nombre_annees):
        if annee in probleme_genration_mix_cible.liste_contrainte_CO2.keys():
            variables_duales_CO2.append( -1* probleme_genration_mix_cible.liste_contrainte_CO2[annee].pi    )
        else :
             variables_duales_CO2.append(0)
             
    variables_duales_CO2 = np.array(variables_duales_CO2)
    
    registre_annuel["variables_duales_co2"] = variables_duales_CO2
    
    registre_horaire = []

    for annee in range(nombre_annees):
        liste_donnees_horaires_annee = []
        donnees_annuelles = donnees_entree.ambiance_realisee[annee]
        for indice_meteo in range(donnees_annuelles.nombre_meteos()):
        
            meteo = donnees_annuelles[indice_meteo]
            
            donnees_horaires_meteo_annee = dict()
            for actif in donnees_entree.actifs_hors_stockage():
                production = [probleme_genration_mix_cible.production[actif.cle][annee][indice_meteo][heure].value() for heure in range(8760)]
                donnees_horaires_meteo_annee["production_%s"%actif.cle] = production
                if(actif.categorie == "ENR"):
                    ecretement =  [  ((actif.puissance* probleme_genration_mix_cible.nombre_unites[actif.cle][annee].value() * meteo.facteur_production_ENR(actif.cle, heure))  - production[heure]) for heure in range(8760)]
                    donnees_horaires_meteo_annee["ecretement_%s"%actif.cle] = ecretement
            for actif_stockage in donnees_entree.actifs_stockage():
                puissance_charge = [probleme_genration_mix_cible.puissance_charge[actif_stockage.cle][annee][indice_meteo][heure].value() for heure in range(8760)]
                puissance_decharge = [probleme_genration_mix_cible.puissance_decharge[actif_stockage.cle][annee][indice_meteo][heure].value() for heure in range(8760)]
                stock = [probleme_genration_mix_cible.stock[actif_stockage.cle][annee][indice_meteo][heure].value() for heure in range(8760)]
                donnees_horaires_meteo_annee["puissance_charge_%s" % actif_stockage.cle] = puissance_charge
                donnees_horaires_meteo_annee["puissance_decharge_%s" % actif_stockage.cle] = puissance_decharge
                donnees_horaires_meteo_annee["stock_%s" % actif_stockage.cle] = stock
            prix_horaires = [probleme_genration_mix_cible.contraintes_satisfaction_demande[annee][indice_meteo][heure].pi for heure in range(8760)]
            donnees_horaires_meteo_annee["prix_horaire"] = prix_horaires
            defaillance = [probleme_genration_mix_cible.defaillance[annee][indice_meteo][heure].value() for heure in range(8760)]
            donnees_horaires_meteo_annee["defaillance"] = defaillance
            donnees_horaires_meteo_annee["demande"] = [ meteo.demande(0, heure)  for heure in range(8760)]
            liste_donnees_horaires_annee.append(donnees_horaires_meteo_annee)
        registre_horaire.append(liste_donnees_horaires_annee)

    return mix_cible, registre_couts, registre_annuel, registre_horaire,probleme_genration_mix_cible

