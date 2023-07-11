# -*- coding: utf-8 -*-
# AnTIGonE – Copyright 2020 EDF

import numpy as np
import os
import sys
import pandas as pd

class Unite:
    """
    Cette classe représente une unité de production.

    Attributs
    ---------
    actif : DonneesEntree.Actif
        type d'actif auquel appartient l'unité
    annee_ouverture : int
        année d'ouverture de l'unité
    annee_fermeture : int
        année de fermeture de l'unité
    contrat : Contrats.Contrat
        contrat dont bénéficie l'unité, la valeur sera None s'il n'y en a aucun
    nombre_annees_consecutives_fermeture_anticipee_envisagee : int
        compte des années consécutives où la fermeture anticipée de l'unité a été envisagée
    derniere_annee_fermeture_anticipee_envisagee : int
        dernière année à laquelle la fermeture anticipée de l'unité a été envisagée
    """

    def __init__(self, actif, annee_ouverture, annee_fermeture, contrat=None):
        self.actif = actif
        self.annee_ouverture = annee_ouverture
        self.annee_fermeture = annee_fermeture
        self.contrat = contrat

        # attributs utilisés pour tenir le compte des délais de fermeture
        self.nombre_annees_consecutives_fermeture_anticipee_envisagee = 0
        self.derniere_annee_fermeture_anticipee_envisagee = -1


class Parc:
    """
    Cette classe représente le parc de production.

    Attributs
    ---------
    _registre_unites_ouvertes : dict
        dictionnaire contenant, pour chaque type d'actif, le tableau annuel des listes d'unités ouvertes
    _registre_unites_actives : dict
        dictionnaire contenant, pour chaque type d'actif, le tableau annuel des listes d'unités actives
    _memorisation_tests_ajout_unite : list
        liste des unités ajoutées au parc en tant que test, mémorisées en vue de les retirer si besoin

    Méthodes
    --------
    _calcul_registre_unites_actives(self, cle_actif, annee_depart=0)
        Met à jour _registre_unites_actives à partir de _registre_unites_ouvertes.
    nombre_unites(self, cle_actif, annee)
        Retourne le nombre d'unités de l'actif correspondant à la clé actives dans le parc à l'année donnée.
    unites_actives(self, cle_actif, annee)
        Retourne la liste des unités de l'actif correspondant à la clé actives dans le parc à l'année donnée.
    nombre_unites_ouvertes(self, cle_actif, annee)
        Retourne le nombre d'unités de l'actif correspondant à la clé ouvertes à l'année donnée.
    unites_ouvertes(self, cle_actif, annee)
        Retourne la liste des unités de l'actif correspondant à la clé ouvertes dans le parc à l'année donnée.
    ajout_unite(self, unite)
        Ajoute l'unité donnée au parc.
    retrait_unite(self, unite)
        Retire l'unité donnée du parc.
    test_ajout_unite(self, unite)
        Ajoute l'unité donnée au parc en la mémorisant pour pouvoir annuler le test ultérieurement.
    annule_tests(self)
        Retire du parc toutes les unités ajoutées par la méthode test_ajout_unite().
    fermeture_anticipee_unite(self, unite, annee)
        Provoque la fermeture de l'unité donnée à l'année souhaitée.
    toutes_unites(self)
        Renvoie la liste de toutes les unités du parc, tous actifs et toutes années confondues.
    _initialisation_registres(self, parc_initial, registre_ouverture_initial, registre_fermeture_initial, donnees_entree
    )
        Initialise les registres du parc à partir des éléments issus de la lecture des données d'entrée.
    """

    def __init__(self, parc_initial, registre_ouverture_initial, registre_fermeture_initial, donnees_entree):

        # attribut permettant d'accéder aux unites ouvertes par cle d'actif et par annee
        self._registre_unites_ouvertes = dict()

        # attribut permettant d'accéder aux unites actives par cle d'actif et par annee
        self._registre_unites_actives = dict()

        # initialisation des registres
        self._initialisation_registres(parc_initial, registre_ouverture_initial, registre_fermeture_initial, donnees_entree)

        self._memorisation_tests_ajout_unite = []
        
        self.donnees_entree = donnees_entree
        
        self.registre_ouverture_initial = registre_ouverture_initial
        self.registre_fermeture_initial = registre_fermeture_initial
        
        

    def _calcul_registre_unites_actives(self, cle_actif, annee_depart=0):
        """
        Met à jour _registre_unites_actives à partir de _registre_unites_ouvertes.

        Cette méthode est appelée suite à un ajout ou un retrait d'unité du parc pour apporter les modifications
        nécessaires à _registre_unites_actives. Elle est supposée être privée et ne devrait donc pas être appelée
        en dehors des méthodes de Parc.

        Paramètres
        ----------
        cle_actif : str
            clé de l'actif dont le registre des unités actives doit être mis à jour
        annee_depart : int
            année à partir de laquelle le registre doit être mis à jour, pour les cas où la modification opérée sur le
            parc n'a d'impact sur les unités actives qu'à partir d'une certaine date
        """

        registre_unites_ouvertes = self._registre_unites_ouvertes[cle_actif]
        registre_unites_actives = self._registre_unites_actives[cle_actif]
        liste_unites_actives_annee_precedente = []
        if(annee_depart > 0):
            liste_unites_actives_annee_precedente = registre_unites_actives[annee_depart - 1]
        for annee in range(annee_depart, registre_unites_ouvertes.shape[0]):
            liste_unites_actives = []
            # les unites actives à l'année précédentes et qui ne ferment pas restent actives
            for unite in liste_unites_actives_annee_precedente:
                if(unite.annee_fermeture > annee):
                    liste_unites_actives.append(unite)
            # les unités qui ouvrent à l'année considérée sont actives si elles ne ferment pas immédiatement
            for unite_ouverte in registre_unites_ouvertes[annee]:
                if (unite_ouverte.annee_fermeture > annee):
                    liste_unites_actives.append(unite_ouverte)
            registre_unites_actives[annee] = liste_unites_actives
            liste_unites_actives_annee_precedente = liste_unites_actives

    def nombre_unites(self, cle_actif, annee):
        """
        Retourne le nombre d'unités de l'actif correspondant à la clé actives dans le parc à l'année donnée.

        Paramètres
        ----------
        cle_actif : str
            clé de l'actif dont on veut connaître le nombre d'unités
        annee : int
            année à laquelle on veut connaître le nombre d'unités

        Retours
        -------
        int
            nombre d'unités
        """

        return len(self._registre_unites_actives[cle_actif][annee])

    def get_df_nb_unites(self) :
    
        df_nb_units = pd.DataFrame()
        
        annee_debut = 0 
        annee_fin = self.donnees_entree.parametres_simulation.horizon_simulation
        for n in range(annee_debut,annee_fin):
            for actif in self.donnees_entree.tous_actifs():
            
                df_nb_units.at[n,actif.cle] = self.nombre_unites(actif.cle, n) 
        
            
        return df_nb_units
        
    def unites_actives(self, cle_actif, annee):
        """
        Retourne la liste des unités de l'actif correspondant à la clé actives dans le parc à l'année donnée.

        Paramètres
        ----------
        cle_actif : str
            clé de l'actif pour lequel on veut connaître la liste d'unités actives
        annee : int
            année à laquelle on veut connaître la liste d'unités actives

        Retours
        -------
        list
            liste des unités actives
        """

        return self._registre_unites_actives[cle_actif][annee]
        
    def nombre_unites_ouvertes(self, cle_actif, annee):
        """
        Retourne le nombre d'unités de l'actif correspondant à la clé ouvertes à l'année donnée.

        Paramètres
        ----------
        cle_actif : str
            clé de l'actif pour lequel on veut connaître le nombre d'unités ouvertes
        annee : int
            année à laquelle on veut connaître le nombre d'unités ouvertes

        Retours
        -------
        int
            nombre d'unités ouvertes
        """

        return len(self._registre_unites_ouvertes[cle_actif][annee])
    
    def print_parc(self, head,path=None):
        """
        Imprime dans la console la vision de l'évolution du parc en nombre d'unités, depuis la première année jusqu'au max en mémoire. Fonction utile pour le deboggage. 
        """
        if path == None : 
            folderPath = os.path.join(self.donnees_entree.dossier_sortie)
            filePath = os.path.join(folderPath,"parc_vision.csv")
        else : 
            folderPath = os.path.dirname(path)
            filePath = path
            
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)
            
        
                   
        if not os.path.exists(filePath):
            with open(filePath,'a') as fd:
                pass

        towrite = head + '\n'
        for cle_actif in self._registre_unites_actives.keys():
            to_print = str(cle_actif)
            towrite += str(cle_actif)
            for annee in range(0,len(self._registre_unites_ouvertes[cle_actif])):
                to_print += '   ' + str(len(self._registre_unites_actives[cle_actif][annee]))
                towrite += '; ' + str(len(self._registre_unites_actives[cle_actif][annee]))
            #print(to_print)
            towrite += '\n'



        with open(filePath,'a') as fd:
            fd.write(towrite)
            
        return


    def print_parc_df(self, head,path=None):
        """
        Imprime dans la console la vision de l'évolution du parc en nombre d'unités, depuis la première année jusqu'au max en mémoire. Fonction utile pour le deboggage. 
        """
        
        if path == None : 
            folderPath = os.path.join(self.donnees_entree.dossier_sortie)
            filePath = os.path.join(folderPath,"parc_vision.csv")
        else : 
            folderPath = os.path.dirname(path)
            filePath = path
            
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)
            
        nb_annee = self.donnees_entree.parametres_simulation.horizon_simulation
        
        df = pd.DataFrame(index=range(nb_annee))
        
        
        for cle_actif in self._registre_unites_actives.keys():

            annee_max = np.min([ len(self._registre_unites_ouvertes[cle_actif])  , nb_annee ])
            
            for n in range(annee_max):
            
                df.at[n,cle_actif] = len(self._registre_unites_actives[cle_actif][n])
                   
        df.to_csv(path,sep=";")
        
            
        return

    def update_date_fermeture(self,unite,annee):
    
    
        """
        
        Fonction très similaire à fermeture_anticipee_unite, mais utilisée pour repousser une fermeture
        (TO DO : voir s'il faut la garder)
        
        """

        actif = unite.actif
        unite.annee_fermeture = annee
        self._calcul_registre_unites_actives(actif.cle)    
    
    
    
        return None

    def unites_ouvertes(self, cle_actif, annee):
        """
        Retourne la liste des unités de l'actif correspondant à la clé ouvertes dans le parc à l'année donnée.

        Paramètres
        ----------
        cle_actif : str
            clé de l'actif pour lequel on veut connaître la liste d'unités ouvertes
        annee : int
            année à laquelle on veut connaître la liste d'unités ouvertes

        Retours
        -------
        list
            liste des unités ouvertes
        """

        return self._registre_unites_ouvertes[cle_actif][annee]

    def ajout_unite(self, unite):
        """
        Ajoute l'unité donnée au parc.

        Paramètres
        ----------
        unite : Unite
            unité à ajouter

        Retours
        -------
        bool
            True si l'unité a été ajouté avec succès, False sinon
        """

        annee_ouverture = unite.annee_ouverture
        actif = unite.actif
        registre_unites_ouvertes_actif = self._registre_unites_ouvertes[actif.cle]
        if annee_ouverture < len(registre_unites_ouvertes_actif):
            registre_unites_ouvertes_actif[annee_ouverture].append(unite)
            self._calcul_registre_unites_actives(actif.cle, annee_depart=annee_ouverture)
            return True
        return False

    def retrait_unite(self, unite):
        """
        Retire l'unité donnée du parc.

        Paramètres
        ----------
        unite : Unite
            unité à retirer, il doit s'agir du même objet que celui préalablement ajouté et non d'une instance identique

        Retours
        -------
        bool
            True si l'unité a été retirée avec succès, False sinon
        """

        annee_ouverture = unite.annee_ouverture
        actif = unite.actif
        registre_unites_ouvertes_actif = self._registre_unites_ouvertes[actif.cle]
        liste_unites_ouvertes_annee_ouverture = registre_unites_ouvertes_actif[annee_ouverture]
        for indice in range(len(liste_unites_ouvertes_annee_ouverture)):
            # parcours de la liste des unités ouvertes la même année que l'unité fournie en argument
            if(liste_unites_ouvertes_annee_ouverture[indice] is unite):
                # si on retrouve l'unité passée en argument dans la liste, on la retire et on recalcule les registres
                # il doit s'agir de la même instance d'unité (comparaison avec is) et non d'une instance identique
                liste_unites_ouvertes_annee_ouverture.pop(indice)
                self._calcul_registre_unites_actives(actif.cle, annee_depart=annee_ouverture)
                return True
        return False

    def test_ajout_unite(self, unite):
        """
        Ajoute l'unité donnée au parc en la mémorisant pour pouvoir annuler le test ultérieurement.

        Paramètres
        ----------
        unite : Unite
            unité à ajouter

        Retours
        -------
        bool
            True si l'unité a été ajouté avec succès, False sinon
        """

        # ajout de l'unité au parc en utilisant la fonction d'ajout normale
        resultat_ajout = self.ajout_unite(unite)

        if resultat_ajout:
            # mémorisation des modifications apportées si l'ajout a été fait avec succès
            self._memorisation_tests_ajout_unite.append(unite)

        return resultat_ajout

    def annule_tests(self):
        """
        Retire du parc toutes les unités ajoutées par la méthode test_ajout_unite().

        """

        for unite in self._memorisation_tests_ajout_unite:
            self.retrait_unite(unite)
        self._memorisation_tests_ajout_unite = []

    def fermeture_anticipee_unite(self, unite, annee):
        """
        Provoque la fermeture de l'unité donnée à l'année souhaitée.

        La fermeture de l'unité est reprogrammée à l'année voulue en contrôlant si la durée de vie de l'actif le permet.
        La présence de l'unité dans le parc n'est pas vérifiée.

        Paramètres
        ----------
        unite : Unite
            unité dont la fermeture est à reprogrammer, il doit s'agir du même objet que celui préalablement ajouté et
            non d'une instance identique
        annee : int
            année à laquelle on souhaite fermer l'unité

        Retours
        -------
        bool
            True si la fermeture a pu être reprogramée, False sinon
        """

        actif = unite.actif
        annee_ouverture = unite.annee_ouverture
        if(annee > annee_ouverture + actif.duree_vie):
            return False

        unite.annee_fermeture = annee
        self._calcul_registre_unites_actives(actif.cle)
        return True

    def fermeture_anticipee_plus_proche(self,cle_actif,annee):
        
        """
        
        Ferme une unité de l'actif donné pendant l'année donnée. 
        L'unité qui va être déclassée correspond à celle à qui il reste moins d'année
        de fonctionnement
        
        """
        

        # on cherche l'unité de la techno dont la date de fermeture prévues
        # est la plus proche de l'année courante
        
        fermeture_la_plus_proche = np.inf
       
        for unite in self._registre_unites_actives[cle_actif][annee] :
            if unite.annee_fermeture <= fermeture_la_plus_proche :
                fermeture_la_plus_proche = unite.annee_fermeture
                
        # maintenant que la date est connue, on supprime l'unité

        for unite in self._registre_unites_actives[cle_actif][annee] :
            if unite.annee_fermeture == fermeture_la_plus_proche :               
                unite.annee_fermeture = annee
                self._calcul_registre_unites_actives(cle_actif)
                break
                    
        return unite

    def fermeture_anticipee_plus_lointaine(self,cle_actif,annee):
        
        """
        
        Ferme une unité de l'actif donné pendant l'année donnée. 
        L'unité qui va être déclassée correspond à celle à qui il reste moins d'année
        de fonctionnement
        
        """

        # on cherche l'unité de la techno dont la date de fermeture prévues
        # est la plus proche de l'année courante
        
        fermeture_la_plus_proche = 0
       
        for unite in self._registre_unites_actives[cle_actif][annee] :
            if unite.annee_fermeture >= fermeture_la_plus_proche :
                fermeture_la_plus_proche = unite.annee_fermeture
                
        # maintenant que la date est connue, on supprime l'unité

        for unite in self._registre_unites_actives[cle_actif][annee] :
            if unite.annee_fermeture == fermeture_la_plus_proche :               
                unite.annee_fermeture = annee
                self._calcul_registre_unites_actives(cle_actif)
                break
                    
        return unite
       
        
    def toutes_unites(self):
        """
        Renvoie la liste de toutes les unités du parc, tous actifs et toutes années confondues.

        Retours
        -------
        list
            liste de toutes les unités du parc
        """

        liste_unites = []
        for cle_actif, registre_unites_ouvertes_actif in self._registre_unites_ouvertes.items():
            for liste_unites_ouvertes in registre_unites_ouvertes_actif:
                liste_unites += liste_unites_ouvertes

        return liste_unites

    def _initialisation_registres(self, parc_initial, registre_ouverture_initial, registre_fermeture_initial, donnees_entree):
        """
        Initialise les registres du parc à partir des éléments issus de la lecture des données d'entrée.

        Cette méthode est supposée être privée et ne devrait donc pas être appelée en dehors des méthodes de Parc.

        Paramètres
        ----------
        parc_initial : dict
            dictionnaire contenant, pour chaque type d'actif, le nombre d'unités présentes dans le parc initial
        registre_ouverture_initial : dict
            dictionnaire contenant, pour chaque type d'actif, le tableau annuel des ouvertures prévues initialement
        registre_fermeture_initial : dict
            dictionnaire contenant, pour chaque type d'actif, le tableau annuel des fermetures prévues initialement
        donnees_entree : DonneesEntree.DonneesEntree
            données d'entrée à utiliser
        """

        for actif in donnees_entree.tous_actifs():
            nombre_annees = donnees_entree.parametres_simulation.horizon_simulation + donnees_entree.parametres_simulation.horizon_prevision + actif.duree_construction + actif.duree_vie
            registre_unites_ouvertes_actif = np.empty(nombre_annees, dtype=list)
            registre_unites_actives_actif = np.empty(nombre_annees, dtype=list)

            # remplissage des registres par des listes vides
            for annee in range(nombre_annees):
                registre_unites_ouvertes_actif[annee] = []
                registre_unites_actives_actif[annee] = []

            # ajout des unités présentes dans le parc initial
            # et de celles dont l'ouverture est contrainte par le registre d'ouverture initial
            annees_ouverture = []
            annees_fermeture = []

            nombre_unites_initial = parc_initial[actif.cle]
            for indice_unite in range(nombre_unites_initial):
                annees_ouverture.append(0)

            registre_ouverture_initial_actif = registre_ouverture_initial[actif.cle]
            for annee in range(registre_ouverture_initial_actif.shape[0]):
                for indice_unite in range(int(registre_ouverture_initial_actif[annee])):
                    annees_ouverture.append(annee)
                       
            registre_fermeture_initial_actif = registre_fermeture_initial[actif.cle]
            for annee in range(registre_fermeture_initial_actif.shape[0]):
                for indice_unite in range(int(registre_fermeture_initial_actif[annee])):
                    annees_fermeture.append(annee)
                    
            #if(len(annees_fermeture) > len(annees_ouverture)):
            #    print("Le nombre de fermetures fournies en entrée pour %s dépasse le nombre d'unités ouvertes.\nCertaines seront ignorées."%actif.cle)

            if(len(annees_fermeture) < len(annees_ouverture)):
                # s'il y a trop peu de fermetures, on considère que les unités sont fermées après la fin du registre
                nombre_fermetures_manquantes = len(annees_ouverture) - len(annees_fermeture)
                for fermeture_manquante in range(nombre_fermetures_manquantes):
                    annees_fermeture.append(nombre_annees)

            fermetures_avancees = False
            for indice in range(len(annees_ouverture)):
                annee_ouverture = annees_ouverture[indice]
                annee_fermeture = annees_fermeture[indice]
                if(annee_fermeture - annee_ouverture > actif.duree_vie):
                    fermetures_avancees = True
                    annee_fermeture = annee_ouverture + actif.duree_vie
                unite = Unite(actif, annee_ouverture, annee_fermeture, contrat=None)
                registre_unites_ouvertes_actif[annee_ouverture].append(unite)

            #if(fermetures_avancees):
            #    print("Les dates de fermeture fournies en entrée pour %s causent des dépassements de durée de vie.\nCertaines ont été avancées."%actif.cle)

            self._registre_unites_ouvertes[actif.cle] = registre_unites_ouvertes_actif
            self._registre_unites_actives[actif.cle] = registre_unites_actives_actif
            self._calcul_registre_unites_actives(actif.cle)

    def retrait_ouveture_parc_anticipee(self,annee):
        
        """
        
        Cette fonction sert à enlever les unités ouvertes de manière exogène lors de l'année passée en argument  du parc anticipé. 
        En principe, cette fonction doit être appelée sur un objet parc correspondant au parc anticipé qui n'a pas été
        préalablement modifié.
        
        """
        
        
    
    
        return

    def get_nb_unites_actives(self,cle_actif,annee):
    
        return len(self._registre_unites_actives[cle_actif][annee])

    def get_df_nb_unites_extrapole(self, annee, k):


        df_nb_units = pd.DataFrame()

        annee_fin = self.donnees_entree.parametres_simulation.horizon_simulation

        for n in range(annee + 1):
            for actif in self.donnees_entree.tous_actifs():
                df_nb_units.at[n, actif.cle] = self.nombre_unites(actif.cle, n)

        for actif in self.donnees_entree.tous_actifs():

            x_future = np.arange(annee + 1, annee_fin)

            if actif.demantelable or actif.ajoutable:
                if annee == 0:
                    for n in range(annee + 1, annee_fin):
                        df_nb_units.at[n, actif.cle] = self.nombre_unites(actif.cle, 0)

                else:

                    x_debut = np.max([0, annee - k + 1])

                    x = np.arange(x_debut, annee + 1)
                    y = df_nb_units.loc[x_debut:annee, actif.cle]

                    reglin = stats.linregress(x, y)

                    a = reglin.slope
                    b = reglin.intercept

                    for x_f in x_future:
                        nb_unites = np.max([0, a * x_f + b])
                        nb_unites = np.rint(nb_unites)
                        df_nb_units.at[x_f, actif.cle] = nb_unites

            else:
                for x_f in x_future:
                    df_nb_units.at[x_f, actif.cle] = self.nombre_unites(actif.cle, x_f)


        return df_nb_units


class DonneesSimulation:
    """
    Cette classe regroupe les données qui permettent de décrire le déroulement d'une simulation.

    Contrairement à la classe DonneesEntree.DonneesEntree qui n'est pas supposée être modifiée, cette classe est amenée
    à évoluer à chaque étape d'une simulation.

    Attributs
    ---------
    parc : Parc
    matrice_resultats_annuels : list
        matrice indexée par [année][météo] contenant les instances de DispatchV0.ResultatAnnuel issues des dispatchs
        calculés pour l'ambiance réalisée
    liste_rapports_investissement : list
        liste des instances d'Investissement.RapportInvestissement issues des séquences d'investissement
    liste_rapports_demantelement : list
        liste des instances de Demantelement.RapportDemantelement issues des séquences de démantèlement
    liste_rapports_appels_offres_investissement : list
        liste des instances d'AppelsOffresInvestissement.RapportAppelsOffresInvestissement issues des séquences d'appels
        d'offres d'investissement
    liste_rapports_appels_offres_demantelement : list
        liste des instances d'AppelsOffresDemantelement.RapportAppelsOffresDemantelement issues des séquences d'appels
        d'offres de démantèlement
    dict_rapport_mecanisme_capacite : dict
        dictionnaire des instances de MecanismeCapacite.RapportMecanismeCapacite issues des séquences de Mécanisme de capacité
    annee_courante : int
        année courante

    Méthodes
    --------
    incrementation_annee(self, rapport_investissement, rapport_demantelement, rapport_appels_offres_investissement,
    rapport_appels_offres_demantelement, rapport_mecanisme_capacite, liste_resultats_annuels)
        Provoque le passage à l'année suivante en stockant les rapports et les résultats de l'année qui vient d'être
        simulée.
    """

    def __init__(self, parc):
        self.parc = parc
        self.matrice_resultats_annuels = []
        self.liste_rapports_investissement = []
        self.liste_rapports_demantelement = []
        self.liste_rapports_appels_offres_investissement = []
        self.liste_rapports_appels_offres_demantelement = []
        self.dict_rapports_mecanisme_capacite = {}
        self.annee_courante = 0
        
        self.df_resume = pd.DataFrame()
        self.df_resume.at[0,"step"] = "starting_ANTIGONE_run"
        

    def incrementation_annee(self, rapport_investissement, rapport_demantelement, rapport_appels_offres_investissement, rapport_appels_offres_demantelement, dict_rapport_annuel_mecanisme_capacite, liste_resultats_annuels):
        """
        Provoque le passage à l'année suivante en stockant les rapports et les résultats de l'année qui vient d'être
        simulée.

        Paramètres
        ---------- 
        rapport_investissement : Investissement.RapportInvestissement
            rapport de la séquence d'investissement de l'année courante
        rapport_demantelement : Demantelement.RapportDemantelement
            rapport de la séquence de démantèlement de l'année courante
        rapport_appels_offres_investissement : AppelsOffresInvestissement.RapportAppelsOffresInvestissement
            rapport de la séquence d'investissement par appels d'offres de l'année courante
        rapport_appels_offres_demantelement : AppelsOffresDemantelement.RapportAppelsOffresDemantelement
            rapport de la séquence de démantèlement par appels d'offres de l'année courante
        dict_rapport_annuel_mecanisme_capacite : dict
            dictionnaire contenant pour chaque année un dictionnaire contenant les rapports de la séquence du mécanisme de capacité de chaque enchère réalisée lors de l'année
        liste_resultats_annuels : list
            liste d'instances de DispatchV0.ResultatAnnuel issues des dispatchs sur les différentes météos de l'ambiance
            réalisée à l'année courante
        """

        self.liste_rapports_investissement.append(rapport_investissement)
        self.liste_rapports_demantelement.append(rapport_demantelement)
        self.liste_rapports_appels_offres_investissement.append(rapport_appels_offres_investissement)
        self.liste_rapports_appels_offres_demantelement.append(rapport_appels_offres_demantelement)
        self.dict_rapports_mecanisme_capacite[self.annee_courante] = dict_rapport_annuel_mecanisme_capacite
        
        self.matrice_resultats_annuels.append(liste_resultats_annuels)

        self.annee_courante += 1
        



