# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF


import sys
import pandas as pd
import os
import time
import pulp
import numpy as np
import DonneesSimulation

def pjoin(*args, **kwargs):
    return os.path.join(*args, **kwargs).replace(os.sep, '//')

def pd_to_dict_rint(df):

    dico = {}
    
    for col in df.columns :
        dico[col] = np.around(df[col].to_numpy()).astype(int)
        
    return dico

def update_anticipation(donnees_entree, donnees_simulation,chemins_gep):
    
    
    for idx,chemin in enumerate(chemins_gep) :
    
        ambiance = list(donnees_entree.ambiances.keys())[idx]
        
        chemin_rep = os.path.normpath(chemin)
        chemin_sorties = pjoin(chemin,"results")
        os.makedirs(chemin_sorties)
        type_optim = "LP"
        
        run_gep(chemin_rep,chemin_sorties,type_optim)
        
        df_reg_ouvertures = pd.read_excel(pjoin(chemin_sorties,"sorties_annuelles.xlsx"),sheet_name="nb_unites_ouvertes",index_col=0)
        df_reg_fermetures = pd.read_excel(pjoin(chemin_sorties,"sorties_annuelles.xlsx"),sheet_name="nb_unites_fermees",index_col=0)
        
        # conversion des dataframes au format 
        
        df_reg_ouvertures.index = df_reg_ouvertures.index.to_numpy() + donnees_simulation.annee_courante
        df_reg_fermetures.index = df_reg_fermetures.index.to_numpy() + donnees_simulation.annee_courante
        
        for n in range(donnees_simulation.annee_courante):
            df_reg_ouvertures.loc[n] = 0
            df_reg_fermetures.loc[n] = 0
            
        df_reg_ouvertures.sort_index(inplace=True)
        df_reg_fermetures.sort_index(inplace=True)
        
        parc_initial = {}
        df_parc = donnees_simulation.parc.get_df_nb_unites()
                
        for actif in donnees_entree.tous_actifs():
            parc_initial[actif.cle] = 0
            df_reg_ouvertures.loc[donnees_simulation.annee_courante,actif.cle] += df_parc.loc[donnees_simulation.annee_courante,actif.cle]
        
            
        reg_ouvertures = pd_to_dict_rint(df_reg_ouvertures)
        reg_fermetures = pd_to_dict_rint(df_reg_fermetures)
        
        
        parc_anticipation = DonneesSimulation.Parc(parc_initial, reg_ouvertures, reg_fermetures, donnees_entree)
        
        donnees_simulation.dico_parcs_anticipes[ambiance] = parc_anticipation


    return None
    
    
def run_gep(chemin_rep,chemin_sorties,type_optim):
    
    ################### Lecture des données
    
    print("Lecture des données")
    
    #### Fichier param
    
    chemin_param_simu = pjoin(chemin_rep,"Parametres","parametres_simulation.csv")
    df_param_simu = pd.read_csv(chemin_param_simu,sep=";",index_col=0)

    taux_actualisation = float(df_param_simu.at["taux_actu_systeme","value"])


    chemin_param_ponderation = pjoin(chemin_rep,"Parametres","parametres_ponderation.csv")
    df_param_ponderation = pd.read_csv(chemin_param_ponderation,sep=";",index_col=0)

    #### Fichier param GEP
    
    chemin_co2_quota = pjoin(chemin_rep,"GenerationMixCible","co2_quota.csv")
    df_quota = pd.read_csv(chemin_co2_quota,sep=";",index_col=0)

    chemin_contraintes = pjoin(chemin_rep,"GenerationMixCible","contraintes_trajectoire.csv")
    df_contraintes = pd.read_csv(chemin_contraintes,sep=";").T    
    
    #### Fichiers actifs
    
    chemin_actifs_enr = pjoin(chemin_rep,"Actifs","actifs_enr.csv")
    df_actifs_enr = pd.read_csv(chemin_actifs_enr,sep=";",index_col=0)
    
    chemin_actifs_pilot = pjoin(chemin_rep,"Actifs","actifs_pilot.csv")
    df_actifs_pilot = pd.read_csv(chemin_actifs_pilot,sep=";",index_col=0)

    chemin_actifs_stockage = pjoin(chemin_rep,"Actifs","actifs_stockage.csv")    
    df_actifs_stockage = pd.read_csv(chemin_actifs_stockage,sep=";",index_col=0)
    

    tous_actifs = np.concatenate([df_actifs_enr.index,df_actifs_pilot.index,df_actifs_stockage.index])
    tous_actifs_hors_stockage = np.concatenate([df_actifs_enr.index,df_actifs_pilot.index])
    df_tous_actifs = np.array([df_actifs_enr,df_actifs_pilot,df_actifs_stockage])
    
    #### Fichier Parc
    
    chemin_parc_initial = pjoin(chemin_rep,"Parc","parc_initial.csv")
    df_parc_initial = pd.read_csv(chemin_parc_initial,sep=";",index_col=0).T

    chemin_reg_fermetures = pjoin(chemin_rep,"Parc","registre_fermetures.csv")
    df_reg_fermetures = pd.read_csv(chemin_reg_fermetures,sep=";",index_col=0).T
    df_reg_fermetures.index = np.arange(len(df_reg_fermetures.index))
    
    chemin_reg_ouvertures = pjoin(chemin_rep,"Parc","registre_ouvertures.csv")
    df_reg_ouvertures = pd.read_csv(chemin_reg_ouvertures,sep=";",index_col=0).T
    df_reg_ouvertures.index = np.arange(len(df_reg_ouvertures.index))
        
    #### Réalisation
    
    chemin_realisation = pjoin(chemin_rep,"Realisation")  

    realisation = {}
        
    rep_real = pjoin(chemin_rep,"Realisation")

    # couts combustibles 
    
    path_couts_comb = pjoin(rep_real,"couts_combustibles_et_carbone.csv")
    realisation["couts_combustibles"] = pd.read_csv(path_couts_comb,sep=";",index_col=0)
        
    nb_meteo = int(df_param_simu.at["nb_meteo","value"])
    
    for met in range(nb_meteo):
    
        realisation["meteo_%d"%met] = {}
    
        rep_meteo = pjoin(chemin_rep,"Realisation","meteo_%d"%met)
        
        # Demande
        
        path_demande = pjoin(rep_meteo,"demande.csv")
        realisation["meteo_%d"%met]["demande"] = pd.read_csv(path_demande,sep=";",index_col=0)
        
        # EnR
        
        path_fc = pjoin(rep_meteo,"facteurs_production_ENR.csv")
        realisation["meteo_%d"%met]["fc"] = pd.read_csv(path_fc,sep=";",index_col=0)

        # Dispo
            
        path_dispo = pjoin(rep_meteo,"disponibilite_pilot.csv")
        realisation["meteo_%d"%met]["dispo"] = pd.read_csv(path_dispo,sep=";",index_col=0)
                
    ################### Calculs préliminaires

    print("Calculs préliminaires")
    
    nombre_annees = int(df_param_simu.at["horizon_simulation","value"])

    parc_initial = dict()
   
    for df in df_tous_actifs :
        for tech in df.index:
            if tech in df_parc_initial.columns:
                parc_initial[tech] = df_parc_initial.at["nombre",tech]
            else : 
                parc_initial[tech] = 0        
    

    df_nb_unites_parc_reference = pd.DataFrame(index=range(nombre_annees))
    
    for df in df_tous_actifs :
        for techno in df.index :
            
            duree_vie = int(df.at[techno,"duree_vie"])

            derniere_annee = np.min([duree_vie,nombre_annees])
            
            for n in range(derniere_annee):
                df_nb_unites_parc_reference.at[n,techno] = parc_initial[techno]
                
                
            for n in range(nombre_annees):
                if techno in df_reg_ouvertures.columns:
                    if df_reg_ouvertures.at[n,techno] > 0 :
                    
                        derniere_annee = np.min([n+duree_vie,nombre_annees])
        
                        for k in range(n,derniere_annee):
                            df_nb_unites_parc_reference.at[k,techno] += df_reg_ouvertures.at[n,techno]
                            
                if techno in df_reg_fermetures.columns:
                    if df_reg_fermetures.at[n,techno] > 0 :
                    
                        for k in range(n,nombre_annees):
                            df_nb_unites_parc_reference.at[k,techno] -= df_reg_fermetures.at[n,techno]                            
                            
                            
    df_nb_unites_parc_reference = df_nb_unites_parc_reference.fillna(0)
    df_nb_unites_parc_reference = df_nb_unites_parc_reference.clip(lower=0,upper=None)
    
    ################### Realisation du GEP

    print("Ecriture du problème d'optimisation")
    
    model = pulp.LpProblem(name="GEP_problem")

    # ########### #
    # Variables   #
    # ########### #
    
    # variables nb unités
    
    nombre_unites = dict()    
    nombre_unites_ouvertes = dict()
    nombre_unites_fermees = dict()
    nombre_unites_ouverture_forcee_fermees = dict()
    nombre_unites_ouverture_forcee = dict()
    
    # variables  dispatch
    
    production = dict()   
    stock = dict()
    puissance_charge = dict()
    puissance_decharge = dict()
    defaillance = []      
    
    if type_optim == "LP":
        cat = "Continuous"
    if type_optim == "MIP":
        cat = "Integer"
    
    for techno in tous_actifs:
        nombre_unites[techno] = pulp.LpVariable.dict("nombre_unites_%s" % (techno), range(nombre_annees), lowBound=0, cat=cat)

    for techno in tous_actifs:

        nombre_unites_ouvertes[techno] = pulp.LpVariable.dict("nombre_unites_ouvertes_%s" % (techno), range(nombre_annees), lowBound=0, upBound=None, cat=cat)
        nombre_unites_fermees[techno] = pulp.LpVariable.dict("nombre_unites_fermees_%s" % (techno), range(nombre_annees), lowBound=0, cat=cat)
    
    for techno in tous_actifs:
        nombre_unites_ouverture_forcee_fermees[techno] = pulp.LpVariable.dict("nombre_unites_ouverture_forcee_fermees_%s" % (techno), range(nombre_annees), lowBound=0, cat=cat)
        nombre_unites_ouverture_forcee[techno] = pulp.LpVariable.dict("nombre_unites_ouverture_forcee_%s" % (techno), range(nombre_annees), lowBound=0, cat=cat)

    # initialisation des variables de production des actifs hors stockage

    for df in [df_actifs_enr,df_actifs_pilot]:
        for techno in df.index: 
            production_actif = []
            for annee in range(nombre_annees):
                production_actif_annee = []
                for indice_meteo in range(nb_meteo):
                    production_actif_annee_meteo = pulp.LpVariable.dict("production_%s_annee_%d_meteo_%d" % (techno, annee, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                    production_actif_annee.append(production_actif_annee_meteo)
                production_actif.append(production_actif_annee)
            production[techno] = production_actif
            
    # initialisation des variables de stock, puissance de charge et puissance de décharge des actifs de stockage
        
    for techno in df_actifs_stockage.index:
        stock_actif = []
        puissance_charge_actif = []
        puissance_decharge_actif = []
        for annee in range(nombre_annees):
            stock_actif_annee = []
            puissance_charge_actif_annee = []
            puissance_decharge_actif_annee = []
            for indice_meteo in range(nb_meteo):
                stock_actif_annee_meteo = pulp.LpVariable.dict("stock_%s_annee_%d_meteo_%d" % (techno, annee, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                puissance_charge_actif_annee_meteo = pulp.LpVariable.dict("puissance_charge_%s_annee_%d_meteo_%d" % (techno, annee, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                puissance_decharge_actif_annee_meteo = pulp.LpVariable.dict("puissance_decharge_%s_annee_%d_meteo_%d" % (techno, annee, indice_meteo), range(8760), lowBound=0, cat="Continuous")
                stock_actif_annee.append(stock_actif_annee_meteo)
                puissance_charge_actif_annee.append(puissance_charge_actif_annee_meteo)
                puissance_decharge_actif_annee.append(puissance_decharge_actif_annee_meteo)
            stock_actif.append(stock_actif_annee)
            puissance_charge_actif.append(puissance_charge_actif_annee)
            puissance_decharge_actif.append(puissance_decharge_actif_annee)
        stock[techno] = stock_actif
        puissance_charge[techno] = puissance_charge_actif
        puissance_decharge[techno] = puissance_decharge_actif
        
    # initialisation des variables de défaillance

    for annee in range(nombre_annees):
        defaillance_annee = []
        for indice_meteo in range(nb_meteo):
            defaillance_annee_meteo = pulp.LpVariable.dict("defaillance_annee_%d_meteo_%d" % (annee, indice_meteo), range(8760), lowBound=0, cat="Continuous")
            defaillance_annee.append(defaillance_annee_meteo)
        defaillance.append(defaillance_annee)

    # ################# #
    # FONCTION OBJECTIF #
    # ################# #

    print("\t Ecriture de la fonction objectif")
    
    cout_production = 0
    
    df_couts_variables = pd.DataFrame(index=range(nombre_annees))
    
    for annee in range(nombre_annees):
    
        prix_carbone = realisation["couts_combustibles"].at["cout_CO2","Annee_%d"%annee]
           
        coef_amo = 1 / (1+taux_actualisation)**annee        
        
        for indice_meteo in range(nb_meteo):
        
            coef_proba = df_param_ponderation.at[indice_meteo,"value"]
            
            for heure in range(8760):
            
                for techno in df_actifs_pilot.index:
                
                    combu = df_actifs_pilot.at[techno,"combustible"]
                    prix_combu = realisation["couts_combustibles"].at[combu,"Annee_%d"%annee]
                    rendement = df_actifs_pilot.at[techno,"rend"]                    
                    coef_emissions = df_actifs_pilot.at[techno,"emission_CO2"]
                    
                    cout_variable = (prix_combu / rendement) + (coef_emissions*prix_carbone)                    
                    df_couts_variables.at[annee,techno] = cout_variable
                    
                    cout_production += coef_proba * coef_amo* production[techno][annee][indice_meteo][heure] * cout_variable

                for techno in df_actifs_enr.index : 
                
                    cout_variable = df_actifs_enr.at[techno,"CV"]
                    coef_emissions = df_actifs_enr.at[techno,"emission_CO2"]
                    
                    cout_variable_total = cout_variable + (coef_emissions*prix_carbone)
                    df_couts_variables.at[annee,techno] = cout_variable_total
                    
                    cout_production += coef_proba * coef_amo  * cout_variable_total * production[techno][annee][indice_meteo][heure]
                    
                for techno in df_actifs_stockage.index : 
                
                    cout_variable = df_actifs_stockage.at[techno,"CV"]
                    df_couts_variables.at[annee,techno] = cout_variable
                    
                    cout_production += coef_proba * coef_amo* cout_variable* puissance_decharge[techno][annee][indice_meteo][heure] * cout_variable
                
    cout_defaillance = 0

    for annee in range(nombre_annees):
        coef_amo = 1 / (1+taux_actualisation)**annee
        
        for indice_meteo in range(nb_meteo):
        
            coef_proba = df_param_ponderation.at[indice_meteo,"value"]
            
            for heure in range(8760):
            
                cout_defaillance += coef_amo * coef_proba* float(df_param_simu.at["VOLL","value"]) * defaillance[annee][indice_meteo][heure]
                
                
    cout_construction = 0

    for annee in range(nombre_annees):
        coef_amo = 1 / (1+taux_actualisation)**annee
        
        for df in df_tous_actifs :
            for techno in df.index:
                
                

                capex_total = df.at[techno,"CC_MW"]
                
                
                taux_actu = df.at[techno,"taux_actu"]
                duree_vie = df.at[techno,"duree_vie"]
                
                annuite_per_mw = capex_total *  taux_actu / (1-(1+taux_actu)**(-duree_vie)) / (1+taux_actu)
                
                if "Pnom" in df.columns:
                    puissance = df.at[techno,"Pnom"]
                else :
                    puissance = df.at[techno,"puissance"]
                    
                annuite_unite = annuite_per_mw * puissance
                                      
                cout_construction += annuite_unite * coef_amo * sum([1 / (1 + taux_actualisation) ** annee_future for annee_future in range(min(duree_vie, nombre_annees - annee))]) * nombre_unites_ouvertes[techno][annee]
    
    cout_maintenance = 0
    
    for annee in range(nombre_annees):
    
        coef_amo = 1 / (1+taux_actualisation)**annee
        
        for df in df_tous_actifs :
            for techno in df.index:

                cf_mw = df.at[techno,"CF_MW"]
                
                if "Pnom" in df.columns:
                    puissance = df.at[techno,"Pnom"]
                else :
                    puissance = df.at[techno,"puissance"]
                    
                    
                cf_unite = cf_mw * puissance
                
                cout_maintenance += coef_amo * nombre_unites[techno][annee]  * cf_unite
            
            
    cout_total = pulp.lpSum([cout_production,cout_defaillance,cout_construction, cout_maintenance])
    
    model.setObjective(cout_total)


    # ########### #
    # Contraintes #
    # ########### #
        

    print("\t Ecriture des contraintes")
    
    # contraintes d'évolution du nombre d'unités
    for techno in tous_actifs :
        nombre_unites_actif = nombre_unites[techno]
        nombre_unites_ouvertes_actif = nombre_unites_ouvertes[techno]
        nombre_unites_fermees_actif = nombre_unites_fermees[techno]
        for annee in range(nombre_annees):
            if annee == 0:
                # à l'année 0, les unités du parc initial sont ajoutées
                contrainte = pulp.LpConstraint(
                    e=nombre_unites_actif[annee] - nombre_unites_ouvertes_actif[annee] + nombre_unites_fermees_actif[annee],
                    sense=pulp.LpConstraintEQ,
                    rhs=parc_initial[techno],
                    name="evolution_nombre_unites_%s_%d" % (techno, annee)
                )
                model.addConstraint(contrainte)

            else:
                contrainte = pulp.LpConstraint(
                    e=nombre_unites_actif[annee] - nombre_unites_actif[annee - 1] - nombre_unites_ouvertes_actif[annee] + nombre_unites_fermees_actif[annee],
                    sense=pulp.LpConstraintEQ,
                    rhs=0,
                    name="evolution_nombre_unites_%s_%d" % (techno, annee)
                )
                model.addConstraint(contrainte)



    # contraintes de trajectoire CO2
    
    liste_contrainte_CO2 = {}
    
    for annee in range(nombre_annees):

        quota = df_quota.at["Annee_"+str(annee),"CO2_quota"]
        
        if quota < np.inf :
        
            somme_emissions = 0       
            
            for indice_meteo in range(nb_meteo):
            
                coef_proba = df_param_ponderation.at[indice_meteo,"value"]
                
                for techno in df_actifs_pilot.index:
                    coef_emissions = df_actifs_pilot.at[techno,"emission_CO2"]
                    somme_emissions += pulp.lpSum([coef_proba*production[techno][annee][indice_meteo][heure]*coef_emissions for heure in range(8760)])
                    
            contrainte = pulp.LpConstraint(
                e=somme_emissions,
                sense=pulp.LpConstraintLE,
                rhs=quota,
                name="contrainte_co2_annee_%s_meteo_%s" % (str(annee),str(indice_meteo))
                )
            
            model.addConstraint(contrainte)
            liste_contrainte_CO2[annee] = contrainte

        else :
            continue
            
    # contraintes de trajectoire imposées par l'utilisateur
    dict_contraintes_personnalisees = dict()
    
    for nom_contrainte in df_contraintes.columns:

        liste_contraintes_personnalisees_annuelles = []

        sens_contrainte = None

        if df_contraintes.at["type_contrainte",nom_contrainte] == "egalite":
            sens_contrainte = pulp.LpConstraintEQ
        elif df_contraintes.at["type_contrainte",nom_contrainte] == "borne_inferieure":
            sens_contrainte = pulp.LpConstraintGE
        elif df_contraintes.at["type_contrainte",nom_contrainte] == "borne_superieure":
            sens_contrainte = pulp.LpConstraintLE

        for annee in range(nombre_annees):
            
            techno = df_contraintes.at["actifs_concernes",nom_contrainte]

            nombre_unites_actif_annee = nombre_unites[techno][annee]

            second_membre = int(df_contraintes.at["annee_%d"%annee,nom_contrainte])
            
            contrainte = pulp.LpConstraint(
                e= nombre_unites_actif_annee ,
                sense=sens_contrainte,
                rhs=second_membre,
                name="contrainte_trajectoire_%d_annee_%d" % (nom_contrainte, annee)
            )
            
            model.addConstraint(contrainte)
            liste_contraintes_personnalisees_annuelles.append(contrainte)
            
        dict_contraintes_personnalisees[nom_contrainte] = liste_contraintes_personnalisees_annuelles
        
    # contraintes de satisfaction de la demande
    
    contraintes_satisfaction_demande = []
    for annee in range(nombre_annees):
        contraintes_satisfaction_demande_annee = []
        for indice_meteo in range(nb_meteo):
            contraintes_satisfaction_demande_annee_meteo = []
            
            for heure in range(8760):
                somme_productions = pulp.lpSum([production[techno][annee][indice_meteo][heure] for techno in tous_actifs_hors_stockage])
                somme_puissances_charge = pulp.lpSum([puissance_charge[techno][annee][indice_meteo][heure] for techno in df_actifs_stockage.index])
                somme_puissances_decharge = pulp.lpSum([puissance_decharge[techno][annee][indice_meteo][heure] for techno in df_actifs_stockage.index])
                
                demande = realisation["meteo_%d"%indice_meteo]["demande"].at[heure,"Annee_%d"%annee]

                defaillance_var = defaillance[annee][indice_meteo][heure]
                
                contrainte = pulp.LpConstraint(
                    e=somme_productions - somme_puissances_charge + somme_puissances_decharge + defaillance_var,
                    sense=pulp.LpConstraintEQ,
                    rhs=demande,
                    name="satisfaction_demande_annee_%d_meteo_%d_heure_%d" % (annee, indice_meteo, heure)
                )
                model.addConstraint(contrainte)
                contraintes_satisfaction_demande_annee_meteo.append(contrainte)
            contraintes_satisfaction_demande_annee.append(contraintes_satisfaction_demande_annee_meteo)
        contraintes_satisfaction_demande.append(contraintes_satisfaction_demande_annee)

    # contraintes de continuité du stock
    
    for actif_stockage in df_actifs_stockage.index:
        stock_actif = stock[actif_stockage]
        puissance_decharge_actif = puissance_decharge[actif_stockage]
        puissance_charge_actif = puissance_charge[actif_stockage]
        for annee in range(nombre_annees):
            for indice_meteo in range(nb_meteo):
                for heure in range(8760):
                    stock_var = stock_actif[annee][indice_meteo][heure]
                    stock_suivant_var = stock_actif[annee][indice_meteo][(heure+1)%8760]
                    puissance_charge_var = puissance_charge_actif[annee][indice_meteo][heure]
                    puissance_decharge_var = puissance_decharge_actif[annee][indice_meteo][heure]
                    
                    rendement_charge = df_actifs_stockage.at[actif_stockage,"rend_ch"]
                    rendement_decharge = df_actifs_stockage.at[actif_stockage,"rend_dech"]      
                    
                    contrainte = pulp.LpConstraint(
                        e= stock_suivant_var - stock_var + puissance_decharge_var * 1 / rendement_decharge  - puissance_charge_var * rendement_charge,
                        sense=pulp.LpConstraintEQ,
                        rhs=0,
                        name="continuite_stock_%s_annee_%d_meteo_%d_heure_%d" % (actif_stockage, annee, indice_meteo, heure)
                    )
                    model.addConstraint(contrainte)

    # contrainte de borne supérieure sur la production
    
    for actif in tous_actifs_hors_stockage:
        production_actif = production[actif]
        nombre_unites_actif = nombre_unites[actif]
        for annee in range(nombre_annees):
            for indice_meteo in range(nb_meteo):
                for heure in range(8760):
                    production_var = production_actif[annee][indice_meteo][heure]
                    borne_superieure_production = None
                    if actif in df_actifs_enr.index:
                        puissance = float(df_actifs_enr.at[actif,"Pnom"])
                        fc = realisation["meteo_%d"%indice_meteo]["fc"].at[heure,"%s_%d"%(actif,annee)]
                        borne_superieure_production = nombre_unites_actif[annee] * puissance * fc
                    else:
                        puissance = float(df_actifs_pilot.at[actif,"Pnom"])
                        dispo = realisation["meteo_%d"%indice_meteo]["dispo"].at[heure,"%s_%d"%(actif,annee)]
                        borne_superieure_production = nombre_unites_actif[annee] * puissance * dispo
                        
                    contrainte = pulp.LpConstraint(
                        e=borne_superieure_production - production_var,
                        sense=pulp.LpConstraintGE,
                        rhs=0,
                        name="borne_superieure_production_%s_annee_%d_meteo_%d_heure_%d" % (actif, annee, indice_meteo, heure)
                    )
                    model.addConstraint(contrainte)

    # contraintes de bornes supérieures sur le stock, la puissance de charge et la puissance de décharge
    
    for actif_stockage in df_actifs_stockage.index:
        stock_actif = stock[actif_stockage]
        puissance_charge_actif = puissance_charge[actif_stockage]
        puissance_decharge_actif = puissance_decharge[actif_stockage]

        nombre_unites_actif = nombre_unites[actif_stockage]
        
        for annee in range(nombre_annees):
            borne_superieure_stock = nombre_unites_actif[annee] * df_actifs_stockage.at[actif_stockage,"stock_max_MWh"]
            borne_superieure_puissance_charge = nombre_unites_actif[annee] * df_actifs_stockage.at[actif_stockage,"puissance"]
            borne_superieure_puissance_decharge = nombre_unites_actif[annee] * df_actifs_stockage.at[actif_stockage,"puissance"]

            for indice_meteo in range(nb_meteo):
                for heure in range(8760):
                    stock_var = stock_actif[annee][indice_meteo][heure]
                    puissance_charge_var = puissance_charge_actif[annee][indice_meteo][heure]
                    puissance_decharge_var = puissance_decharge_actif[annee][indice_meteo][heure]

                    contrainte = pulp.LpConstraint(
                        e=borne_superieure_stock - stock_var,
                        sense=pulp.LpConstraintGE,
                        rhs=0,
                        name="borne_superieure_stock_%s_annee_%d_meteo_%d_heure_%d" % (actif_stockage, annee, indice_meteo, heure)
                    )
                    model.addConstraint(contrainte)

                    contrainte = pulp.LpConstraint(
                        e=borne_superieure_puissance_charge - puissance_charge_var,
                        sense=pulp.LpConstraintGE,
                        rhs=0,
                        name="borne_superieure_puissance_charge_%s_annee_%d_meteo_%d_heure_%d" % (actif_stockage, annee, indice_meteo, heure)
                    )
                    model.addConstraint(contrainte)

                    contrainte = pulp.LpConstraint(
                        e=borne_superieure_puissance_decharge - puissance_decharge_var,
                        sense=pulp.LpConstraintGE,
                        rhs=0,
                        name="borne_superieure_puissance_decharge_%s_annee_%d_meteo_%d_heure_%d" % (actif_stockage, annee, indice_meteo, heure)
                    )
                    model.addConstraint(contrainte)


    # contraintes imposant que les actifs ne dépassent pas leur durée de vie
    for df in df_tous_actifs:
        for techno in df.index : 
            duree_vie = df.at[techno,"duree_vie"]
            nombre_unites_actif = nombre_unites[techno]
            nombre_unites_fermees_actif = nombre_unites_fermees[techno]
            for annee in range(max(0, nombre_annees - duree_vie)):
                # on impose que pour chaque année considérée, le nombre d'unités actives soit inférieur ou égal
                # au nombre de fermetures ayant lieu dans la période  équivalente à une durée de vie qui la suit
                # ce qui revient à s'assurer que chaque unité active peut se voir associer une fermeture sans dépasser
                # cette durée
                contrainte = pulp.LpConstraint(
                    e= pulp.lpSum([nombre_unites_fermees_actif[annee_future] for annee_future in range(annee, annee + duree_vie + 1)]) - nombre_unites_actif[annee],
                    sense=pulp.LpConstraintGE,
                    rhs=0,
                    name="non-depassement_duree_vie_%s_%d" % (techno, annee)
                )
                model.addConstraint(contrainte)


    # contraintes d'ouvertures forcées et de fermetures programmées initialement
    
     
    
    for df in df_tous_actifs:
        for actif in df.index : 
            
            nombre_unites_ouverture_forcee_actif_reference = np.zeros(nombre_annees, dtype=int)
            for annee in range(nombre_annees):
                nombre_unites_ouverture_forcee_actif_reference[annee] = df_nb_unites_parc_reference.at[annee,actif]

            nombre_unites_ouverture_forcee_ouvertes_actif = np.zeros(nombre_annees, dtype=int)
            for annee in range(nombre_annees):
                nombre_unites_ouverture_forcee_ouvertes_actif[annee] = df_reg_ouvertures.at[annee,actif]

                    
            # recuperation des variables PuLP        

            nombre_unites_actif = nombre_unites[actif]
            nombre_unites_ouvertes_actif = nombre_unites_ouvertes[actif]
            nombre_unites_fermees_actif = nombre_unites_fermees[actif]

            nombre_unites_ouverture_forcee_actif = nombre_unites_ouverture_forcee[actif]
            nombre_unites_ouverture_forcee_fermees_actif = nombre_unites_ouverture_forcee_fermees[actif]

            for annee in range(nombre_annees):
                # contraintes analogues à celles pour l'évolution du nombre d'unités
                if annee == 0:
                    # à l'année 0, les unités du parc initial sont ajoutées
                    contrainte = pulp.LpConstraint(
                        e=nombre_unites_ouverture_forcee_actif[annee] + nombre_unites_ouverture_forcee_fermees_actif[annee],
                        sense=pulp.LpConstraintEQ,
                        rhs=parc_initial[actif],
                        name="evolution_nombre_unites_ouverture_forcee_%s_%d" % (actif, annee)
                    )
                    model.addConstraint(contrainte)
                else:
                    contrainte = pulp.LpConstraint(
                        e=nombre_unites_ouverture_forcee_actif[annee] - nombre_unites_ouverture_forcee_actif[annee - 1] + nombre_unites_ouverture_forcee_fermees_actif[annee],
                        sense=pulp.LpConstraintEQ,
                        rhs=nombre_unites_ouverture_forcee_ouvertes_actif[annee],
                        name="evolution_nombre_unites_ouverture_forcee_%s_%d" % (actif, annee)
                    )
                    model.addConstraint(contrainte)

                # le nombre d'unités dont l'ouverture est forcée doit être inférieur à la trajectoire de référence
                # car on n'autorise pas à dépasser la date de fermeture programmée
                # en revanche on autorise à fermer les unités avant la date prévue
                nombre_unites_ouverture_forcee_actif[annee].bounds(0, nombre_unites_ouverture_forcee_actif_reference[annee])

                if df.at[actif,"ajoutable"] :
                
                    # le nombre d'ouvertures total est supérieur au nombre d'ouvertures d'unités dont l'ouverture est
                    # forcée, sauf pour l'année 0 où les unités dont l'ouverture est forcée constituent le parc initial
                    contrainte = pulp.LpConstraint(
                        e=nombre_unites_ouvertes_actif[annee],
                        sense=pulp.LpConstraintGE,
                        rhs=nombre_unites_ouverture_forcee_ouvertes_actif[annee],
                        name="borne_nombre_unites_ouvertes_%s_%d" % (actif, annee)
                    )
                    model.addConstraint(contrainte)
                    
                else : 
                
                     # le nombre d'ouvertures total est supérieur au nombre d'ouvertures d'unités dont l'ouverture est
                    # forcée, sauf pour l'année 0 où les unités dont l'ouverture est forcée constituent le parc initial
                    contrainte = pulp.LpConstraint(
                        e=nombre_unites_ouvertes_actif[annee],
                        sense=pulp.LpConstraintEQ,
                        rhs=nombre_unites_ouverture_forcee_ouvertes_actif[annee],
                        name="borne_nombre_unites_ouvertes_%s_%d" % (actif, annee)
                    )
                    model.addConstraint(contrainte)           

                # le nombre de fermetures total est supérieur au nombre de fermetures d'unités dont l'ouverture est
                # forcée
                
                
                contrainte = pulp.LpConstraint(
                    e=nombre_unites_fermees_actif[annee] - nombre_unites_ouverture_forcee_fermees_actif[annee],
                    sense=pulp.LpConstraintGE,
                    rhs=0,
                    name="borne_nombre_unites_fermees_%s_%d" % (actif, annee)
                )
                model.addConstraint(contrainte)
          
    # contraintes actif ajoutable
    
    # for df in df_tous_actifs:
        # for techno in df.index : 
            # if not df.at[techno,"ajoutable"] :
                
                # nombre_unites_ouvertes_actif = nombre_unites_ouvertes[techno]
            
                # for annee in range(nombre_annees):
                
                    # contrainte = pulp.LpConstraint(
                        # e=nombre_unites_ouvertes_actif[annee],
                        # sense=pulp.LpConstraintEQ,
                        # rhs=0,
                        # name="Actif_non_ajoutable_%s_%d" % (techno, annee)
                    # )
                    # model.addConstraint(contrainte)                
                    

    # ########### #
    # Resolution  #
    # ########### #

    print("Resolution du problème")
    
    log_path = os.path.join(chemin_sorties,"log.txt")

    solver = pulp.CPLEX_CMD(path="/opt/cplex/12.8/cplex/bin/x86-64_linux/cplex")
    
    path_lp = os.path.join(chemin_sorties,"lp.lp")    

    model.writeLP(path_lp)
    model.setSolver(solver)
    model.solve()
    
    print("status : ", pulp.LpStatus[model.status])   
    
    if not(model.status == 1):
        print("/!\\ /!\\ LE PROBLEME N'A PAS PU ETRE RESOLU CORRECTEMENT /!\\ /!\\")
        sys.exit()

    # ##################### #
    # Ecriture des sorties  #
    # ##################### #
    
    print("Ecriture des sorties")   
    
    #### Sortie dispatch
    
    dict_dispatch = {}
    
    for annee in range(nombre_annees):
        dict_dispatch[annee] = {}
        coef_amo = 1 / (1+taux_actualisation)**annee      
        for indice_meteo in range(nb_meteo):
        
            coef_proba = df_param_ponderation.at[indice_meteo,"value"]
                
            df_dispatch = pd.DataFrame(index=range(8760))
            
            for heure in range(8760):
            
                for techno in tous_actifs_hors_stockage :
                    df_dispatch.at[heure,"production_"+techno] = production[techno][annee][indice_meteo][heure].value()
                        
                for techno in df_actifs_enr.index : 
                
                    nb_unite = nombre_unites[techno][annee].value()
                    puissance = float(df_actifs_enr.at[techno,"Pnom"])
                    productible = realisation["meteo_%d"%indice_meteo]["fc"].at[heure,"%s_%d"%(techno,annee)] * nb_unite *  puissance                
               
                    df_dispatch.at[heure,"ecretement_"+techno] = productible - production[techno][annee][indice_meteo][heure].value()
                                    
                    
                for techno in df_actifs_stockage.index : 

                    df_dispatch.at[heure,"decharge_"+techno] = puissance_decharge[techno][annee][indice_meteo][heure].value()

                        
                df_dispatch.at[heure,"defaillance"] = defaillance[annee][indice_meteo][heure].value()
                df_dispatch.at[heure,"demande"] = realisation["meteo_%d"%indice_meteo]["demande"].at[heure,"Annee_%d"%annee]
                df_dispatch.at[heure,"cout_marginal"] = contraintes_satisfaction_demande[annee][indice_meteo][heure].pi /(coef_amo*coef_proba)
                
                for techno in df_actifs_stockage.index : 
                    df_dispatch.at[heure,"charge_"+techno] = puissance_charge[techno][annee][indice_meteo][heure].value()
                    df_dispatch.at[heure,"stock_"+techno] = stock[techno][annee][indice_meteo][heure].value()
                                
            chemin_dispatch = pjoin(chemin_sorties,"dispatch_annee_%d_meteo_%d.csv"%(annee,indice_meteo))
            df_dispatch.to_csv(chemin_dispatch,sep=";")
            
            dict_dispatch[annee][indice_meteo] = df_dispatch
                  
    # sorties annuelles      

    
    xls_output = pjoin(chemin_sorties,"sorties_annuelles.xlsx")
    
    with pd.ExcelWriter(xls_output) as writer:  

        # nb unites

        dict_nb_unites = {"nb_unites":nombre_unites,
                            "nb_unites_ouvertes":nombre_unites_ouvertes,
                            "nb_unites_fermees":nombre_unites_fermees,
                            "nb_unites_forcee_fermee":nombre_unites_ouverture_forcee_fermees,
                            "nb_unites_forcees":nombre_unites_ouverture_forcee}

        
        for nom_nb_unite in dict_nb_unites:
        
            df_nb_unites = pd.DataFrame(index=range(nombre_annees))
            
            nb_unite = dict_nb_unites[nom_nb_unite]
                
            for annee in range(nombre_annees):
                for techno in tous_actifs :
                    df_nb_unites.at[annee,techno] = nb_unite[techno][annee].value()
                    
            df_nb_unites.to_excel(writer, sheet_name=nom_nb_unite)

        # capa
        
        df_capa = pd.DataFrame(index=range(nombre_annees))
            
        for df in df_tous_actifs: 
            for annee in range(nombre_annees):
                for techno in df.index :
                    if "Pnom" in df.columns:
                        puissance = df.at[techno,"Pnom"]
                    else :
                        puissance = df.at[techno,"puissance"]
                    df_capa.at[annee,"puissance_installee_"+techno] = puissance*nombre_unites[techno][annee].value()
                    
        df_capa.to_excel(writer, sheet_name="capa")
        
        # carbon shadow price

        df_dual_variables = pd.DataFrame(index=range(nombre_annees))
        
        
        for annee in range(nombre_annees) :
            if annee in liste_contrainte_CO2:
                df_dual_variables.at[annee,"carbon_shadow_price"] = -1 * liste_contrainte_CO2[annee].pi / (1+taux_actualisation)**(-annee)
            else : 
                df_dual_variables.at[annee,"carbon_shadow_price"] = 0
                
        df_dual_variables.to_excel(writer, sheet_name="carbon shadow price")

        # cout_variables
        
        df_couts_variables.to_excel(writer, sheet_name="cout variable")


        # indicateurs
        
        df_indicateurs = pd.DataFrame(index=range(nombre_annees))
        
        for annee in range(nombre_annees):  

            df_indicateurs.at[annee,"defaillance"] = 0
            df_indicateurs.at[annee,"LOLE"] = 0
            df_indicateurs.at[annee,"cout_marginal"] = 0
            
            for indice_meteo in range(nb_meteo):

                coef_proba = df_param_ponderation.at[indice_meteo,"value"]
                dispatch = dict_dispatch[annee][indice_meteo]
                
                # defaillance

                df_indicateurs.at[annee,"defaillance"] += coef_proba *  dispatch["defaillance"].sum()
                
                # lole
                
                cond_1 = dispatch["defaillance"] > 0 
                lole = len(dispatch[cond_1].index)
                
                df_indicateurs.at[annee,"LOLE"] += coef_proba * lole
                
                # cout marginal
                
                df_indicateurs.at[annee,"cout_marginal"] += coef_proba *  dispatch["cout_marginal"].mean()                
                
        df_indicateurs.to_excel(writer, sheet_name="indicateurs")
                  


    return df_reg_ouvertures, df_reg_fermetures