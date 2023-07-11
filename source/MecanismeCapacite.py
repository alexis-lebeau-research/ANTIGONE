# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import DonneesEntree
import DonneesSimulation
import Contrats
import Anticipation
import Ecriture
import Lecture
import IndicateursEconomiques

import numpy as np
import pandas as pd
from math import *

import sys
import os

class RapportEnchere :
    """
    Cette classe représente une enchère du mécanisme de capacité.

    Attributs
    ---------
    horizon : DonneesEntree.Actif
        type d'actif dont des unités ont été démantelées
    quantite_capacite : int
        volume de capacité lauréate
    prix_capacite : float
        coût total des compensations versées par l'agence de régulation pour chaque unité de capacité (€/kW)
    """
    def __init__(self, horizon, quantite_capacite, prix_capacite):
        self.horizon = horizon
        self.quantite_capacite = quantite_capacite
        self.prix_capacite = prix_capacite
        

class RapportEnchereMecanismeCapacite:
    """
    Cette classe synthétise les informations d'une séquence du mécanisme de capacité. 

    Attributs
    ---------
    annee_courante : int 
        année courante 
    annee_livraison : int
        année de livraison du mécanisme de capacité 
    quantite_capacite : int
        volume de capacité lauréate
    prix_capacite : float
        coût total des compensations versées par l'agence de régulation pour chaque unité de capacité (€/kW)
    df_actifs_laureats : dataFrame
        dataFrame qui contient les clé des actifs lauréats, leur bid, la capacité des unités et le nombre d'unité laureate 
    df_actifs_non_laureats : dataFrame
        dataFrame qui contient les clé des actifs non lauréats, leur bid, la capacité des unités et le nombre d'unité non laureate 
    """

    def __init__(self, annee_courante, horizon, quantite_capacite, prix_capacite, df_actifs_laureats, df_actifs_non_laureats):
        self.annee_courante = annee_courante
        self.annee_livraison = annee_livraison
        self.quantite_capacite = quantite_capacite
        self.prix_capacite = prix_capacite
        self.df_actifs_laureats = df_actifs_laureats
        self.df_actifs_non_laureats = df_actifs_non_laureats
        
class RapportMecanismeCapacite:
    """
    Cette classe synthétise les informations d'une séquence du mécanisme de capacité. 

    Attributs
    ---------
    annee_courante : int 
        année courante 
    annee_livraison : int
        année de livraison
    quantite_capacite : int
        volume de capacité lauréate
    prix_capacite : float
        coût total des compensations versées par l'agence de régulation pour chaque unité de capacité (€/kW)
    df_actifs_laureats : dataFrame
        dataFrame qui contient les clé des actifs lauréats, leur bid, la capacité des unités et le nombre d'unité laureate 
    df_actifs_non_laureats : dataFrame
        dataFrame qui contient les clé des actifs non lauréats, leur bid, la capacité des unités et le nombre d'unité non laureate 
    """

    def __init__(self, annee_courante, annee_livraison, quantite_capacite, prix_capacite, df_actifs_laureats, df_actifs_non_laureats):
        self.annee_courante = annee_courante
        self.annee_livraison = annee_livraison
        self.quantite_capacite = quantite_capacite
        self.prix_capacite = prix_capacite
        self.df_actifs_laureats = df_actifs_laureats
        self.df_actifs_non_laureats = df_actifs_non_laureats




def selection_actifs_mecanisme_capacite(capacite_investissement_argent, capacite_investissement_puissance, donnees_entree, donnees_simulation):
    """
    Sélectionne, parmi l'ensemble des actifs, ceux qui peuvent participer au mécanisme de capacité et calcule pour chacun le
    nombre maximum d'unités pouvant être construites en respectant les capacités d'investissement et les limites de
    gisement. Pour les actifs qui ne peuvent qu'être démentelé, il n'y a donc pas de limite (- inf).

    Paramètres
    ----------
    capacite_investissement_argent : float
        part du budget consacré à l'investissement encore disponible
    capacite_investissement_puissance : float
        part du budget en puissance consacré à l'investissement encore disponible
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser

    Retours
    -------
    list
        liste des actifs éligibles
    dict
        dictionnaire contenant, pour chaque actif éligible, le nombre maximal d'unités pouvant être construites
    """

    annee_courante = donnees_simulation.annee_courante
    horizon_simulation = donnees_entree.parametres_simulation.horizon_simulation

    # représentation de l'infini
    plus_infini = float("inf")
    moins_infini = - float("inf")

    liste_actifs_mecanisme_capacite = []

    dict_nombre_max_unites = dict()

    # construction de la liste des actifs qui peuvent participer au mécanisme de capacité selon les ressources d'investissement restantes
    # et selon le gisement disponible pour la technologie
    for actif in donnees_entree.tous_actifs():
        
        if actif.eligible_mecanisme_capacite : 
      
            dict_nombre_max_unites[actif.cle] = 0
    
            # on va calculer le nombre maximum d'unités de l'actif dans lesquelles on peut investir
            # ce nombre est initialisé à plus_infini
            nombre_max_unites_investies = plus_infini
    
            puissance = 0
            if actif.categorie == "Stockage":
                puissance = actif.puissance_nominale_decharge
            elif actif.categorie == "Pilotable":
                puissance = actif.puissance_nominale
            elif actif.categorie == "ENR":
                puissance = actif.puissance_reference
    
            # non-dépassement de la limite de construction annuelle
            if not(actif.limite_construction_annuelle == 'aucune'):
                nombre_unites_deja_ouvertes = donnees_simulation.parc.nombre_unites_ouvertes(actif.cle, annee_courante + actif.duree_construction)
                nombre_max_unites_investies = min(nombre_max_unites_investies, max(0, actif.limite_construction_annuelle - nombre_unites_deja_ouvertes))
    
            # non-dépassement de la capacité d'investissement en argent
            cout_fixe_construction_actif = actif.cout_fixe_construction(annee_courante)
            if cout_fixe_construction_actif > 0:
                nombre_max_unites_investies = min(nombre_max_unites_investies, int(capacite_investissement_argent / cout_fixe_construction_actif))
    
            # non-dépassement de la capacité d'investissement en puissance
            if puissance > 0:
                nombre_max_unites_investies = min(nombre_max_unites_investies, int(capacite_investissement_puissance / puissance))
    
            # non-dépassement du gisement sur toute la durée de vie de l'actif potentiellement construit
            # uniquement vérifié s'il est possible d'investir dans au moins une unité avec les capacités restantes
            if (nombre_max_unites_investies > 0) and (not actif.gisement_max == "aucun") and puissance > 0:
                nombre_max_unites_total = int(actif.gisement_max / puissance)
                for annee_fonctionnement in range(min(annee_courante + actif.duree_construction, horizon_simulation), min(annee_courante + actif.duree_construction + actif.duree_vie, horizon_simulation)):
                    nombre_max_unites_investies = min(nombre_max_unites_investies, nombre_max_unites_total - donnees_simulation.parc.nombre_unites(actif.cle, annee_fonctionnement))
    
            if actif.ajoutable and nombre_max_unites_investies > 0:
                liste_actifs_mecanisme_capacite.append(actif)
                dict_nombre_max_unites[actif.cle] = nombre_max_unites_investies
                
            if actif.demantelable : 
                liste_actifs_mecanisme_capacite.append(actif)
                dict_nombre_max_unites[actif.cle] = moins_infini

    return liste_actifs_mecanisme_capacite, dict_nombre_max_unites


def facteur_de_charge_mecapa(actif, annee_livraison, donnees_entree) :
    """
    Détermine pour l'actif, le facteur de charge moyen pour l'année de livraison. Ce dernier permet de déterminer la contribution de l'actif à la production lors de la pointe hivernale et donc calculer la capacité offerte pendant l'enchère.

     Paramètres
    ----------
    actif : DonneesEntree.Actif
        actif dont on souhaite déterminer le facteur de charge
    annee_livraison : int
        année de livraison
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser

    Retours
    -------
    facteur_de_charge_mecapa : float
        Facteur de charge moyen jusque la fin de l'anticipation

    """
    realisation = donnees_entree.realisation

    df_ponderation = donnees_entree.df_parametres_ponderation

    puissance = 0
    if actif.categorie == "Stockage":
        puissance = actif.puissance_nominale_decharge
    elif actif.categorie == "Pilotable":
        puissance = actif.puissance_nominale
    elif actif.categorie == "ENR":
        puissance = actif.puissance_reference


    facteur_de_charge_mecapa = 0

    for annee in range (annee_livraison, annee_livraison + 1) :

        disponibilite_annee = pd.DataFrame([0 for k in range(8760)], columns = ["Annee_%d"%annee])["Annee_%d"%annee]

        for meteo in [meteo for meteo in realisation.keys()][1:]  :

            indice_meteo = int(meteo[-1])
            dispo_pilot_meteo = realisation[meteo]["dispo"]
            facteur_charge_enr_meteo = realisation[meteo]["fc"]

            if actif.categorie == "Pilotable":
                try :
                    disponibilite_annee = dispo_pilot_meteo["%s_%d"%(actif.cle, annee)]
                    facteur_de_charge_mecapa += disponibilite_annee.sort_values(ascending = False).head(int(8760/4)).mean() * df_ponderation.at[indice_meteo, "value"]
                except KeyError:
                    disponibilite_annee = pd.DataFrame([1 for k in range(8760)], columns = ["Annee_%d"%annee])["Annee_%d"%annee]
                    facteur_de_charge_mecapa += (disponibilite_annee.mean()) * df_ponderation.at[indice_meteo, "value"]
            elif actif.categorie == "ENR":
                try :
                    disponibilite_annee = facteur_charge_enr_meteo["%s_%d"%(actif.cle, annee)]
                    facteur_de_charge_mecapa += (disponibilite_annee.mean()) * df_ponderation.at[indice_meteo, "value"]
                except KeyError:
                    disponibilite_annee = pd.DataFrame([1 for k in range(8760)], columns = ["Annee_%d"%annee])["Annee_%d"%annee]
                    facteur_de_charge_mecapa += (disponibilite_annee.mean()) * df_ponderation.at[indice_meteo, "value"]

            elif actif.categorie == "Stockage" :
                if actif.cle == "bat_4h" :
                    facteur_de_charge_mecapa = 0.85
                if actif.cle == "bat_1h" :
                    facteur_de_charge_mecapa = 0.46



    return facteur_de_charge_mecapa


def enchere_mecanisme_capacite(donnees_entree, demande_capacite_annee_livraison, df_bid_mecapa):
    """
    Réalise l'enchère du mécanisme de capacité à partir de la puissance demandée pour l'année de livraison et d'une dataframe comprenant l'ensemble de l'offre
    

    Paramètres
    ----------
    demande_capacite_annee_livraison : float
        besoin capacitaire pour l'année de livraison 
    df_bid_mecapa : dataframe
        dataframe comprenant l'ensemble des offres (investissement et désinvestissement)
    Retours
    -------
    capacite_laureate_totale : float 
        Capacité totale des unités lauréates
    prix_capacite : float 
        prix de clearing de la capacité pour cette enchère (max des MM des unités lauréates)
    df_actifs_laureats_mecapa : dataframe
        dataframe contenant l'ensemble des actifs lauréats avec les informations correspondantes    
    """
    df_bid_mecapa_sort = (df_bid_mecapa.dropna()).sort_values(by = "bid", ascending = True)
    
    capacite_laureate_totale = 0
    price_cap = 1000000
    try : 
        price_cap = float(donnees_entree.df_param_mecapa.at["price_cap", "value"])
    except KeyError : 
        pass
        
    df_actifs_laureats_mecapa = pd.DataFrame(columns = ["actif", 'bid', 'capacite', 'fc', 'nbr_unite', 'CAPEX', 'FO&M', 'revenus_energie', 'prime_risque_energie', 'revenus_capacitaires'])
    
    while capacite_laureate_totale < demande_capacite_annee_livraison and not(df_bid_mecapa_sort.empty) :
        
        actif_laureat = df_bid_mecapa_sort.index[0]
        cle_actif_laureat = df_bid_mecapa_sort.at[actif_laureat, "actif"]
        bid_laureat_actif = df_bid_mecapa_sort.at[actif_laureat, "bid"]
        capacite_laureate_actif = df_bid_mecapa_sort.at[actif_laureat, "capacite"]
        fc_laureate_actif = df_bid_mecapa_sort.at[actif_laureat, "fc"]
        investissement_initial = df_bid_mecapa_sort.at[actif_laureat, "CAPEX"]
        couts_fixes_maintenance = df_bid_mecapa_sort.at[actif_laureat, "FO&M"]
        revenus_energie = df_bid_mecapa_sort.at[actif_laureat, "revenus_energie"]
        prime_risque_energie = df_bid_mecapa_sort.at[actif_laureat, "prime_risque_energie"]
        anticipation_revenus_capacitaires = df_bid_mecapa_sort.at[actif_laureat, "revenus_capacitaires"]
        
        if bid_laureat_actif > price_cap :
            prix_capacite = price_cap
            print("La capacité a atteint le plafond de prix de : %f"%price_cap)
            break
        
        nbr_unite_deja_laureate = 0
        if actif_laureat in df_actifs_laureats_mecapa.index : 
            nbr_unite_deja_laureate = df_actifs_laureats_mecapa.at[actif_laureat, "nbr_unite"]
        
        df_actifs_laureats_mecapa.loc[actif_laureat] = [cle_actif_laureat, bid_laureat_actif, capacite_laureate_actif, fc_laureate_actif, nbr_unite_deja_laureate+1, investissement_initial, couts_fixes_maintenance, revenus_energie, prime_risque_energie, anticipation_revenus_capacitaires]
        
        df_bid_mecapa_sort.at[actif_laureat, "nbr_unite"] -= 1 
        if df_bid_mecapa_sort.at[actif_laureat, "nbr_unite"] <= 0 : 
            df_bid_mecapa_sort = df_bid_mecapa_sort.drop(index = [actif_laureat])
        
        capacite_laureate_totale = (df_actifs_laureats_mecapa['capacite']*df_actifs_laureats_mecapa['nbr_unite']*df_actifs_laureats_mecapa['fc']).sum()
    
        prix_capacite = df_actifs_laureats_mecapa['bid'].max()
    
    if capacite_laureate_totale < demande_capacite_annee_livraison : 
            print("\t\t La capacité demandée n'a pas été atteinte, seulement %d MW ont été pourvus"%capacite_laureate_totale)
            
    return capacite_laureate_totale, prix_capacite, df_actifs_laureats_mecapa
    


def calcul_anticipation_revenus_capacitaires(actif, annee_ouverture, annee_fin_anticipation, nbAnneeNPV, dico_anticipation_prix_capacite_moyen, donnees_entree) :
    """
    Calcul la somme actualisée des revenus capacitaires pour une unité de l'actif considéré dans l'ambiance choisie à partir du dictionnaire contenant les anticipations des prix de la capacité dans chacune des ambiances entre les années annee_ouverture + 1 et annee_ouverture + nbAnneeNPV. On commence à annee_ouverture + 1 car on souhaite déterminer le MM de l'année annee_ouverture en fonction des anticipations pour les années suivantes.
    
    Paramètres
    ----------
    actif : DonneesEntree.Actif
        Actif considéré pour lequel on souhaite calculer les revenus capacitaires des anneés comprises entre annee_debut + 1 et annee_fin
    ambiance : str
        nom de l'ambiance
    annee_ouverture : int 
        Année à partir de laquelle l'actif est construit et fonctionne
    annee_fin_anticipation : int 
        Année de la fin de l'ancitipation. On peut donc récupérer le prix de la capacité pour les années qui sont entre annee_fin_anticipation et annee_fin (tous égaux au prix de la capacité à l'année annee_fin_anticipation + 1)
    nbAnneeNPV : int 
        Nombre d'année sur lesquelles on va calculer les revenus capacitaires
    dico_anticipation_prix_capacite : dict
        dictionnaire contenant pour chaque ambiance un dictionnaire contenant pour chaque année un dictionnaire contenant les anticipations de prix et de capacité lauréate : dico_anticipation_prix_capacite[ambiance][annee][prix_capacite]
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée
    Retours
    -------
    anticipation_revenus_capacitaires_actualises : float 
        revenus capacitaires anticipés et actualisés
    """

    annee_fin = annee_ouverture + nbAnneeNPV
    
    anticipation_revenus_capacitaires_actualises = 0
    
    for annee in range(annee_ouverture + 1, annee_fin) :
    
        prix_capacite_annuel = dico_anticipation_prix_capacite_moyen[annee_fin_anticipation - 1]["prix_capacite"]
        try : 
            prix_capacite_annuel = dico_anticipation_prix_capacite_moyen[annee]["prix_capacite"]
        except KeyError :
            pass 
        
        puissance = actif.puissance * facteur_de_charge_mecapa(actif, annee_ouverture, donnees_entree)
        revenu_capacitaire_annuel = puissance * prix_capacite_annuel
        
        anticipation_revenus_capacitaires_actualises += revenu_capacitaire_annuel * (1 + actif.taux_actualisation) ** (-(annee - annee_ouverture))
        
    return anticipation_revenus_capacitaires_actualises
    


def calcul_anticipation_prix_capacite(actif_ajoute, annee_debut_anticipation_capacite, annee_fin_anticipation, donnees_entree, donnees_simulation, matrice_resultats_annuels, dico_df_nb_unites_ambiances) : 
    """
    Calcul le prix anticipé de la capacité entre l'année de début de l'ancitipation et l'année de fin de l'anticipation. Pour cela, on détermine le dispatch pour chacune des années en question. Il faut ensuite réaliser les enchères du mécanisme de capacité pour chacune des années afin de déterminer le prix de la capacité. Pour cela, il faut partir des années après l'horizon de prévision. En effet, à partir de cette année on a atteint un état stable dans lequel le nombre des actifs est stable et donc dans lequel il n'y a plus de nouveau investissement. On peut donc, pour ces années, déterminer pour tous les actifs un MM nécessaire pour continuer de fonctionner (calcul_missing_money_actif_demantelable) et donc en déduire le prix de la capacité après réalisation de l'enchère. Pour les années dans la fenètre de prévision il suffit ensuite de remonter de la fin vers le début en prenant en compte les prix de la capacité des années suivantes qui sont nécessaires pour les nouveaux investissements.   

    Paramètres
    ----------
    annee_debut_anticipation_capacite : int 
        année du début de l'ancitipation du prix de la capacité
    annee_fin_anticipation : int 
        année de fin de l'ancitipation du prix de la capacité
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    matrice_resultats_annuels : list
        matrice indexée par [ambiance][année][météo] des résultats des dispatchs 
    dico_df_nb_unites_ambiances : dict
        dictionnaire qui contient le parc anticipé dans chacune des ambiances en cohérence avec le parc réel de l'année courante

    Retours
    -------
    dico_anticipation_prix_capacite : dic
        dictionnaire qui contient les listes d'anticipation de prix de la capacité dans chacune des ambiances
    """     
    print("\t\t\t Calcul du prix anticipé de la capacité")
    dico_anticipation_prix_capacite = dict()
    dico_anticipation_prix_capacite_moyen = dict()
    
    annee_courante = donnees_simulation.annee_courante
    
    if annee_debut_anticipation_capacite < annee_fin_anticipation : 
        matrice_resultats_annuels = [matrice_resultats_annuels[numero_ambiance][1:] for numero_ambiance in range(len(donnees_entree.ambiances))]

    # Calcul du prix de la capcité pour la dernière année anticipée et toutes les suivantes dans chacune des ambiances 
    annee_livraison = annee_fin_anticipation - 1
    numero_ambiance = 0
    for ambiance in donnees_entree.ambiances : 
        parc_ambiance = (dico_df_nb_unites_ambiances[ambiance]).head(annee_fin_anticipation)
        
        parc_investissement_ambiance = pd.DataFrame(index = parc_ambiance.index, columns = parc_ambiance.columns).fillna(0)
        parc_qui_se_conserve_ambiance = pd.DataFrame(index = parc_ambiance.index, columns = parc_ambiance.columns).fillna(0)
        diff = parc_ambiance.diff().fillna(0)
        
        for techno in parc_ambiance.columns : 
            for annee in parc_ambiance.index : 
                if diff.at[annee, techno] == 0 :
                    parc_qui_se_conserve_ambiance.at[annee, techno] = parc_ambiance.at[annee, techno]
                if diff.at[annee, techno] > 0 :
                    parc_investissement_ambiance.at[annee, techno] = diff.at[annee, techno]
                    if parc_ambiance.at[annee, techno] > 0 :
                        parc_qui_se_conserve_ambiance.at[annee, techno] = parc_ambiance.at[annee-1, techno]
                if diff.at[annee, techno] < 0 :
                    parc_qui_se_conserve_ambiance.at[annee, techno] = parc_ambiance.at[annee, techno]
                    
        if  parc_investissement_ambiance.at[annee_debut_anticipation_capacite - 1, actif_ajoute.cle] == 0 :       
            parc_investissement_ambiance.at[annee_debut_anticipation_capacite - 1, actif_ajoute.cle] += 1 
            parc_qui_se_conserve_ambiance.at[annee_debut_anticipation_capacite - 1, actif_ajoute.cle] -= 1 

        # détermination du missing money des actifs existants éligibles au mécanisme de capacité
        df_bid_mecapa_ambiance = pd.DataFrame(columns = ["actif", "bid", "capacite", 'fc', 'nbr_unite', 'CAPEX', 'FO&M', 'revenus_energie', 'prime_risque_energie', 'revenus_capacitaires'])
        
        for cle_actif in donnees_entree.data_frame_actifs_eligibles_mecapa.index :
            if not donnees_entree.data_frame_actifs_eligibles_mecapa.at[cle_actif, 'eligible'] :
                continue
                
            actif = donnees_entree.trouve_actif(cle_actif)
            
            puissance = actif.puissance
            
            nb_unite_invest = parc_investissement_ambiance.at[annee_livraison, actif.cle]
            nb_unite_qui_se_conservent = parc_qui_se_conserve_ambiance.at[annee_livraison, actif.cle]    
            
            if nb_unite_qui_se_conservent > 0 and actif.demantelable : 
                
                if donnees_entree.df_param_mecapa.at["MM_CT", "value"] :
                    matrice_resultats =  [[matrice_resultats_annuels[numero_ambiance][-1]]]
                    nbAnneeNPV = 1
                    annee_fin_calcul_NPV = annee_livraison + 1
                    anticipation_revenus_capacitaires = 0
                    
                else : 
                    matrice_resultats = [matrice_resultats_annuels[numero_ambiance]] 
        
                    if donnees_entree.parametres_simulation.extrapolation_EOM :
                        annee_fin_calcul_NPV = annee_livraison + actif.duree_vie
                    else : 
                        annee_fin_calcul_NPV = annee_fin_anticipation          
                    nbAnneeNPV = annee_fin_calcul_NPV - annee_livraison
                    
                    
                taux_actualisation = actif.taux_actualisation
                couts_fixes_maintenance =  np.array([ actif.cout_fixe_maintenance * (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum()
                unite =  DonneesSimulation.Unite(actif, annee_livraison, actif.duree_vie) 
                
                matrice_revenus_unite = IndicateursEconomiques.calcul_matrice_revenus_annuels_sans_CF(unite, matrice_resultats, annee_livraison, annee_fin_calcul_NPV, donnees_entree, donnees_simulation)
                VAN_revenus_energie, VAN_annualisee, prime_risque_energie, liste_VAN_revenus_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_unite, taux_actualisation, donnees_entree,0,nbAnneeNPV)

                VAN_unite = VAN_revenus_energie - couts_fixes_maintenance
                
                if VAN_unite < 0 : 
                    missing_money_actif_divest = -VAN_unite * (taux_actualisation/( 1 + taux_actualisation)) / ( 1 - (1 + taux_actualisation)**(-nbAnneeNPV))
                    
                else :
                    missing_money_actif_divest = 0  
                               
                puissance = actif.puissance
                fc = facteur_de_charge_mecapa(actif, annee_livraison, donnees_entree)
                
                if not donnees_entree.df_param_mecapa.at["MM_CT", "value"] : 
                    anticipation_revenus_capacitaires = np.array([ missing_money_actif_divest  * (1+taux_actualisation)**(-n) for n in range(1,nbAnneeNPV)]).sum()
            
                df_bid_mecapa_ambiance.loc["%s_divest"%actif.cle] = [actif.cle, missing_money_actif_divest/(puissance*fc), puissance, fc, nb_unite_qui_se_conservent, 0, couts_fixes_maintenance/puissance, VAN_revenus_energie/puissance, prime_risque_energie/puissance, anticipation_revenus_capacitaires/(puissance*fc)]
            
          
          
            
            if nb_unite_invest > 0 and actif.ajoutable : 
                
                gisement_annuel_actif = donnees_entree.data_frame_actifs_eligibles_mecapa.at[actif.cle, 'gisement_annuel']
                if nb_unite_invest*actif.puissance > gisement_annuel_actif : 
                    nb_unite_invest = floor(gisement_annuel_actif/actif.puissance)
                
                if donnees_entree.parametres_simulation.extrapolation_EOM :
                    annee_fin_calcul_NPV = annee_livraison + actif.duree_vie
                else : 
                    annee_fin_calcul_NPV = annee_fin_anticipation                  
                nbAnneeNPV = annee_fin_calcul_NPV - annee_livraison 

                taux_actualisation = actif.taux_actualisation
                
                #annuite = IndicateursEconomiques.calcul_investissement_IDC_annualise(actif,annee_courante)                
                #investissement_initial =  np.array([ annuite * (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum()                    
                investissement_initial = actif.cout_fixe_construction(annee_livraison)                
                couts_fixes_maintenance =  np.array([ actif.cout_fixe_maintenance * (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum()
                
                # Création d'une unite afin de pouvoir lancer les fonctions de calcul de revenus
                unite =  DonneesSimulation.Unite(actif, annee_livraison, annee_fin_calcul_NPV) 
                matrice_resultats_annuels_ambiance = [matrice_resultats_annuels[numero_ambiance]]          
                matrice_revenus_annuels_energie_unite = IndicateursEconomiques.calcul_matrice_revenus_annuels_sans_CF(unite, matrice_resultats_annuels_ambiance, annee_livraison, annee_fin_calcul_NPV, donnees_entree, donnees_simulation)
                VAN_revenus_energie, VAN_annualisee, prime_risque_energie, liste_VAN_revenus_energie_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_annuels_energie_unite, taux_actualisation, donnees_entree,0,nbAnneeNPV)
                
                VAN_unite = VAN_revenus_energie - couts_fixes_maintenance - investissement_initial

                if VAN_unite < 0 : 
                    missing_money_actif_invest = -VAN_unite * (taux_actualisation/( 1 + taux_actualisation)) / ( 1 - (1 + taux_actualisation)**(-nbAnneeNPV))
                    
                else :
                    missing_money_actif_invest = 0
                
                puissance = actif.puissance
                fc = facteur_de_charge_mecapa(actif, annee_livraison, donnees_entree)

                anticipation_revenus_capacitaires = np.array([ missing_money_actif_invest  * (1+taux_actualisation)**(-n) for n in range(1,nbAnneeNPV)]).sum()

                df_bid_mecapa_ambiance.loc["%s_invest"%actif.cle] = [actif.cle, missing_money_actif_invest/(puissance*fc), puissance, fc,nb_unite_invest, investissement_initial/puissance, couts_fixes_maintenance/puissance, VAN_revenus_energie/puissance, prime_risque_energie/puissance, anticipation_revenus_capacitaires/(puissance*fc) ]
        
            
        # La courbe de demande est estimée par le TSO de manière exogène
        demande_capacite_apres_horizon_ambiance = donnees_entree.data_frame_capacite_cible.at[annee_livraison, ambiance]

        # La courbe d'offre est construite de manière endogène à partir du calcul des missings money des actifs éligibles au mécanisme de capacité
        capacite_laureate_apres_horizon_prevision, prix_capacite_apres_horizon_prevision, df_actifs_laureats_mecapa_ambiance = enchere_mecanisme_capacite(donnees_entree, demande_capacite_apres_horizon_ambiance, df_bid_mecapa_ambiance)     
        
        anticipation_prix_capacite = dict()
        anticipation_prix_capacite["prix_capacite"] = prix_capacite_apres_horizon_prevision
        anticipation_prix_capacite["capacite_laureate"] = capacite_laureate_apres_horizon_prevision
        
        dico_anticipation_prix_capacite_ambiance = dict() 
        dico_anticipation_prix_capacite_ambiance[annee_livraison] = anticipation_prix_capacite
        dico_anticipation_prix_capacite[ambiance] = dico_anticipation_prix_capacite_ambiance
        
        numero_ambiance += 1
    
    nb_ambiance = len(dico_anticipation_prix_capacite)
    dico_anticipation_prix_capacite_moyen[annee_livraison] = {"prix_capacite" : 0, "capacite_laureate" : 0}
    for ambiance in dico_anticipation_prix_capacite.keys() :
        dico_anticipation_prix_capacite_moyen[annee_livraison]["capacite_laureate"] += dico_anticipation_prix_capacite[ambiance][annee_livraison]["capacite_laureate"]/nb_ambiance
        dico_anticipation_prix_capacite_moyen[annee_livraison]["prix_capacite"] += dico_anticipation_prix_capacite[ambiance][annee_livraison]["prix_capacite"]/nb_ambiance
        
    print(annee_livraison, " : ", dico_anticipation_prix_capacite_moyen[annee_livraison])
    # Une fois qu'on a l'anticipation du prix de la capacité pour les années suivant l'anticipation il suffit de remonter le temps jusqu'au début de notre anticipation 
    for i in range (annee_fin_anticipation - annee_debut_anticipation_capacite - 1) :
        # L'année courante commence par l'année fin anticipation et diminue à chaque incrémentation jusque l'annnée début anticipation 
        annee_livraison = annee_fin_anticipation - 2 - i

        numero_ambiance = 0
        for ambiance in donnees_entree.ambiances :    
     
        
            # On construit deux data frame : une première pour les actifs qui sont investies chaque année et une deuxième pour les actifs qui restent chaque année (cela va permettre de calculer le bon MM dans chaque cas)
            parc_ambiance_horizon_prevision = (dico_df_nb_unites_ambiances[ambiance]).head(annee_fin_anticipation)
    ######################################################################################################################################################################################
    ######################### A modifier pour prendre en compte la possibilité d'avoir des actifs qui sont ajoutables et démentelables (travailler avec les registres d'ouverture et de fermeture)
                
            parc_investissement_ambiance_horizon_prevision = pd.DataFrame(index = parc_ambiance_horizon_prevision.index, columns = parc_ambiance_horizon_prevision.columns).fillna(0)
            parc_qui_se_conserve_ambiance_horizon_prevision = pd.DataFrame(index = parc_ambiance_horizon_prevision.index, columns = parc_ambiance_horizon_prevision.columns).fillna(0)
            diff = parc_ambiance_horizon_prevision.diff().fillna(0)
            
            for techno in parc_ambiance_horizon_prevision.columns : 
                for annee in parc_ambiance_horizon_prevision.index : 
                    if diff.at[annee, techno] == 0 :
                        parc_qui_se_conserve_ambiance_horizon_prevision.at[annee, techno] = parc_ambiance_horizon_prevision.at[annee, techno]
                    if diff.at[annee, techno] > 0 :
                        parc_investissement_ambiance_horizon_prevision.at[annee, techno] = diff.at[annee, techno]
                        if parc_ambiance_horizon_prevision.at[annee, techno] > 0 :
                            parc_qui_se_conserve_ambiance_horizon_prevision.at[annee, techno] = parc_ambiance_horizon_prevision.at[annee-1, techno]
                    if diff.at[annee, techno] < 0 :
                        parc_qui_se_conserve_ambiance_horizon_prevision.at[annee, techno] = parc_ambiance_horizon_prevision.at[annee, techno]
                        
            if  parc_investissement_ambiance_horizon_prevision.at[annee_debut_anticipation_capacite - 1, actif_ajoute.cle] == 0 :       
                parc_investissement_ambiance_horizon_prevision.at[annee_debut_anticipation_capacite - 1, actif_ajoute.cle] += 1 
                parc_qui_se_conserve_ambiance_horizon_prevision.at[annee_debut_anticipation_capacite - 1, actif_ajoute.cle] -= 1 
                  
            # détermination du missing money des actifs existants éligibles au mécanisme de capacité
            df_bid_mecapa_ambiance = pd.DataFrame(columns = ["actif", "bid", "capacite", 'fc', 'nbr_unite', 'CAPEX', 'FO&M', 'revenus_energie', 'prime_risque_energie', 'revenus_capacitaires'])
            for cle_actif in donnees_entree.data_frame_actifs_eligibles_mecapa.index :
                if not donnees_entree.data_frame_actifs_eligibles_mecapa.at[cle_actif, 'eligible'] :
                    continue
                    
                actif = donnees_entree.trouve_actif(cle_actif)
                
                puissance = actif.puissance
                
                nb_unite_invest = parc_investissement_ambiance_horizon_prevision.at[annee_livraison, actif.cle]
                nb_unite_qui_se_conservent = parc_qui_se_conserve_ambiance_horizon_prevision.at[annee_livraison, actif.cle]                
                
                if nb_unite_qui_se_conservent > 0 and actif.demantelable : 

                    if donnees_entree.df_param_mecapa.at["MM_CT", "value"] :
                        matrice_resultats_annuels_ambiance = [[matrice_resultats_annuels[numero_ambiance][annee_livraison - annee_debut_anticipation_capacite]]]
                        nbAnneeNPV = 1
                        annee_fin_calcul_NPV = annee_livraison + 1
                        anticipation_revenus_capacitaires = 0
                        
                    else : 
                        matrice_resultats_annuels_ambiance = [matrice_resultats_annuels[numero_ambiance]] 
            
                        if donnees_entree.parametres_simulation.extrapolation_EOM :
                            annee_fin_calcul_NPV = annee_livraison + actif.duree_vie
                        else : 
                            annee_fin_calcul_NPV = annee_fin_anticipation          
                        nbAnneeNPV = annee_fin_calcul_NPV - annee_livraison
                        
                        
                    taux_actualisation = actif.taux_actualisation
                    couts_fixes_maintenance =  np.array([ actif.cout_fixe_maintenance * (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum()
                    unite =  DonneesSimulation.Unite(actif, annee_livraison, actif.duree_vie) 
                    
                    matrice_revenus_unite = IndicateursEconomiques.calcul_matrice_revenus_annuels_sans_CF(unite, matrice_resultats_annuels_ambiance, annee_livraison, annee_fin_calcul_NPV, donnees_entree, donnees_simulation)
                    VAN_revenus_energie, VAN_annualisee, prime_risque_energie, liste_VAN_revenus_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_unite, taux_actualisation, donnees_entree,0,nbAnneeNPV)
                    
                    if not donnees_entree.df_param_mecapa.at["MM_CT", "value"] : 
                        anticipation_revenus_capacitaires = calcul_anticipation_revenus_capacitaires(actif, annee_livraison, annee_fin_anticipation, nbAnneeNPV, dico_anticipation_prix_capacite_moyen, donnees_entree)
                    
                    VAN_unite = VAN_revenus_energie + anticipation_revenus_capacitaires - couts_fixes_maintenance 
                    
                    if VAN_unite < 0 : 
                        missing_money_actif_divest = -VAN_unite
                        
                    else :
                        missing_money_actif_divest = 0  
                                   
                    puissance = actif.puissance
                    fc = facteur_de_charge_mecapa(actif, annee_livraison, donnees_entree)
                    
                    df_bid_mecapa_ambiance.loc["%s_divest"%actif.cle] = [actif.cle, missing_money_actif_divest/(puissance*fc), puissance, fc, nb_unite_qui_se_conservent, 0, couts_fixes_maintenance/puissance, VAN_revenus_energie/puissance, prime_risque_energie/puissance, anticipation_revenus_capacitaires/(puissance*fc)]

                
                
                if nb_unite_invest > 0 and actif.ajoutable : 
                    
                    gisement_annuel_actif = donnees_entree.data_frame_actifs_eligibles_mecapa.at[actif.cle, 'gisement_annuel']
                    if nb_unite_invest*actif.puissance > gisement_annuel_actif : 
                        nb_unite_invest = floor(gisement_annuel_actif/actif.puissance)
                
                    if donnees_entree.parametres_simulation.extrapolation_EOM :
                        annee_fin_calcul_NPV = annee_livraison + actif.duree_vie
                    else : 
                        annee_fin_calcul_NPV = annee_fin_anticipation                  
                    nbAnneeNPV = annee_fin_calcul_NPV - annee_livraison 

                    taux_actualisation = actif.taux_actualisation
                    
                    #annuite = IndicateursEconomiques.calcul_investissement_IDC_annualise(actif,annee_courante)                
                    #investissement_initial =  np.array([ annuite * (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum()                    
                    investissement_initial = actif.cout_fixe_construction(annee_livraison)
                    couts_fixes_maintenance =  np.array([ actif.cout_fixe_maintenance * (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum()
                    
                    # Création d'une unite afin de pouvoir lancer les fonctions de calcul de revenus
                    unite =  DonneesSimulation.Unite(actif, annee_livraison, annee_fin_calcul_NPV) 
                    matrice_resultats_annuels_ambiance = [matrice_resultats_annuels[numero_ambiance]]          
                    matrice_revenus_annuels_energie_unite = IndicateursEconomiques.calcul_matrice_revenus_annuels_sans_CF(unite, matrice_resultats_annuels_ambiance, annee_livraison, annee_fin_calcul_NPV, donnees_entree, donnees_simulation)
                    VAN_revenus_energie, VAN_annualisee, prime_risque_energie, liste_VAN_revenus_energie_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_annuels_energie_unite, taux_actualisation, donnees_entree,0,nbAnneeNPV)
                    
                    anticipation_revenus_capacitaires = calcul_anticipation_revenus_capacitaires(actif, annee_livraison, annee_fin_anticipation, nbAnneeNPV, dico_anticipation_prix_capacite_moyen, donnees_entree)
                    
                    VAN_unite = VAN_revenus_energie + anticipation_revenus_capacitaires - couts_fixes_maintenance - investissement_initial
    
                    if VAN_unite < 0 : 
                        missing_money_actif_invest = -VAN_unite
                        
                    else :
                        missing_money_actif_invest = 0
                    
                    puissance = actif.puissance 
                    fc = facteur_de_charge_mecapa(actif, annee_livraison, donnees_entree)

                    df_bid_mecapa_ambiance.loc["%s_invest"%actif.cle] = [actif.cle, missing_money_actif_invest/(puissance*fc), puissance, fc, nb_unite_invest, investissement_initial/puissance, couts_fixes_maintenance/puissance, VAN_revenus_energie/puissance, prime_risque_energie/puissance, anticipation_revenus_capacitaires/(puissance*fc)]
                        

                 
            demande_capacite_annee_livraison = donnees_entree.data_frame_capacite_cible.at[annee_livraison, ambiance]  
            
            capacite_laureate_annee_livraison, prix_capacite_annee_livraison, df_actifs_laureats_mecapa_ambiance = enchere_mecanisme_capacite(donnees_entree, demande_capacite_annee_livraison, df_bid_mecapa_ambiance)        

            anticipation_prix_capacite = dict()
            anticipation_prix_capacite["prix_capacite"] = prix_capacite_annee_livraison
            anticipation_prix_capacite["capacite_laureate"] = capacite_laureate_annee_livraison
            
            dico_anticipation_prix_capacite_ambiance = dico_anticipation_prix_capacite[ambiance]
            dico_anticipation_prix_capacite_ambiance[annee_livraison] = anticipation_prix_capacite
            dico_anticipation_prix_capacite[ambiance] = dico_anticipation_prix_capacite_ambiance
            
            numero_ambiance += 1
            
        dico_anticipation_prix_capacite_moyen[annee_livraison] = {"prix_capacite" : 0, "capacite_laureate" : 0}
        for ambiance in dico_anticipation_prix_capacite.keys() :
            dico_anticipation_prix_capacite_moyen[annee_livraison]["capacite_laureate"] += dico_anticipation_prix_capacite[ambiance][annee_livraison]["capacite_laureate"]/nb_ambiance
            dico_anticipation_prix_capacite_moyen[annee_livraison]["prix_capacite"] += dico_anticipation_prix_capacite[ambiance][annee_livraison]["prix_capacite"]/nb_ambiance  
        print(annee_livraison, " : ", dico_anticipation_prix_capacite_moyen[annee_livraison])
        
    return dico_anticipation_prix_capacite_moyen


def calcul_missing_money_actif_ajoutable(actif, annee_livraison, donnees_entree, donnees_simulation, indice_enchere_mecanisme_capacite, dico_df_nb_unites_ambiances) :   
    """
    Calcul le missing money de l'actif en question qu'il manque pour que l'investissement soit rentable. Pour cela, la matrice des résultats de l'année de livraison est utilisée pour avoir accès au chronique de production et des coûts marginaux de l'actif. 
    Ensuite on peut déterminer des revenus captés par l'actif qui nous permettent de déterminer le missing money grâce à : MM = Coût fixe - Revenus énergie. Si le missing money est négatif alors on renvoie 0. 

    Paramètres
    ----------
    actif : Donnees_entree.Actif
        actif pour lequel on va calculer le missing money
    annee_livraison : int
        annee courante 
    matrice_resultats_annuels_annee_courante : 
        matrice indexée par [ambiance][année][météo] qui donne le dispatch pour les différentes météo et année (ici uniquement pour l'année courante)
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    indice_enchere_mecanisme_capacite : int
        indice de la boucle du mécanisme de capacité actuelle
    dico_df_nb_unites_ambiances : dictionnaire
        dictionnaire qui contient le parc anticipé dans chacune des ambiances en cohérence avec le parc réel de l'année courante

    Retours
    -------
    missing_money_actif : float
    """   
    print("\t Calcul du Missing money pour l'investissement")     
    annee_courante = donnees_simulation.annee_courante
    dict_VAN_equivalentes = dict()
    dict_criteres_investissement = dict()
    dict_revenu_equivalent_premiere_annee_fonctionnement = dict()
    
    df_resume_evaluation = pd.DataFrame() 
            
    # l'ajout de l'actif est testé
    print("\t\t test d'ajout  d'une unité de %s" % (actif.cle))
    duree_construction = actif.duree_construction
    duree_vie = actif.duree_vie
    annee_ouverture = annee_livraison + duree_construction
    annee_fermeture = annee_ouverture + duree_vie
    unite = DonneesSimulation.Unite(actif, annee_ouverture, annee_fermeture)

    # calcul des résultats annuels pour les différentes ambiances, années et météos avec l'unité testée dans le parc
    annee_debut_anticipation_energie = annee_ouverture
    annee_debut_anticipation_capacite = annee_debut_anticipation_energie + 1
    annee_fin_anticipation = min(annee_courante + donnees_entree.parametres_simulation.horizon_prevision,
                                    annee_debut_anticipation_energie + actif.duree_vie,
                                    donnees_entree.parametres_simulation.horizon_simulation)
    
    
    if donnees_entree.parametres_simulation.extrapolation_EOM :
        annee_fin_calcul_NPV = annee_debut_anticipation_energie + actif.duree_vie
    else : 
        annee_fin_calcul_NPV = annee_fin_anticipation          
    
    nbAnneeNPV = annee_fin_calcul_NPV - annee_debut_anticipation_energie
    
    print("\t\t\t Anticipation entre les années %d (année ouverture) et %d (non incluse)"%(annee_ouverture,annee_fin_anticipation))

    dico_df_nb_unites_ambiances_test = {}

    for ambiance in donnees_entree.ambiances :
        
        if donnees_entree.parametres_simulation.test_avant_invest :
        
            df_nb_unites_ambiances_test = dico_df_nb_unites_ambiances[ambiance].copy()
            
            for k in range(annee_ouverture,annee_fermeture):
                if k in df_nb_unites_ambiances_test.index :
                    df_nb_unites_ambiances_test.at[k,actif.cle] = df_nb_unites_ambiances_test.at[k,actif.cle] + 1


        nom_fic = "DF_PA_%s_MerchMeCapa_%s_%s_test_%s.csv"%(ambiance,str(annee_courante),str(indice_enchere_mecanisme_capacite),actif.cle)    
        path_df_parc = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
        df_nb_unites_ambiances_test.to_csv(path_df_parc,sep=";")
        
        dico_df_nb_unites_ambiances_test[ambiance] = df_nb_unites_ambiances_test
    
    # realisation de l'anticipation
    
    matrice_resultats_annuels = Anticipation.anticipation_resultats_annuels_parc_exogene(annee_debut_anticipation_energie,annee_fin_anticipation, donnees_entree, donnees_simulation,dico_df_nb_unites_ambiances_test)
    
    Ecriture.ecriture_dispatch_boucle(matrice_resultats_annuels,donnees_entree,donnees_simulation,"rapport_mecanisme_capacite/%d/rapport_anticipation_actifs_ajoutable"%indice_enchere_mecanisme_capacite,0,annee_debut_anticipation_energie,actif.cle) 

    # Calcul du volume de CAPEX et OPEX fixes à prendre en compte
    
    taux_actualisation = actif.taux_actualisation
    
    #annuite = IndicateursEconomiques.calcul_investissement_IDC_annualise(actif,annee_courante)
    #investissement_initial =  np.array([ annuite* (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum()  
    investissement_initial = actif.cout_fixe_construction(annee_ouverture)
    couts_fixes_maintenance = np.array([ actif.cout_fixe_maintenance* (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum() 
    
    # Calcul de l'anticipation du prix de la capacité à partir du parc anticipé 
    dico_anticipation_prix_capacite = calcul_anticipation_prix_capacite(actif, annee_debut_anticipation_capacite, annee_fin_anticipation, donnees_entree, donnees_simulation, matrice_resultats_annuels, dico_df_nb_unites_ambiances_test)
    
    anticipation_revenus_capacitaires = calcul_anticipation_revenus_capacitaires(actif, annee_ouverture, annee_fin_anticipation, nbAnneeNPV, dico_anticipation_prix_capacite, donnees_entree)
    
    revenus_capacitaires_annualises = anticipation_revenus_capacitaires * taux_actualisation / ( 1 - (1 + taux_actualisation)**(-(nbAnneeNPV-1)))

    # Calcul des revenus annuels à partir des résultats annuels avec extrapolation éventuelle au delà de l'horizon de prévision pour couvrir la totalité de la durée de vie
    matrice_revenus_annuels = IndicateursEconomiques.calcul_matrice_revenus_annuels_sans_CF(unite, matrice_resultats_annuels, annee_ouverture, annee_fin_calcul_NPV, donnees_entree, donnees_simulation)

    VAN_revenus_energie, VAN_annualisee, prime_risque_energie, liste_VAN_revenus_energie_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_annuels, taux_actualisation, donnees_entree,0,nbAnneeNPV)    

    #print(VAN_revenus_energie/puissance, anticipation_revenus_capacitaires/puissance, couts_fixes_maintenance/puissance, investissement_initial/puissance)
    VAN_unite = VAN_revenus_energie + anticipation_revenus_capacitaires - couts_fixes_maintenance - investissement_initial

    if VAN_unite < 0 : 
        missing_money_actif_invest = -VAN_unite
        
    else :
        missing_money_actif_invest = 0
            
    return missing_money_actif_invest, VAN_revenus_energie, prime_risque_energie, anticipation_revenus_capacitaires, couts_fixes_maintenance  




def calcul_missing_money_actif_demantelable(actif, annee_livraison, donnees_entree, donnees_simulation, matrice_resultats, dico_df_nb_unites_ambiances) :   
    """
    Calcul le missing money de l'actif en question pour que le maintien en fonctionnement soit rentable et ce sur l'ensemble de la durée de vie restante de l'unité. Pour cela, la matrice des résultats de l'année de livraison est utilisée pour avoir accès au chronique de production et des coûts marginaux de l'actif. 
    Ensuite on peut déterminer des revenus captés par l'actif qui nous permettent de déterminer le missing money grâce à : MM = Coût fixe - Revenus énergie. Si le missing money est négatif alors on renvoie 0. 

    Paramètres
    ----------
    actif : Donnees_entree.Actif
        actif pour lequel on va calculer le missing money
    annee_livraison : int
        annee courante 
    matrice_resultats : 
        matrice indexée par [ambiance][année][météo] qui donne le dispatch pour les différentes météo et année 
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser
    dico_df_nb_unites_ambiances : dict
        dictionnaire contenant les dataframes représentant le parc anticipé dans chacune des ambiances

    Retours
    -------
    missing_money_actif : float
    """ 
    
    if donnees_entree.df_param_mecapa.at["MM_CT", "value"] :

        nbAnneeNPV = 1
        annee_fin_calcul_NPV = annee_livraison + 1
        anticipation_revenus_capacitaires = 0


    else : 
        annee_fin_anticipation = min(annee_livraison + donnees_entree.parametres_simulation.horizon_prevision,
                                        annee_livraison + actif.duree_vie,
                                        donnees_entree.parametres_simulation.horizon_simulation)
        
        
        if donnees_entree.parametres_simulation.extrapolation_EOM :
            annee_fin_calcul_NPV = annee_livraison + actif.duree_vie
        else : 
            annee_fin_calcul_NPV = annee_fin_anticipation          
        
        nbAnneeNPV = annee_fin_calcul_NPV - annee_livraison
        
        #Calcul des revenus capacitaires
        dico_anticipation_prix_capacite = calcul_anticipation_prix_capacite(actif, annee_livraison + 1, annee_fin_anticipation, donnees_entree, donnees_simulation, matrice_resultats, dico_df_nb_unites_ambiances)
        anticipation_revenus_capacitaires = calcul_anticipation_revenus_capacitaires(actif, annee_livraison, annee_fin_anticipation, nbAnneeNPV, dico_anticipation_prix_capacite, donnees_entree)
        revenus_capacitaires_annualises = anticipation_revenus_capacitaires * actif.taux_actualisation / ( 1 - (1 + actif.taux_actualisation)**(-(nbAnneeNPV-1)))
    
    
    # Il suffit de regarder les revenus d'une seule unité car cela sera pareil pour toutes les unités de cet actif
    unite =  DonneesSimulation.Unite(actif, annee_livraison, actif.duree_vie) 
    
    # Calcul des FO&M
    taux_actualisation = actif.taux_actualisation
    couts_fixes_maintenance = np.array([ actif.cout_fixe_maintenance* (1+taux_actualisation)**(-n) for n in range(nbAnneeNPV)]).sum()
    
    # Calcul des revenus énergie
    matrice_revenus_unite = IndicateursEconomiques.calcul_matrice_revenus_annuels_sans_CF(unite, matrice_resultats, annee_livraison, annee_fin_calcul_NPV, donnees_entree, donnees_simulation)
    VAN_revenus_energie, VAN_annualisee, prime_risque_energie, liste_VAN_revenus_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_unite, taux_actualisation, donnees_entree,0,nbAnneeNPV)
    
    # Calcul de la VAN totale du projet
    VAN_unite = VAN_revenus_energie + anticipation_revenus_capacitaires - couts_fixes_maintenance
    
    if VAN_unite < 0 : 
        missing_money_actif_divest = -VAN_unite
        
    else :
        missing_money_actif_divest = 0  
            
    return missing_money_actif_divest, VAN_revenus_energie, prime_risque_energie, anticipation_revenus_capacitaires, couts_fixes_maintenance   




def calcul_missing_money_actif_demantelable_v0(actif, annee_livraison, donnees_entree, donnees_simulation, matrice_resultats_annuels_annee_livraison) :   
    """
    Calcul le missing money de l'actif en question pour que le maintien en fonctionnement soit rentable. Pour cela, la matrice des résultats de l'année de livraison est utilisée pour avoir accès au chronique de production et des coûts marginaux de l'actif. 
    Ensuite on peut déterminer des revenus captés par l'actif qui nous permettent de déterminer le missing money grâce à : MM = Coût fixe - Revenus énergie. Si le missing money est négatif alors on renvoie 0. 

    Paramètres
    ----------
    actif : Donnees_entree.Actif
        actif pour lequel on va calculer le missing money
    annee_livraison : int
        annee courante 
    matrice_resultats_annuels_annee_livraison : 
        matrice indexée par [ambiance][année][météo] qui donne le dispatch pour les différentes météo et année (ici uniquement pour l'année de livraison)
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser

    Retours
    -------
    missing_money_actif : float
    """       
    # Il suffit de regarder les revenus d'une seule unité car cela sera pareil pour toutes les unités de cet actif
    unite =  DonneesSimulation.Unite(actif, annee_livraison, actif.duree_vie) 
    
    #Calcul des revenus énergie
    matrice_revenus_annuels_annee_livraison_unite = IndicateursEconomiques.calcul_matrice_revenus_annuels_sans_CF(unite, matrice_resultats_annuels_annee_livraison, annee_livraison, annee_livraison + 1, donnees_entree, donnees_simulation)
    
    # Calcul de la VAN du projet
    nbAnneeNPV = 1
    VAN_revenus_energie, VAN_annualisee, prime_risque_energie, liste_VAN_revenus_possibles = IndicateursEconomiques.calcul_VAN_equivalente(matrice_revenus_annuels_annee_livraison_unite, unite.actif.taux_actualisation, donnees_entree,0,nbAnneeNPV)
    
    VAN_unite = VAN_revenus_energie - actif.cout_fixe_maintenance
    
    if VAN_unite < 0 : 
        missing_money_actif_divest = -VAN_unite
        
    else :
        missing_money_actif_divest = 0  
            
    return missing_money_actif_divest, VAN_revenus_energie, prime_risque_energie  









def sequence_mecanisme_capacite(donnees_entree, donnees_simulation) : 
    """
    Cette fonction effectue la séquence du Mécanisme de capacité annuel et renvoie le rapport associé.

    Paramètres
    ----------
    donnees_entree : DonneesEntree.DonneesEntree
        données d'entrée à utiliser
    donnees_simulation : DonneesSimulation.DonneesSimulation
        données de simulation à utiliser, ce paramètre est modifié par la fonction

    Retours
    -------
    dict_rapport_mecanisme_capacite : dict
        dictionnaire contenant les rapports de la séquence de Mécanisme de capacité
    """
    
    
    annee_courante = donnees_simulation.annee_courante
    idx_fin = (donnees_entree.parametres_simulation.horizon_simulation-1)
    continuer_mecanisme_capacite = True
    dict_rapports_mecanisme_capacite = {}
    indice_enchere_mecanisme_capacite = 0
    
    ################################################################################################################################################################
    ######################################### Modifier cette valeur ################################################################################################
    capacite_investissement_argent = donnees_entree.df_param_mecapa.at["budget_annuel_investissement", "value"]
    capacite_investissement_puissance = donnees_entree.df_param_mecapa.at["capacite_maximale_investissement", "value"]

    dico_parcs_anticipes_boucle = donnees_entree.get_parc_anticipation()    
    
    ### Debut du mécanisme de capacité 
    
    while (continuer_mecanisme_capacite):
        
        if annee_courante == 0 : 
            annee_livraison = annee_courante + indice_enchere_mecanisme_capacite
            
        else : 
            annee_livraison = annee_courante + donnees_entree.df_param_mecapa.at["horizon_enchere", "value"] 
            
        if annee_livraison > donnees_entree.parametres_simulation.horizon_simulation - 1 :
            print("\t Toutes les enchères de l'horizon de simulation ont été réalisées")
            rapport_mecanisme_capacite = RapportMecanismeCapacite(0, 0, 0, 0, pd.DataFrame(), pd.DataFrame())
            dict_rapports_mecanisme_capacite[annee_livraison] = rapport_mecanisme_capacite
            break
            

        print("\n   ENCHERE N°%d DE L'ANNEE %d : ANNEE DE LIVRAISON %d" % (indice_enchere_mecanisme_capacite, annee_courante, annee_livraison))

        # selection des actifs eligibles selon les capacités d'investissement et de gisement
        # et calcul du nombre maximum d'unités dans lesquelles il est possible d'investir
        liste_actifs_mecanisme_capacite, dict_nombre_max_unites = selection_actifs_mecanisme_capacite(capacite_investissement_argent, capacite_investissement_puissance, donnees_entree, donnees_simulation)


        df_nb_unites_parc_reel = donnees_simulation.parc.get_df_nb_unites().loc[0:idx_fin]
        
        nom_fic = "DF_PR_MeCapa_%s_%s.csv"%(str(annee_courante),str(indice_enchere_mecanisme_capacite))    
        path_df_parc_reel = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
        df_nb_unites_parc_reel.to_csv(path_df_parc_reel,sep=";")
     
        # anticipation des résultats annuels pour la prochaine année de fonctionnement
        
        if donnees_entree.parametres_simulation.anticipation_parc_exogene :

            dico_parcs_annee_courante = {}
            
            for ambiance in donnees_entree.ambiances :
            
                
                if donnees_entree.parametres_simulation.anticipation_investissement :
              
                    dico_df_nb_unites_ambiances = donnees_entree.mise_en_coherence_parc(annee_livraison,
                                                                                        dico_parcs_anticipes_boucle,
                                                                                        donnees_simulation.parc,
                                                                                        add_current_investment=True)
                
                else : 
                
                    dico_df_nb_unites_ambiances = donnees_entree.mise_en_coherence_parc(annee_livraison,
                                                                                        dico_parcs_anticipes_boucle,
                                                                                        donnees_simulation.parc,
                                                                                        add_current_investment=False)                
                
                nom_fic = "DF_PA_%s_MeCapa_%s_%s.csv"%(ambiance,str(annee_courante),str(indice_enchere_mecanisme_capacite))    
                path_df_parc_reel = os.path.join(donnees_entree.dossier_sortie,"parc_vision",nom_fic)
                dico_df_nb_unites_ambiances[ambiance].to_csv(path_df_parc_reel,sep=";")
                
            print("\t Calcul du Missing money pour le désinvestissement")
            if donnees_entree.df_param_mecapa.at["MM_CT", "value"] :    
                matrice_resultats = Anticipation.anticipation_resultats_annuels_parc_exogene(annee_livraison, annee_livraison+1, donnees_entree, donnees_simulation,dico_df_nb_unites_ambiances)
    
                Ecriture.ecriture_dispatch_boucle(matrice_resultats,donnees_entree,donnees_simulation,"rapport_mecanisme_capacite/%d/rapport_anticipation_actifs_existants"%indice_enchere_mecanisme_capacite,0,annee_courante)
                
            else : 
            
                annee_fin_anticipation = min(annee_livraison + donnees_entree.parametres_simulation.horizon_prevision,
                                    donnees_entree.parametres_simulation.horizon_simulation)
                                    
                matrice_resultats = Anticipation.anticipation_resultats_annuels_parc_exogene(annee_livraison, annee_fin_anticipation, donnees_entree, donnees_simulation,dico_df_nb_unites_ambiances)
    
                Ecriture.ecriture_dispatch_boucle(matrice_resultats,donnees_entree,donnees_simulation,"rapport_mecanisme_capacite/%d/rapport_anticipation_actifs_existants"%indice_enchere_mecanisme_capacite,0,annee_courante)
            
        else : 
        
            print("\t\t Anticipation des résultats pour l'année courante (utilisation du parc existant): année %s"%(annee_courante))
            
            matrice_resultats_annuels_annee_courante = Anticipation.anticipation_resultats_annuels(annee_courante, annee_courante+1, donnees_entree, donnees_simulation)

            
            Ecriture.ecriture_dispatch_boucle(matrice_resultats_annuels_annee_courante,donnees_entree,donnees_simulation,"rapport_mecanisme_capacite/%d/rapport_mecapa_actifs_existants"%indice_enchere_mecanisme_capacite,0,annee_courante)
            
            donnees_simulation.parc.print_parc("Annee %d - Boucle Mecanisme de capacité %d - Parc annee courante" % (annee_courante ,indice_enchere_mecanisme_capacite ))  
         
            
        # détermination du missing money des actifs existants éligibles au mécanisme de capacité
        df_bid_mecapa = pd.DataFrame(columns = ["actif", "bid", "capacite", 'fc', 'nbr_unite', 'CAPEX', 'FO&M', 'revenus_energie', 'prime_risque_energie', 'revenus_capacitaires'])
        
        for cle_actif in donnees_simulation.parc.get_df_nb_unites().columns:

            actif = donnees_entree.trouve_actif(cle_actif)
            if not actif.eligible_mecanisme_capacite :
                continue      
           
            if actif.demantelable : 

                nbr_unite = donnees_simulation.parc.nombre_unites(actif.cle, annee_livraison)
                if nbr_unite  > 0 :
                
                    missing_money_actif_divest, revenus_energie_anticipe, prime_risque_unite, anticipation_revenus_capacitaires, couts_fixes_maintenance = calcul_missing_money_actif_demantelable(actif, annee_livraison, donnees_entree, donnees_simulation, matrice_resultats, dico_df_nb_unites_ambiances)

                    puissance = actif.puissance
                    fc = facteur_de_charge_mecapa(actif, annee_livraison, donnees_entree)
                    
                    df_bid_mecapa.loc["%s_divest"%actif.cle] = [actif.cle, missing_money_actif_divest/(puissance*fc), puissance, fc, nbr_unite, 0, couts_fixes_maintenance/puissance, revenus_energie_anticipe/puissance, prime_risque_unite/puissance, anticipation_revenus_capacitaires/(puissance*fc)]
                        
                        
                
            if actif.ajoutable : 
            
                puissance = actif.puissance
                fc = facteur_de_charge_mecapa(actif, annee_livraison, donnees_entree)
                
                nbr_unite = ceil(donnees_entree.data_frame_capacite_cible.at[annee_livraison, "reference"]/puissance)
                
                gisement_annuel_actif = donnees_entree.data_frame_actifs_eligibles_mecapa.at[actif.cle, 'gisement_annuel']
                if nbr_unite*actif.puissance > gisement_annuel_actif : 
                    nbr_unite = floor(gisement_annuel_actif/actif.puissance)
                
                if nbr_unite > 0 : 
                
                    missing_money_actif_invest, VAN_revenus_energie, prime_risque_energie, anticipation_revenus_capacitaires, couts_fixes_maintenance = calcul_missing_money_actif_ajoutable(actif, annee_livraison, donnees_entree, donnees_simulation, indice_enchere_mecanisme_capacite, dico_df_nb_unites_ambiances)
                    
                    investissement_initial = actif.cout_fixe_construction(annee_livraison + actif.duree_construction)
                    
                    df_bid_mecapa.loc["%s_invest"%actif.cle] = [actif.cle, missing_money_actif_invest/(puissance*fc), puissance, fc, nbr_unite, investissement_initial/puissance, couts_fixes_maintenance/puissance, VAN_revenus_energie/puissance, prime_risque_energie/puissance, anticipation_revenus_capacitaires/(puissance*fc)]


        print(df_bid_mecapa.loc[:,["bid", "capacite", 'fc', 'nbr_unite', 'revenus_energie', 'revenus_capacitaires']])
        # La courbe de demande est estimée par le TSO de manière exogène (le calcul est tout de même fait au sein d'Antigone pour éviter les erreurs à partir d'un critère dans la table de paramètre du MeCapa)
        demande_capacite_annee_livraison = donnees_entree.data_frame_capacite_cible.at[annee_livraison, "reference"]
        
        # La courbe d'offre est construite de manière endogène à partir du calcul des missings money des actifs éligibles au mécanisme de capacité
        capacite_laureate_totale_enchere, prix_capacite_enchere, df_actifs_laureats_mecapa = enchere_mecanisme_capacite(donnees_entree, demande_capacite_annee_livraison, df_bid_mecapa)
            
        # Une fois l'enchère réalisée, il faut fermer les unités existantes qui n'ont pas été retenue et qui ont un Missing money positif
                
##############################################################################################################################################################
################### Il faut gérer les cas où il y a des actifs avec un MM nul qui ne sont pas retenus par le mecapa pour les garder tout de même (trop d'unité avec MM nul pour la demande)
        df_actifs_non_laureats = df_bid_mecapa   
        
        idx = donnees_simulation.df_resume.index.max()+1
            
        for actif_laureat in df_actifs_laureats_mecapa.index :
            df_actifs_non_laureats.at[actif_laureat, 'nbr_unite'] -= df_actifs_laureats_mecapa.at[actif_laureat, 'nbr_unite']
            
            if '_invest' in actif_laureat : 
                cle_actif = df_actifs_laureats_mecapa.at[actif_laureat, "actif"]
                actif = donnees_entree.trouve_actif(cle_actif)
                nbr_unite_a_ouvrir = int(df_actifs_laureats_mecapa.at[actif_laureat, 'nbr_unite'])
                     
                annee_ouverture = annee_livraison + actif.duree_construction
                print("\t\t ajout de %d unités de %s pour une ouverture en année %d\n" % (nbr_unite_a_ouvrir, actif.cle, annee_ouverture))
                annee_fermeture = annee_ouverture + actif.duree_vie
                for indice_unite_ajoutee in range(nbr_unite_a_ouvrir):
                    unite_ajoutee = DonneesSimulation.Unite(actif, annee_ouverture, annee_fermeture)
                    donnees_simulation.parc.ajout_unite(unite_ajoutee)
                    
                
                donnees_simulation.df_resume.at[idx,"step"] = "adding_%d_%s"%(nbr_unite_a_ouvrir, actif.cle)
                donnees_simulation.df_resume.at[idx,"tech"] = cle_actif
                donnees_simulation.df_resume.at[idx,"module"] = "MerchInvest"
                donnees_simulation.df_resume.at[idx,"year"] = annee_courante                 
                donnees_simulation.df_resume.at[idx,"loop"] = indice_enchere_mecanisme_capacite  
        
        idx = donnees_simulation.df_resume.index.max()+1
        
        for actif_non_laureat in df_actifs_non_laureats.index : 

            if '_divest' in actif_non_laureat : 
                cle_actif = df_actifs_non_laureats.at[actif_non_laureat, "actif"]
                liste_unite_actif_non_laureat  = donnees_simulation.parc.unites_actives( cle_actif, annee_livraison)
                nbr_unite_a_fermer = int(df_actifs_non_laureats.at[actif_non_laureat, 'nbr_unite'])
                               
                for indice_unite_fermee in range(nbr_unite_a_fermer) :    
                    donnees_simulation.parc.fermeture_anticipee_plus_lointaine(cle_actif, annee_livraison)
    
                print("\t\t %d unités de %s démantelées"%(nbr_unite_a_fermer, cle_actif))
                donnees_simulation.df_resume.at[idx,"step"] = "MeCapa_closure_%d_%s"%(nbr_unite_a_fermer, cle_actif)
                donnees_simulation.df_resume.at[idx,"tech"] = cle_actif
                donnees_simulation.df_resume.at[idx,"module"] = "DivestMeCapa"
                donnees_simulation.df_resume.at[idx,"year"] = annee_courante
                donnees_simulation.df_resume.at[idx,"loop"] = indice_enchere_mecanisme_capacite 
            
            
        # enregistrement du rapport du Mécanisme de Capacité
        horizon = donnees_entree.df_param_mecapa.at["horizon_enchere", "value"]
        capacite_laureate = capacite_laureate_totale_enchere
        prix_capacite = prix_capacite_enchere
        rapport_mecanisme_capacite = RapportMecanismeCapacite(annee_courante, annee_livraison, capacite_laureate, prix_capacite, df_actifs_laureats_mecapa, df_actifs_non_laureats)
        
        dict_rapports_mecanisme_capacite[annee_livraison] = rapport_mecanisme_capacite      
                
        indice_enchere_mecanisme_capacite += 1
        
        if annee_livraison == annee_courante + donnees_entree.df_param_mecapa.at["horizon_enchere", "value"] :
            continuer_mecanisme_capacite = False  
        
        
    return dict_rapports_mecanisme_capacite
        # Il faut ensuite indiquer que les actifs laureats vont recevoir un complément de revenu égal au prix de la capacité déterminé lors de l'enchère 
        
        # Si le prix de la capacité est nul, le calcul des revenus est le même
        
        
        # Si le prix est non nul , cela signifie que le MM marginal est positif
        # Les actifs lauréats recoivent donc le MM. 
        # Remarque : Il n'existe aucune situation où pour un même actif, certaines unités lauréates vont rester ouvertes avec un prix de la capa non nul et d'autres (du même actif) qui n'auraient pas été lauréates. En effet, si elles ne sont pas lauréates et que le prix de la capacité est non nul, cela signifie que leur MM est positif et que donc elles ne sont pas rentables sans le complément capacitaire --> elles ferment 
        # Il n'y a donc pas besoin de faire un calcul différent des revenus en fonction des unités d'un même actif. Soit l'actif et toutes ses unités touchent un complément capacitaire non nul, soient aucune unité n'en touche. 
            
            
        
        
        
        





         