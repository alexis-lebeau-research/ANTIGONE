# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import os
import sys
import copy

import numpy as np
import pandas as pd

import IndicateursEconomiques
import Anticipation
import DonneesSimulation
import Ecriture
import Lecture
import statistics as stat


def calcul_VAN_equivalente(donnees_entree,donnees_simulation,actif,annee_ouverture,annee_fin_calcul_VAN,matrice_resultats_annuels):

    print("calcul VAN equivalente")

    matrice_resultats_annuels = np.array(matrice_resultats_annuels)
    annee_courante =  donnees_simulation.annee_courante    
    annee_debut_anticipation = annee_ouverture
    nb_meteo = donnees_entree.parametres_simulation.nb_meteo
    nbAnnee_calcul_VAN = annee_fin_calcul_VAN - annee_ouverture
    df_ponderation = donnees_entree.df_parametres_ponderation
    
    if actif.categorie == "Pilotable":
        puissance =  actif.puissance_nominale
    elif actif.categorie == "ENR":
        puissance =  actif.puissance_reference
    elif actif.categorie == "Stockage":
        puissance =   actif.puissance_nominale_decharge
                       
    ### Debut du calcul de la matrice des revenus annuels
    
    revenus_par_amb = {}
      
    for idx_amb,amb in enumerate(donnees_entree.ambiances) :
    

        resultats_annuels_ambiance = matrice_resultats_annuels[idx_amb]
        
        idx_annee_debut = annee_ouverture - annee_debut_anticipation           
        idx_annee_fin = annee_fin_calcul_VAN - annee_debut_anticipation
        
        revenus_par_annee = np.full(nbAnnee_calcul_VAN,0)

        for idx_n,n in enumerate(range(idx_annee_debut,idx_annee_fin)):
                    
            annee = annee_debut_anticipation + n        


            if(annee - annee_debut_anticipation < len(resultats_annuels_ambiance)):

                resultats_annuels_ambiance_annee = resultats_annuels_ambiance[annee - annee_debut_anticipation]
                annee_donnees = annee
                
            else : 
                resultats_annuels_ambiance_annee = resultats_annuels_ambiance[-1]
                annee_donnees = annee_debut_anticipation + len(resultats_annuels_ambiance) - 1
                
            
            revenus_par_meteo = np.full(nb_meteo,0)
            
            for indice_meteo in range(nb_meteo):
                         
                resultat_annuel  = resultats_annuels_ambiance_annee[indice_meteo]

                
                cout_variable_actif = resultat_annuel.df_cv.at[actif.cle,"CV"]
      
                nb_unite = resultat_annuel.compte_unites[actif.cle]
                
                revenus_par_meteo[indice_meteo] = np.sum((resultat_annuel.cout_marginal - cout_variable_actif) * resultat_annuel.production[actif.cle] / (nb_unite*puissance)) 
                
                if actif.categorie == "Stockage":
                    revenus_par_meteo[indice_meteo] -=  np.sum(resultat_annuel.cout_marginal * resultat_annuel.charge[actif.cle]/(nb_unite*puissance))
                    
                    

             
            
            ##### Neutralité au risque
            
            risk_aversion_st = donnees_entree.parametres_simulation.risk_aversion_st
            
            if not risk_aversion_st:
                moyenne_revenus = (revenus_par_meteo*df_ponderation["value"].values).sum()

                taux_actualisation = actif.taux_actualisation
                facteur_actu = (1+taux_actualisation)**(-(annee - annee_courante))
                
                revenus_par_annee[idx_n] = facteur_actu * moyenne_revenus

            
            ##### Averse au risque
            
            else:

                alpha = donnees_entree.parametres_simulation.coefficient_risque
                
                mu = (revenus_par_meteo*df_ponderation["value"].values).sum()
    
                utilite_revenus = 1 -np.exp( -alpha * revenus_par_meteo / mu)
                
                esp_utilite = (utilite_revenus *df_ponderation["value"].values).sum()
                
                equivalent_certain = -np.log(1-esp_utilite)*mu/alpha

                taux_actualisation = actif.taux_actualisation
                facteur_actu = (1+taux_actualisation)**(-(annee - annee_courante))
                
                revenus_par_annee[idx_n] = facteur_actu * equivalent_certain
                    

        revenus_par_amb[amb] =    revenus_par_annee
    
    ### Fin du calcul de la matrice des revenus annuels

    taux_actualisation = actif.taux_actualisation
        
        
    # Calcul du volume de CAPEX à prendre en compte
    
   
    annuite = IndicateursEconomiques.calcul_investissement_IDC_annualise(actif,annee_courante) / puissance
    
    investissement_initial =  np.array([ annuite* (1+taux_actualisation)**(-n) for n in range(nbAnnee_calcul_VAN)]).sum() 

    # Calcul du volume de fixed OPEX à prendre en compte
    
    cout_fixe_MW = actif.cout_fixe_maintenance /  puissance  
    couts_fom =  np.array([ cout_fixe_MW* (1+taux_actualisation)**(-n) for n in range(nbAnnee_calcul_VAN)]).sum() 
            
    # Calcul des VAN possibles dans les différentes ambiances / météos
    
    liste_VAN_possibles_avec_CAPEX = []
    liste_VAN_possibles_sans_CAPEX = []           
    liste_revenus_possibles = []        
    
    for idx_amb,amb in enumerate(donnees_entree.ambiances) :
           
        VAN_avec_CAPEX = revenus_par_amb[amb].sum() - investissement_initial - couts_fom
        VAN_sans_CAPEX = revenus_par_amb[amb].sum() - couts_fom
        revenus = revenus_par_amb[amb].sum()
               
        liste_VAN_possibles_avec_CAPEX.append(VAN_avec_CAPEX)
        liste_VAN_possibles_sans_CAPEX.append(VAN_sans_CAPEX)
        liste_revenus_possibles.append(revenus)
    
    # Calcul de la VAN equivalente
    
    parametre_VAN_equivalente = donnees_entree.parametres_simulation.VAN_equivalente
    
    VAN_equivalente_avec_CAPEX = 0
    VAN_equivalente_sans_CAPEX = 0
    revenus_equivalents = 0
    
    if parametre_VAN_equivalente == "moyenne":


        if not donnees_entree.parametres_simulation.risk_aversion_lt : 
            revenus_equivalents = stat.mean(liste_revenus_possibles)
        else : 

            moyenne = stat.mean(liste_revenus_possibles)

            alpha = donnees_entree.parametres_simulation.coefficient_risque
            width = donnees_entree.parametres_simulation.width_lt_uncertainty
            
            a = moyenne - (width*moyenne)/2
            b = moyenne + (width*moyenne)/2
            
            #esp_utilite = 1 + (1/(2*alpha))*(np.exp(-2*alpha)-1)
            

            esp_utilite = 1 - ( np.exp(-alpha*b/moyenne)  - np.exp(-alpha*a/moyenne)    ) / ( - alpha*(b-a) / moyenne )  

            revenus_equivalents = -(moyenne/alpha)*np.log(1-esp_utilite)


        VAN_equivalente_avec_CAPEX = revenus_equivalents - investissement_initial - couts_fom
        VAN_equivalente_sans_CAPEX = revenus_equivalents - couts_fom
        

        
    elif parametre_VAN_equivalente == "mediane":
        VAN_equivalente_avec_CAPEX = stat.median(liste_VAN_possibles_avec_CAPEX)
        VAN_equivalente_sans_CAPEX = stat.median(liste_VAN_possibles_sans_CAPEX)
    elif parametre_VAN_equivalente == "minimum":
        VAN_equivalente_avec_CAPEX = min(liste_VAN_possibles_avec_CAPEX)
        VAN_equivalente_sans_CAPEX = min(liste_VAN_possibles_sans_CAPEX)
    elif parametre_VAN_equivalente == "maximum":
        VAN_equivalente_avec_CAPEX = max(liste_VAN_possibles_avec_CAPEX)
        VAN_equivalente_sans_CAPEX = max(liste_VAN_possibles_sans_CAPEX)
    elif parametre_VAN_equivalente == "quantile":
        VAN_equivalente_avec_CAPEX = np.quantile(liste_VAN_possibles_avec_CAPEX, donnees_entree.parametres_simulation.quantile_meteo)
        VAN_equivalente_sans_CAPEX = np.quantile(liste_VAN_possibles_sans_CAPEX, donnees_entree.parametres_simulation.quantile_meteo)
        

    dict_VAN_equivalente = {}
    dict_VAN_equivalente["VAN_avec_capex"] = VAN_equivalente_avec_CAPEX
    dict_VAN_equivalente["VAN_sans_capex"] = VAN_equivalente_sans_CAPEX
    dict_VAN_equivalente["revenus"] = revenus_equivalents
    dict_VAN_equivalente["couts_fixes_totaux"] = couts_fom+investissement_initial
    dict_VAN_equivalente["couts_fom"] = couts_fom
    
    dict_VAN_possibles = {}
    dict_VAN_possibles["VAN_possibles_avec_capex"] = liste_VAN_possibles_avec_CAPEX
    dict_VAN_possibles["VAN_possibles_sans_capex"] = liste_VAN_possibles_sans_CAPEX
    
    return dict_VAN_equivalente, dict_VAN_possibles
    
    
def sequence_merchant_decisions(donnees_entree, donnees_simulation):


    annee_courante = donnees_simulation.annee_courante    
    horizon_prevision = donnees_entree.parametres_simulation.horizon_prevision
    idx_fin = (donnees_entree.parametres_simulation.horizon_simulation-1)        
    
    #### On sauvegarde la liste des unités présentes initialement dans le parc 
    
    unites_initialement_presentes = {}
    
    for actif in donnees_entree.tous_actifs():
        cle = actif.cle
        unites_initialement_presentes[cle] = donnees_simulation.parc.unites_actives(cle, annee_courante)

    # on stocke dans un dataframe les unites qui seront demantelees
    # et qui etaient dans le parc initial -> on pourra potentiellement les "re-investir"
    # en ne payant que l'OPEX fixe au cours des itérations
    
    df_unite_deco = pd.DataFrame()

    # on stocke dans un dataframe les unites qui seront investies mais non presentes dans le parc initial
    # de sorte a pouvoir les demanteler et economiser les CAPEX
    
    df_unite_invest = pd.DataFrame()        


    dict_etats_parc = {}
    dict_etats_parc["initial"] = [ donnees_simulation.parc.nombre_unites(actif.cle,annee_courante) for actif in donnees_entree.tous_actifs() ]


    ### Avant de commencer les boucles d'investissements, on prépare le parc anticipé si cette option est activée
      
      

    if donnees_entree.parametres_simulation.anticipation_parc_exogene :       
        dico_parcs_anticipes_boucle = donnees_simulation.dico_parcs_anticipes


    
    #### Boucle    
    
      
    continuer = True
    liste_rapports_investissement = []
    liste_rapports_demantelement = []
    indice_boucle = 0

    while (continuer):
    
        print("\t Boucle merchant module %d " % indice_boucle)

        resume_decision = pd.DataFrame()
        
        
        ######## parc reel
           
        df_nb_unites_parc_reel = donnees_simulation.parc.get_df_nb_unites().loc[0:idx_fin]
        
        nom_fic = "DF_PR_MerchantModule_%s_%s.csv"%(str(annee_courante),str(indice_boucle))    
        path_df_parc_reel = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
        df_nb_unites_parc_reel.to_csv(path_df_parc_reel,sep=";")
        
        ######## parc anticipe

        if donnees_entree.parametres_simulation.anticipation_parc_exogene : 
    
            dico_df_nb_unites_ambiances = donnees_entree.mise_en_coherence_parc(annee_courante,
                                                                                dico_parcs_anticipes_boucle,
                                                                                donnees_simulation.parc,
                                                                                add_current_investment=False,
                                                                                add_current_divestment=False)
                                                                                
        else : 
        
            df_nb_unites = df_nb_unites_parc_reel.copy()
            
            dico_df_nb_unites_ambiances = {}
            
            for ambiance in donnees_entree.ambiances :
            

                if donnees_entree.parametres_simulation.extrapolation_capa :
                
                    nb_annee_extrapolation =  donnees_entree.parametres_simulation.nb_annee_extrapolation_capa
                    
                    dico_df_nb_unites_ambiances[ambiance] = donnees_simulation.parc.get_df_nb_unites_extrapole(annee_courante,nb_annee_extrapolation)
                    
                else :
                    dico_df_nb_unites_ambiances[ambiance] = df_nb_unites.copy()
                                                                                
                                                                                
        for nom_amb in donnees_entree.ambiances :
                 
            nom_fic = "DF_PA_%s_MerchantModule_%s_%s.csv"%(nom_amb,str(annee_courante),str(indice_boucle))    
            path_df_parc_anticipe = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
            dico_df_nb_unites_ambiances[nom_amb].to_csv(path_df_parc_anticipe,sep=";")
                    
                                
        ######## evaluation des investissements potentiels
        
        actifs_a_tester_pour_ajout = [actif for actif in donnees_entree.tous_actifs() if actif.ajoutable  ]
  
        dict_VAN_equivalentes_avec_CAPEX = dict()
        dict_VAN_equivalentes_sans_CAPEX = dict()
        
        VAN_max_ajout = 0
        actif_candidat_ajout = None
        unite_repechee = None
                
        resume_market_module_invest = pd.DataFrame()
        id_option_invest = 0        

        for actif in actifs_a_tester_pour_ajout :
        
            print("\t\t\t Evaluation : %s"%(actif.cle))
                
            annee_ouverture = annee_courante + actif.duree_construction
            annee_fermeture = annee_ouverture + actif.duree_vie 

            annee_debut_anticipation = annee_ouverture
            annee_fin_anticipation = min(annee_courante + donnees_entree.parametres_simulation.horizon_prevision,
                                            annee_fermeture,
                                            donnees_entree.parametres_simulation.horizon_simulation)

            # preparation du parc pour le test
                                        
            dico_nb_unites_ambiances_test = {}

            for nom_amb in donnees_entree.ambiances :

                
                df_nb_unites_ambiances_test = dico_df_nb_unites_ambiances[nom_amb].copy()
                
                for k in range(annee_ouverture,annee_fermeture):
                    if k in df_nb_unites_ambiances_test.index :
                        df_nb_unites_ambiances_test.at[k,actif.cle] = df_nb_unites_ambiances_test.at[k,actif.cle] + 1
            

                nom_fic = "DF_PA_%s_MerchantModule_%s_%s_test_%s.csv"%(nom_amb,str(annee_courante),str(indice_boucle),actif.cle)    
                path_df_parc = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
                df_nb_unites_ambiances_test.to_csv(path_df_parc,sep=";")
                
                dico_nb_unites_ambiances_test[nom_amb] = df_nb_unites_ambiances_test                
            
            # realisation de l'anticipation
            
            print("\t\t\t\t Realisation de l'anticipation")
            
            matrice_resultats_annuels = Anticipation.anticipation_resultats_annuels_parc_exogene(annee_debut_anticipation,annee_fin_anticipation, donnees_entree, donnees_simulation,dico_nb_unites_ambiances_test)
            
            Ecriture.ecriture_dispatch_boucle(matrice_resultats_annuels,donnees_entree,donnees_simulation,"rapport_MerchantModule",indice_boucle,annee_courante,actif.cle)
            
            print("\t\t\t\t\t Anticipation faite")
            
            if donnees_entree.parametres_simulation.extrapolation_merchant :
                dict_VAN_equivalente, dict_VAN_possibles = calcul_VAN_equivalente(donnees_entree,donnees_simulation,actif,annee_debut_anticipation,annee_fermeture,matrice_resultats_annuels)            
            else:
                dict_VAN_equivalente, dict_VAN_possibles = calcul_VAN_equivalente(donnees_entree,donnees_simulation,actif,annee_debut_anticipation,annee_fin_anticipation,matrice_resultats_annuels)
                    
            dict_VAN_equivalentes_avec_CAPEX[actif.cle] = dict_VAN_equivalente["VAN_avec_capex"]
            dict_VAN_equivalentes_sans_CAPEX[actif.cle] = dict_VAN_equivalente["VAN_sans_capex"]

            print("\t\t\t\t VAN (avec CAPEX) : %s"%(dict_VAN_equivalente["VAN_avec_capex"]))
            
            # ecriture du resume
            
            resume_market_module_invest.at[id_option_invest,"name"] = actif.cle
            resume_market_module_invest.at[id_option_invest,"type_invest"] = "new"            
            resume_market_module_invest.at[id_option_invest,"VAN_unite_test"] = dict_VAN_equivalente["VAN_avec_capex"] / 1e3
            resume_market_module_invest.at[id_option_invest,"REVENUS_unite_test"] = dict_VAN_equivalente["revenus"] / 1e3
            resume_market_module_invest.at[id_option_invest,"COUTS_FIXES_unite_test"] = dict_VAN_equivalente["couts_fixes_totaux"] / 1e3
              
            id_option_invest += 1


        for actif in actifs_a_tester_pour_ajout:
            if dict_VAN_equivalentes_avec_CAPEX[actif.cle] > VAN_max_ajout : 
                VAN_max_ajout = dict_VAN_equivalentes_avec_CAPEX[actif.cle]
                actif_candidat_ajout = actif


        ### Evaluation des candidats au repechage 
        
        print("\t\t Evaluation des candidats au repechage")
        print("\t\t\t %s"%(df_unite_deco))

        if len(df_unite_deco.index) > 0 : 
        
            df_unite_deco_grouped = df_unite_deco.groupby(["annee_ouverture","annee_fin_calcul_VAN","techno"])["unite"].apply(list)
            print("\t\t\t grouped :")
            print("\t\t\t %s"%(df_unite_deco_grouped))
   
  
            for idx, group in enumerate(df_unite_deco_grouped.index):
                        
                unite = df_unite_deco_grouped.to_numpy()[idx][0]
                actif = unite.actif   
                annee_ouverture = annee_courante  
                annee_fin_calcul_VAN = annee_courante + 1 
                annee_fermeture = group[1]
                
                unite_test = DonneesSimulation.Unite(actif, annee_ouverture, annee_fin_calcul_VAN)

                nom_group = "%s_ouv_%s_fin_%s"%(actif.cle,annee_ouverture,annee_fermeture)
                              
                print("\t\t\t %s"%(nom_group))  

                dico_nb_unites_ambiances_test = {}

                for ambiance in donnees_entree.ambiances :

  
                    
                    df_nb_unites_ambiances_test = dico_df_nb_unites_ambiances[ambiance].copy()
                    df_nb_unites_ambiances_test.at[annee_courante,actif.cle] = df_nb_unites_ambiances_test.at[annee_courante,actif.cle] + 1

                    dico_nb_unites_ambiances_test[nom_amb] = df_nb_unites_ambiances_test      
                    
                    nom_fic = "DF_PA_%s_MerchantModule_%s_%s_test_second_chance_%s.csv"%(nom_amb,str(annee_courante),str(indice_boucle),actif.cle)    
                    path_df_parc = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
                    df_nb_unites_ambiances_test.to_csv(path_df_parc,sep=";")
                                         

                matrice_resultats_annuels = Anticipation.anticipation_resultats_annuels_parc_exogene(annee_courante,annee_courante+1, donnees_entree, donnees_simulation,dico_nb_unites_ambiances_test)
                
                Ecriture.ecriture_dispatch_boucle(matrice_resultats_annuels,donnees_entree,donnees_simulation,"rapport_MerchantModule",indice_boucle,annee_courante,actif.cle)
                                           
                dict_VAN_equivalente, dict_VAN_possibles = calcul_VAN_equivalente(donnees_entree,donnees_simulation,actif,annee_courante,annee_courante+1,matrice_resultats_annuels)
                          
                print("\t\t\t VAN : %s"%(dict_VAN_equivalente["VAN_sans_capex"]))
                
                resume_market_module_invest.at[id_option_invest,"name"] = "%s_%s_%s"%(actif.cle,annee_ouverture,annee_fin_calcul_VAN)
                resume_market_module_invest.at[id_option_invest,"type_invest"] = "repechage"
                resume_market_module_invest.at[id_option_invest,"VAN_unite_test"] = dict_VAN_equivalente["VAN_sans_capex"] / 1e3
                resume_market_module_invest.at[id_option_invest,"REVENUS_unite_test"] = dict_VAN_equivalente["revenus"] / 1e3
                resume_market_module_invest.at[id_option_invest,"couts_fom"] = dict_VAN_equivalente["couts_fom"] / 1e3
            
                if dict_VAN_equivalente["VAN_sans_capex"] > VAN_max_ajout :
                    VAN_max_ajout = dict_VAN_equivalente["VAN_sans_capex"]
                    actif_candidat_ajout = actif
                    unite_repechee = unite     
                    annee_fermeture_repechage = annee_fermeture
                
                id_option_invest += 1
                
        if actif_candidat_ajout != None : 
            print("\t\t -> Candidat ajout : %s (VAN : %s)"%(actif_candidat_ajout.cle,str(VAN_max_ajout)))
            
            resume_decision.at["invest","actif"] = actif_candidat_ajout.cle
            resume_decision.at["invest","VAN_max_ajout"] = VAN_max_ajout            
            
            if unite_repechee != None : 
                print("\t\t\t (unite repechee)")
            else : 
                print("\t\t\t (nouvelle unite)")
        else : 
            print("\t\t -> pas de candidat a l'investissement")
                    
        ######## evaluation des demantelements potentiels
           
        #### realisation d'une anticipation
      
        annee_debut_anticipation = annee_courante                                        
        annee_fin_anticipation = min(annee_courante + donnees_entree.parametres_simulation.horizon_prevision, \
                                        donnees_entree.parametres_simulation.horizon_simulation)
                                        
        matrice_resultats_annuels = Anticipation.anticipation_resultats_annuels_parc_exogene(annee_debut_anticipation,annee_fin_anticipation, donnees_entree, donnees_simulation,dico_df_nb_unites_ambiances)
        
        Ecriture.ecriture_dispatch_boucle(matrice_resultats_annuels,donnees_entree,donnees_simulation,"rapport_MerchantModule",indice_boucle,annee_courante)        


        resume_market_module_divest = pd.DataFrame()
        id_option_divest = 0        

        VAN_min_retrait = 0
        actif_candidat_demantelement = None
        unite_a_demanteler = None     

        actifs_a_tester_pour_demantelement = []
        
        for actif in donnees_entree.tous_actifs() :
            if actif.demantelable and not actif.ajoutable :
                if df_nb_unites_parc_reel.at[annee_courante,actif.cle] > 0 : 
                    actifs_a_tester_pour_demantelement.append(actif)

        techno_en_sursis = []     

        for actif in actifs_a_tester_pour_demantelement :
                             
            ######## Evaluation lors de l'annee courante
                
            annee_ouverture = annee_courante
            annee_fin_calcul_VAN = annee_courante + 1
            
            dict_VAN_equivalente_annee_courante, dict_VAN_possibles_annee_courante = calcul_VAN_equivalente(donnees_entree,donnees_simulation,actif,annee_ouverture,annee_fin_calcul_VAN,matrice_resultats_annuels)
            
            print("\t\t\t Evaluation : %s -> VAN : %s"%(actif.cle,dict_VAN_equivalente_annee_courante["VAN_sans_capex"]))
            
            resume_market_module_divest.at[id_option_divest,"name"] = actif.cle
            resume_market_module_divest.at[id_option_divest,"VAN_sans_capex_annee_courante"] = dict_VAN_equivalente_annee_courante["VAN_sans_capex"]  / 1e3
            resume_market_module_divest.at[id_option_divest,"REVENUS_annee_courante"] = dict_VAN_equivalente_annee_courante["revenus"]  / 1e3
            resume_market_module_divest.at[id_option_divest,"FOM_annee_courante"] = dict_VAN_equivalente_annee_courante["couts_fom"]  / 1e3
            
            resume_market_module_divest.at[id_option_divest,"type"] = "parc_existant"

            if dict_VAN_equivalente_annee_courante["VAN_sans_capex"] < 0 : 
            
                print("\t\t Evaluation demantelement horizon complet (parc existant)")    
                
                for unite in donnees_simulation.parc.unites_actives(actif.cle, annee_courante):
                    
                    annee_ouverture = annee_courante
                    annee_fermeture = unite.annee_fermeture
                    
                    print("\t\t\t Test demantelement horizon complet : %s %s %s"%(actif.cle,annee_ouverture,annee_fermeture))    
                   
                    annee_fin_calcul_VAN = np.min([annee_fermeture, annee_fin_anticipation]) 
                    
                    dict_VAN_equivalente_horizon_complet, dict_VAN_possibles_horizon_complet = calcul_VAN_equivalente(donnees_entree,donnees_simulation,actif,annee_ouverture,annee_fin_calcul_VAN,matrice_resultats_annuels)

                    resume_market_module_divest.at[id_option_divest,"VAN_sans_capex_horizon_complet"] = dict_VAN_equivalente_horizon_complet["VAN_sans_capex"]  / 1e3
                    resume_market_module_divest.at[id_option_divest,"REVENUS_horizon_complet"] = dict_VAN_equivalente_horizon_complet["revenus"]  / 1e3
                    resume_market_module_divest.at[id_option_divest,"FOM_horizon_complet"] = dict_VAN_equivalente_horizon_complet["couts_fom"]  / 1e3

                    if  dict_VAN_equivalente_horizon_complet["VAN_sans_capex"] < VAN_min_retrait : 
                    
                        VAN_min_retrait = dict_VAN_equivalente_horizon_complet["VAN_sans_capex"]
                        actif_candidat_demantelement = actif
                        unite_a_demanteler = unite
                    
            id_option_divest += 1

        if actif_candidat_demantelement != None : 
            print("Candidat au retrait parmi parc existant : %s (VAN : %s)"%(actif_candidat_demantelement.cle,VAN_min_retrait))
        else :
            print("Pas de candidat au retrait dans le parc existant")

        ## Parc Investi
        
        
        print("\t\t Evaluation demantelement annee courante (unites investies au cours de la boucle)")
        
        unites_investies_en_sursis = []
        
        for idx_unite in df_unite_invest.index :


            unite = df_unite_invest.at[idx_unite,"unite"]
            actif = unite.actif
            
            # annee courante
            
            annee_ouverture = annee_courante
            annee_fermeture = df_unite_invest.at[idx_unite,"annee_fermeture"]
            
            annee_fin_calcul_VAN = annee_courante + 1

            dict_VAN_equivalente_annee_courante, dict_VAN_possibles_annee_courante = calcul_VAN_equivalente(donnees_entree,donnees_simulation,actif,annee_ouverture,annee_fin_calcul_VAN,matrice_resultats_annuels)

            print("\t\t\t %s (ouv. : %s , ferm. %s) -> VAN (annee courante) : %s "%(unite.actif.cle,annee_ouverture,annee_fermeture,dict_VAN_equivalente_annee_courante["VAN_avec_capex"]))         

            resume_market_module_divest.at[id_option_divest,"name"] = "%s_%s_%s"%(actif.cle,annee_ouverture,annee_fermeture) 
            resume_market_module_divest.at[id_option_divest,"type"] = "annulation_investissement"
            resume_market_module_divest.at[id_option_divest,"VAN_avec_capex_annee_courante"] = dict_VAN_equivalente_annee_courante["VAN_avec_capex"]  / 1e3
            
       
            # horizon complet          

            annee_fin_calcul_VAN = min(annee_fermeture, annee_fin_anticipation  ) 
                                               
            dict_VAN_equivalente_horizon_complet, dict_VAN_possibles_horizon_complet = calcul_VAN_equivalente(donnees_entree,donnees_simulation,actif,annee_ouverture,annee_fin_calcul_VAN,matrice_resultats_annuels)

            print("\t\t\t %s (ouv. : %s , ferm. %s) -> VAN (horizon complet): %s "%(unite.actif.cle,annee_ouverture,annee_fermeture,dict_VAN_equivalente_horizon_complet["VAN_avec_capex"]))         
        
            resume_market_module_divest.at[id_option_divest,"VAN_avec_capex_horizon_complet"] = dict_VAN_equivalente_horizon_complet["VAN_avec_capex"]
            

            if  dict_VAN_equivalente_horizon_complet["VAN_avec_capex"] < VAN_min_retrait : 
            
                VAN_min_retrait = dict_VAN_equivalente_horizon_complet["VAN_avec_capex"]
                actif_candidat_demantelement = actif
                unite_a_demanteler = unite            
      
            id_option_divest += 1 
        
        if actif_candidat_demantelement != None : 
            print("\t\t -> Candidat retrait : %s (VAN : %s)"%(actif_candidat_demantelement.cle,str(VAN_min_retrait)))
            resume_decision.at["divest","actif"] = actif_candidat_demantelement.cle
            resume_decision.at["divest","VAN_min_retrait"] = VAN_min_retrait
        else : 
            print("\t\t -> pas de candidat au retrait")
            
        # Choix de la decision : investissement ou declassement ? 
        
        decision = None
        
        
        if (not actif_candidat_ajout) and (not actif_candidat_demantelement) : 
            decision = None
            
        if actif_candidat_ajout and (not actif_candidat_demantelement) :
            # Une décision d'investissement et aucun déclassement
            decision = "investissement"
            resume_decision.at["invest","retenu"] = "yes"
            
        if (not actif_candidat_ajout) and actif_candidat_demantelement :
            # Une décision de déclassemen et aucun investissement
            decision = "declassement"
            resume_decision.at["divest","retenu"] = "yes"
            
        if actif_candidat_ajout and actif_candidat_demantelement :            
            
            if abs(VAN_max_ajout) > abs(VAN_min_retrait) :
                decision = "investissement"
                resume_decision.at["invest","retenu"] = "yes"
            if abs(VAN_max_ajout) < abs(VAN_min_retrait) :            
                decision = "declassement"            
                resume_decision.at["divest","retenu"] = "yes"

        print("\t\t -> Decision prise : %s"%(decision))


            
        if decision == "investissement" :
            if unite_repechee != None :           
    
                donnees_simulation.parc.update_date_fermeture(unite_repechee,annee_fermeture_repechage)
                
                idx = donnees_simulation.df_resume.index.max()+1
                donnees_simulation.df_resume.at[idx,"step"] = "second_chance_%s"%(unite_repechee.actif.cle)
                donnees_simulation.df_resume.at[idx,"module"] = "MerchantModule"
                donnees_simulation.df_resume.at[idx,"year"] = annee_courante     
                donnees_simulation.df_resume.at[idx,"loop"] = indice_boucle
            
            else : 
            
                actif_choisi = actif_candidat_ajout
  
                nombre_unites_investies = actif_choisi.granularite_investissement         
                           
                # On ajoute effectivement l'unité dans les parcs réels et anticipés

                print("\t\t Choix d'investissement : ajout de %d unités de %s\n" % (nombre_unites_investies, actif_choisi.cle))
                   
                annee_ouverture = annee_courante + actif_choisi.duree_construction
                annee_fermeture = annee_ouverture + actif_choisi.duree_vie
                
                for indice_unite_ajoutee in range(nombre_unites_investies):
                
                    unite_ajoutee = DonneesSimulation.Unite(actif_choisi, annee_ouverture, annee_fermeture)

                    if unite_ajoutee not in unites_initialement_presentes[actif_choisi.cle] : 
                    
                        df_row = pd.DataFrame({"unite":[unite_ajoutee],
                                                        "techno":[actif_choisi.cle],
                                                        "annee_ouverture":[unite_ajoutee.annee_ouverture],
                                                        "annee_fermeture":[unite_ajoutee.annee_fermeture]})
                                                        
                        df_unite_invest = pd.concat((df_unite_invest,df_row), ignore_index=True)                    
                    
                    donnees_simulation.parc.ajout_unite(unite_ajoutee)           



                idx = donnees_simulation.df_resume.index.max()+1
                donnees_simulation.df_resume.at[idx,"step"] = "new_%s"%(actif_choisi.cle)
                donnees_simulation.df_resume.at[idx,"module"] = "MerchantModule"
                donnees_simulation.df_resume.at[idx,"year"] = annee_courante     
                donnees_simulation.df_resume.at[idx,"loop"] = indice_boucle
                
        if decision == "declassement" :
        
            print("\t\t Choix demantelement : retrait de 1 unités de %s\n" % (actif_candidat_demantelement.cle))
                
            liste_unites_fermees = []
            
            actif_moins_rentable = actif_candidat_demantelement    
            
            if unite_a_demanteler in unites_initialement_presentes[actif_moins_rentable.cle] : 

                df_row = pd.DataFrame({"unite":[unite_a_demanteler],
                                                "techno":[actif_moins_rentable.cle],
                                                "annee_ouverture":[unite_a_demanteler.annee_ouverture],
                                                "annee_fermeture":[unite_a_demanteler.annee_fermeture],
                                                "annee_fin_calcul_VAN":[min(unite_a_demanteler.annee_fermeture,annee_fin_anticipation)]})
                                                
                df_unite_deco = pd.concat((df_unite_deco,df_row), ignore_index=True)


                idx = donnees_simulation.df_resume.index.max()+1
                donnees_simulation.df_resume.at[idx,"step"] = "closure_%s"%(actif_candidat_demantelement.cle)
                donnees_simulation.df_resume.at[idx,"module"] = "MerchantModule"
                donnees_simulation.df_resume.at[idx,"year"] = annee_courante     
                donnees_simulation.df_resume.at[idx,"loop"] = indice_boucle        
            
            else:

                idx = donnees_simulation.df_resume.index.max()+1
                donnees_simulation.df_resume.at[idx,"step"] = "reverse_%s"%(actif_candidat_demantelement.cle)
                donnees_simulation.df_resume.at[idx,"module"] = "MerchantModule"
                donnees_simulation.df_resume.at[idx,"year"] = annee_courante     
                donnees_simulation.df_resume.at[idx,"loop"] = indice_boucle        

            fermeture = donnees_simulation.parc.fermeture_anticipee_unite(unite_a_demanteler, annee_courante)             

        if decision == None :

            continuer = False

        else : 
        
            etat_parc = [ donnees_simulation.parc.nombre_unites(actif.cle,annee_courante) for actif in donnees_entree.tous_actifs() ]
            
            print("etats parc sauvegardes")
            print(dict_etats_parc)
            
            print("etat parc courrant")
            print(etat_parc)
                        
            for k in dict_etats_parc.keys() : 
                if dict_etats_parc[k] == etat_parc : 
                    print("Le parc est dans le meme etat que %s"%(k))
                    continuer = False
                    
            dict_etats_parc[indice_boucle] = [ donnees_simulation.parc.nombre_unites(actif.cle,annee_courante) for actif in donnees_entree.tous_actifs() ]
                           

        path_dir = os.path.join(donnees_entree.dossier_sortie,"annee_"+ str(annee_courante),"rapport_MerchantModule",str(indice_boucle))
        path_file = os.path.join(path_dir,"rapport_%s_%s.xlsx"%(annee_courante,indice_boucle))
        
        if not os.path.isdir(path_dir):
            os.makedirs(path_dir)
        
           
        with pd.ExcelWriter(path_file, engine='xlsxwriter') as writer :
            resume_market_module_invest.to_excel(writer, sheet_name='invest')
            resume_market_module_divest.to_excel(writer, sheet_name='divest')
            resume_decision.to_excel(writer, sheet_name='decision')
            
        indice_boucle += 1 
                                
        
    return None