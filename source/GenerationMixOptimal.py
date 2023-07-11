# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF


import pulp
import numpy as np

import IndicateursEconomiques


class ContrainteMix:
    def __init__(self, nom, liste_actifs_concernes, type_contrainte, grandeur_concernee, valeur_second_membre):
        self.nom = nom
        self.liste_actifs_concernes = liste_actifs_concernes
        self.type_contrainte = type_contrainte
        self.grandeur_concernee = grandeur_concernee
        self.valeur_second_membre = valeur_second_membre


class ProblemeGenerationMixOptimal(pulp.LpProblem):
    """
    Problème de génération de mix optimal from scratch.

    Cette classe représente un problème d'optimisation calculant un mix optimal "from scratch" pour une année donnée,
    elle hérite de la classe de problème linéaire de pulp.


    Attributs
    ---------
    nombre_unites : dict
        dictionnaire contenant, pour chaque actif, les variables de nombre d'unités présentes dans le parc
    production : dict
        dictionnaire contenant, pour chaque type d'actif, les variables de quantité d'énergie produite pour chaque météo
         et à chaque heure
    defaillance : pulp.LpVariable.dict
        dictionnaire contenant les variables des puissances non-fournies pour chaque météo et à chaque heure
    stock : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, les variables de stock
    puissance_charge : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, les variables de puissance de charge
    puissance_decharge : dict
        dictionnaire contenant, pour chaque type d'actif de stockage, les variables de puissance de décharge
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

    def __init__(self, donnees_entree, annee, liste_contraintes_mix):

        super().__init__("Generation_mix_optimal", pulp.LpMinimize)

        donnees_annuelles = donnees_entree.ambiance_realisee[annee]

        # ######### #
        # VARIABLES #
        # ######### #

        # initialisation des variables de nombre d'unités
        self.nombre_unites = dict()

        for actif in donnees_entree.tous_actifs():
            self.nombre_unites[actif.cle] = pulp.LpVariable("nombre_unites_%s" % (actif.cle), lowBound=0, cat="Continuous")

        # initialisation des variables de production des actifs hors stockage
        self.production = dict()
        for actif_hors_stockage in donnees_entree.actifs_hors_stockage():
            production_actif = []
            for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                production_actif_meteo = pulp.LpVariable.dict("production_%s_meteo_%d" % (actif_hors_stockage.cle, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                production_actif.append(production_actif_meteo)
            self.production[actif_hors_stockage.cle] = production_actif

        # initialisation des variables de stock, puissance de charge et puissance de décharge des actifs de stockage
        self.stock = dict()
        self.puissance_charge = dict()
        self.puissance_decharge = dict()
        for actif_stockage in donnees_entree.actifs_stockage():
            stock_actif = []
            puissance_charge_actif = []
            puissance_decharge_actif = []
            for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                stock_actif_meteo = pulp.LpVariable.dict("stock_%s_meteo_%d" % (actif_stockage.cle, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                puissance_charge_actif_meteo = pulp.LpVariable.dict("puissance_charge_%s_meteo_%d" % (actif_stockage.cle, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                puissance_decharge_actif_meteo = pulp.LpVariable.dict("puissance_decharge_%s_meteo_%d" % (actif_stockage.cle,indice_meteo), range(8760), lowBound=0, cat="Continuous")
                stock_actif.append(stock_actif_meteo)
                puissance_charge_actif.append(puissance_charge_actif_meteo)
                puissance_decharge_actif.append(puissance_decharge_actif_meteo)
            self.stock[actif_stockage.cle] = stock_actif
            self.puissance_charge[actif_stockage.cle] = puissance_charge_actif
            self.puissance_decharge[actif_stockage.cle] = puissance_decharge_actif

        # initialisation des variables de défaillance
        self.defaillance = []
        for indice_meteo in range(donnees_annuelles.nombre_meteos()):
            defaillance_meteo = pulp.LpVariable.dict("defaillance_meteo_%d" % (indice_meteo), range(8760), lowBound=0, cat="Continuous")
            self.defaillance.append(defaillance_meteo)

        # ########### #
        # CONTRAINTES #
        # ########### #

        # contraintes de mix imposées par l'utilisateur
        self.dict_contraintes_personnalisees = dict()
        for contrainte_mix in liste_contraintes_mix:
            sens_contrainte = None
            nom_contrainte_mix = contrainte_mix.nom

            if contrainte_mix.type_contrainte == "egalite":
                sens_contrainte = pulp.LpConstraintEQ
            elif contrainte_mix.type_contrainte == "borne_inferieure":
                sens_contrainte = pulp.LpConstraintGE
            elif contrainte_mix.type_contrainte == "borne_superieure":
                sens_contrainte = pulp.LpConstraintLE

            variables_nombre_unites_et_facteurs = []
            donnees_annuelles = donnees_entree.ambiance_realisee[annee]
            for actif in contrainte_mix.liste_actifs_concernes:
                nombre_unites_actif = self.nombre_unites[actif.cle]

                facteur = actif.puissance
                if contrainte_mix.grandeur_concernee == "energie_productible":
                    if actif.categorie == "ENR":
                        liste_energies_productibles = []
                        for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                            meteo = donnees_annuelles[indice_meteo]
                            liste_energies_productibles.append(
                                actif.puissance * np.sum(meteo.facteurs_production_ENR(actif.cle)))
                        facteur = sum(liste_energies_productibles) / len(liste_energies_productibles)
                    else:
                        facteur = 8760 * actif.puissance

                variables_nombre_unites_et_facteurs.append((nombre_unites_actif, facteur))

            second_membre = contrainte_mix.valeur_second_membre
            if contrainte_mix.grandeur_concernee == "energie_productible":
                liste_demandes = []
                for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                    meteo = donnees_annuelles[indice_meteo]
                    liste_demandes.append(np.sum(meteo.demande_annuelle(0)))
                second_membre = sum(liste_demandes) / len(liste_demandes) * contrainte_mix.valeur_second_membre / 100

            contrainte = pulp.LpConstraint(
                e=pulp.lpSum([facteur * nombre_unites for nombre_unites, facteur in variables_nombre_unites_et_facteurs]),
                sense=sens_contrainte,
                rhs=second_membre,
                name="contrainte_trajectoire_%s" % nom_contrainte_mix
            )
            self.addConstraint(contrainte)
            self.dict_contraintes_personnalisees[nom_contrainte_mix] = contrainte

        # contraintes de satisfaction de la demande
        self.contraintes_satisfaction_demande = []
        for indice_meteo in range(donnees_annuelles.nombre_meteos()):
            meteo = donnees_annuelles[indice_meteo]
            contraintes_satisfaction_demande_meteo = []
            for heure in range(8760):
                somme_productions = pulp.lpSum([production_actif[indice_meteo][heure] for cle_actif, production_actif in self.production.items()])
                somme_puissances_charge = pulp.lpSum([puissance_charge_actif[indice_meteo][heure] for cle_actif, puissance_charge_actif in self.puissance_charge.items()])
                somme_puissances_decharge = pulp.lpSum([puissance_decharge_actif[indice_meteo][heure] for cle_actif, puissance_decharge_actif in self.puissance_decharge.items()])
                demande = meteo.demande(0, heure)
                defaillance = self.defaillance[indice_meteo][heure]
                contrainte = pulp.LpConstraint(
                    e=somme_productions - somme_puissances_charge + somme_puissances_decharge + defaillance,
                    sense=pulp.LpConstraintEQ,
                    rhs=demande,
                    name="satisfaction_demande_meteo_%d_heure_%d" % (indice_meteo, heure)
                )
                self.addConstraint(contrainte)
                contraintes_satisfaction_demande_meteo.append(contrainte)
            self.contraintes_satisfaction_demande.append(contraintes_satisfaction_demande_meteo)

        # contraintes de continuité du stock
        for actif_stockage in donnees_entree.actifs_stockage():
            stock_actif = self.stock[actif_stockage.cle]
            puissance_decharge_actif = self.puissance_decharge[actif_stockage.cle]
            puissance_charge_actif = self.puissance_charge[actif_stockage.cle]
            for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                for heure in range(8760):
                    stock = stock_actif[indice_meteo][heure]
                    stock_suivant = stock_actif[indice_meteo][(heure+1)%8760]
                    puissance_charge = puissance_charge_actif[indice_meteo][heure]
                    puissance_decharge = puissance_decharge_actif[indice_meteo][heure]
                    contrainte = pulp.LpConstraint(
                        e= stock_suivant - stock + puissance_decharge * 1 / actif_stockage.rendement_decharge - puissance_charge * actif_stockage.rendement_charge,
                        sense=pulp.LpConstraintEQ,
                        rhs=0,
                        name="continuite_stock_%s_meteo_%d_heure_%d" % (actif_stockage.cle, indice_meteo, heure)
                    )
                    self.addConstraint(contrainte)

        # contrainte sur la valeur du stock de départ
        # ceci revient à contraindre également le stock d'arrivée étant donné le "cycle" formé par les contraintes de
        # continuité du stock
        for actif_stockage in donnees_entree.actifs_stockage():
            stock_actif = self.stock[actif_stockage.cle]
            nombre_unites_actif = self.nombre_unites[actif_stockage.cle]
            for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                stock_depart = stock_actif[indice_meteo][0]
                valeur_contrainte = nombre_unites_actif * actif_stockage.capacite * actif_stockage.stock_initial
                contrainte = pulp.LpConstraint(
                    e=stock_depart - valeur_contrainte,
                    sense=pulp.LpConstraintEQ,
                    rhs=0,
                    name="stock_initial_%s_meteo_%d" % (actif_stockage.cle, indice_meteo)
                )
                self.addConstraint(contrainte)

        # contrainte de borne supérieure sur la production
        for actif in donnees_entree.actifs_hors_stockage():
            production_actif = self.production[actif.cle]
            nombre_unites_actif = self.nombre_unites[actif.cle]
            for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                meteo = donnees_annuelles[indice_meteo]
                for heure in range(8760):
                    production = production_actif[indice_meteo][heure]
                    borne_superieure_production = None
                    if(actif.categorie == "ENR"):
                        borne_superieure_production = nombre_unites_actif * actif.puissance * meteo.facteur_production_ENR(actif.cle, heure)
                    else:
                        borne_superieure_production = nombre_unites_actif * actif.puissance
                    contrainte = pulp.LpConstraint(
                        e=borne_superieure_production - production,
                        sense=pulp.LpConstraintGE,
                        rhs=0,
                        name="borne_superieure_production_%s_meteo_%d_heure_%d" % (actif.cle, indice_meteo, heure)
                    )
                    self.addConstraint(contrainte)

        # contraintes de bornes supérieures sur le stock, la puissance de charge et la puissance de décharge
        for actif_stockage in donnees_entree.actifs_stockage():
            stock_actif = self.stock[actif_stockage.cle]
            puissance_charge_actif = self.puissance_charge[actif_stockage.cle]
            puissance_decharge_actif = self.puissance_decharge[actif_stockage.cle]

            nombre_unites_actif = self.nombre_unites[actif_stockage.cle]

            borne_superieure_stock = nombre_unites_actif * actif_stockage.capacite
            borne_superieure_puissance_charge = nombre_unites_actif * actif_stockage.puissance_nominale_charge
            borne_superieure_puissance_decharge = nombre_unites_actif * actif_stockage.puissance_nominale_decharge

            for indice_meteo in range(donnees_annuelles.nombre_meteos()):
                for heure in range(8760):
                    stock = stock_actif[indice_meteo][heure]
                    puissance_charge = puissance_charge_actif[indice_meteo][heure]
                    puissance_decharge = puissance_decharge_actif[indice_meteo][heure]

                    contrainte = pulp.LpConstraint(
                        e=borne_superieure_stock - stock,
                        sense=pulp.LpConstraintGE,
                        rhs=0,
                        name="borne_superieure_stock_%s_meteo_%d_heure_%d" % (actif_stockage.cle, indice_meteo, heure)
                    )
                    self.addConstraint(contrainte)

                    contrainte = pulp.LpConstraint(
                        e=borne_superieure_puissance_charge - puissance_charge,
                        sense=pulp.LpConstraintGE,
                        rhs=0,
                        name="borne_superieure_puissance_charge_%s_meteo_%d_heure_%d" % (actif_stockage.cle, indice_meteo, heure)
                    )
                    self.addConstraint(contrainte)

                    contrainte = pulp.LpConstraint(
                        e=borne_superieure_puissance_decharge - puissance_decharge,
                        sense=pulp.LpConstraintGE,
                        rhs=0,
                        name="borne_superieure_puissance_decharge_%s_meteo_%d_heure_%d" % (actif_stockage.cle, indice_meteo, heure)
                    )
                    self.addConstraint(contrainte)

        # ################# #
        # FONCTION OBJECTIF #
        # ################# #

        self.cout_production = pulp.lpSum([
            pulp.lpSum([
                pulp.lpSum([
                    pulp.lpSum([
                        (donnees_annuelles.prix_combustible(actif_pilotable, 0) / actif_pilotable.rendement + donnees_annuelles.prix_carbone(0) * actif_pilotable.emission_carbone) * self.production[actif_pilotable.cle][indice_meteo][heure] for heure in range(8760)
                    ]) for indice_meteo in range(donnees_annuelles.nombre_meteos())
                ]) for actif_pilotable in donnees_entree.actifs_pilotables()
            ]),
            pulp.lpSum([
                pulp.lpSum([
                    pulp.lpSum([
                        actif_ENR.cout_variable * self.production[actif_ENR.cle][indice_meteo][heure] for heure in range(8760)
                    ]) for indice_meteo in range(donnees_annuelles.nombre_meteos())
                ]) for actif_ENR in donnees_entree.actifs_ENR()
            ]),
            pulp.lpSum([
                pulp.lpSum([
                    pulp.lpSum([
                        actif_stockage.cout_variable * self.puissance_decharge[actif_stockage.cle][indice_meteo][heure] for heure in range(8760)
                    ]) for indice_meteo in range(donnees_annuelles.nombre_meteos())
                ]) for actif_stockage in donnees_entree.actifs_stockage()])
            ])

        self.cout_defaillance = pulp.lpSum([
            pulp.lpSum([
                donnees_entree.parametres_simulation.plafond_prix * self.defaillance[indice_meteo][heure] for heure in range(8760)
            ]) for indice_meteo in range(donnees_annuelles.nombre_meteos())
        ])

        # !!! on ne paye que la première annuité ??? revoir !!!
        self.cout_construction = pulp.lpSum([
            IndicateursEconomiques.calcul_investissement_IDC_annualise(actif, max(0, annee - actif.duree_construction))  * self.nombre_unites[actif.cle] for actif in donnees_entree.tous_actifs()
        ])

        self.cout_maintenance = pulp.lpSum([
            self.nombre_unites[actif.cle] * actif.cout_fixe_maintenance for actif in donnees_entree.tous_actifs()
        ])

        self.cout_total = pulp.lpSum([self.cout_production, self.cout_defaillance, self.cout_construction, self.cout_maintenance])

        self.setObjective(self.cout_total)

def generation_mix_optimal(donnees_entree, annee, liste_contraintes_mix):
    """
    Génère un mix optimal "from scratch" pour l'année donnée en argument en optimisant  pour minimiser les coûts de
    construction, de production, de défaillance et de maintenance.

    Paramètres
    ----------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    annee : int
        année à laquelle vont être considérées les données de l'ambiance de référence pour l'optimisation


    Retours
    -------
    dict
        dictionnaire contenant, pour chaque actif, la trajectoire cible
    """

    probleme_genration_mix_optimal = ProblemeGenerationMixOptimal(donnees_entree, annee, liste_contraintes_mix)

    probleme_genration_mix_optimal.solve()

    if not (probleme_genration_mix_optimal.status == 1):
        print("/!\\ /!\\ LE PROBLEME N'A PAS PU ETRE RESOLU CORRECTEMENT /!\\ /!\\")
        print("status : ", probleme_genration_mix_optimal.status)

    print("coût production : ", probleme_genration_mix_optimal.cout_production.value())
    print("coût défaillance : ", probleme_genration_mix_optimal.cout_defaillance.value())
    print("coût construction : ", probleme_genration_mix_optimal.cout_construction.value())
    print("coût maintenance : ", probleme_genration_mix_optimal.cout_maintenance.value())
    print("coût total : ", probleme_genration_mix_optimal.cout_total.value())

    for actif in donnees_entree.tous_actifs():
        print(actif.cle, probleme_genration_mix_optimal.nombre_unites[actif.cle].value())

    heures_defaillance = sum([1 * (probleme_genration_mix_optimal.defaillance[0][heure].value()>0) for heure in range(8760)])
    volume_defaillance = sum([probleme_genration_mix_optimal.defaillance[0][heure].value() for heure in range(8760)])
    print(heures_defaillance)
    print(volume_defaillance)

    registre_couts = dict()
    registre_couts["cout_production"] = [probleme_genration_mix_optimal.cout_production.value()]
    registre_couts["cout_defaillance"] = [probleme_genration_mix_optimal.cout_defaillance.value()]
    registre_couts["cout_construction"] = [probleme_genration_mix_optimal.cout_construction.value()]
    registre_couts["cout_maintenance"] = [probleme_genration_mix_optimal.cout_maintenance.value()]
    registre_couts["cout_total"] = [probleme_genration_mix_optimal.cout_total.value()]

    mix_optimal = dict()
    registre_annuel = dict()

    for actif in donnees_entree.tous_actifs():

        mix_optimal[actif.cle] = round(probleme_genration_mix_optimal.nombre_unites[actif.cle].value(), 0)

        registre_annuel["capacite_installee_%s" % actif.cle] = [probleme_genration_mix_optimal.nombre_unites[actif.cle].value() * actif.puissance]

        cout_variable = 0
        if actif.categorie == "Pilotable":
            cout_variable = donnees_entree.ambiance_realisee[annee].prix_combustible(actif, 0) / actif.rendement + donnees_entree.ambiance_realisee[annee].prix_carbone(0) * actif.emission_carbone
        elif actif.categorie in ["Stockage", "ENR"]:
            cout_variable = actif.cout_variable

        registre_annuel["cout_variable_%s" % actif.cle] = [cout_variable]

    # écriture des valeurs des variables duales des contraintes personnalisées
    for nom_contrainte_mix, contrainte_personnalisee in probleme_genration_mix_optimal.dict_contraintes_personnalisees.items():
        valeurs_variables_duales = contrainte_personnalisee.pi
        registre_annuel["variable_duale_%s" % nom_contrainte_mix] = [valeurs_variables_duales]

    registre_horaire = []

    donnees_annuelles = donnees_entree.ambiance_realisee[annee]
    for indice_meteo in range(donnees_annuelles.nombre_meteos()):
        donnees_horaires_meteo = dict()
        for actif in donnees_entree.actifs_hors_stockage():
            production = [probleme_genration_mix_optimal.production[actif.cle][indice_meteo][heure].value() for heure in range(8760)]
            donnees_horaires_meteo["production_%s" % actif.cle] = production
        for actif_stockage in donnees_entree.actifs_stockage():
            puissance_charge = [probleme_genration_mix_optimal.puissance_charge[actif_stockage.cle][indice_meteo][heure].value() for heure in range(8760)]
            puissance_decharge = [probleme_genration_mix_optimal.puissance_decharge[actif_stockage.cle][indice_meteo][heure].value() for heure in range(8760)]
            stock = [probleme_genration_mix_optimal.stock[actif_stockage.cle][indice_meteo][heure].value() for heure in range(8760)]
            donnees_horaires_meteo["puissance_charge_%s" % actif_stockage.cle] = puissance_charge
            donnees_horaires_meteo["puissance_decharge_%s" % actif_stockage.cle] = puissance_decharge
            donnees_horaires_meteo["stock_%s" % actif_stockage.cle] = stock
        prix_horaires = [probleme_genration_mix_optimal.contraintes_satisfaction_demande[indice_meteo][heure].pi for heure in range(8760)]
        donnees_horaires_meteo["prix_horaire"] = prix_horaires
        defaillance = [probleme_genration_mix_optimal.defaillance[indice_meteo][heure].value() for heure in range(8760)]
        donnees_horaires_meteo["defaillance"] = defaillance
        registre_horaire.append(donnees_horaires_meteo)

    return mix_optimal, registre_couts, registre_annuel, registre_horaire
