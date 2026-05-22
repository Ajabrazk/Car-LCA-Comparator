import pandas as pd
from src.voiture import Voiture

class ACVHandler:
    def __init__(self, fichier_excel):
        self.fichier = fichier_excel
        self.facteurs_emission = {}
        self.liste_voitures = []
        self.indicateurs_disponibles =[]
        self.loadData()

    def getVoitures(self):
        return self.liste_voitures
        
    def getIndicateurs(self):
        return self.indicateurs_disponibles

    def getFacteur(self, nom_facteur, indicateur):
        if nom_facteur in self.facteurs_emission:
            if indicateur in self.facteurs_emission[nom_facteur]:
                return self.facteurs_emission[nom_facteur][indicateur]
        return 0.0

    def parseFloat(self, valeur):
        try:
            valeur_texte = str(valeur).replace(',', '.')
            if valeur_texte == "" or valeur_texte == "nan":
                return 0.0
            return float(valeur_texte)
        except:
            return 0.0

    def loadData(self):
        # 1. Chargement des Facteurs d'Emission
        df_facteurs = pd.read_excel(self.fichier, sheet_name="Emission factor")
        df_facteurs.columns = df_facteurs.columns.astype(str).str.strip()
        df_facteurs = df_facteurs.dropna(subset=['Index'])
        
        # --- SELECTION DES INDICATEURS PERTINENTS ---
        self.indicateurs_disponibles = [
            "Climate change",
            "Particulate matter formation",
            "Material resources: metals/minerals",
            "Energy ressources: non-renewable"
        ]
        
        for index, row in df_facteurs.iterrows():
            nom = str(row['Index']).strip()
            self.facteurs_emission[nom] = {}
            for ind in self.indicateurs_disponibles:
                if ind in df_facteurs.columns:
                    self.facteurs_emission[nom][ind] = self.parseFloat(row.get(ind))
                else:
                    self.facteurs_emission[nom][ind] = 0.0

        # 2. Chargement des parametres (Tableau du Haut)
        df_voitures = pd.read_excel(self.fichier, sheet_name="Car parameters")
        df_voitures.columns = df_voitures.columns.astype(str).str.strip()
        
        # 3. Chargement des TTW (Le tableau du bas, place dans le 2eme onglet)
        try:
            df_ttw = pd.read_excel(self.fichier, sheet_name="Car parameters v2")
            df_ttw.columns = df_ttw.columns.astype(str).str.strip()
        except:
            print("Erreur : L'onglet 'Car parameters v2' est introuvable.")
            df_ttw = pd.DataFrame()

        # SECURITE ABSOLUE : On utilise les positions (index) pour les 3 premieres colonnes 
        # car elles n'ont pas toujours de nom dans l'Excel de Lea
        col_seg = df_voitures.columns[0]   # Colonne des tailles (Small, Medium...)
        col_fuel = df_voitures.columns[1]  # Colonne des moteurs (Petrol, BEV...)
        col_choice = df_voitures.columns[2] # Colonne des scenarios (Current, 2050...)

        # Nettoyage des cellules fusionnees
        df_voitures[col_fuel] = df_voitures[col_fuel].ffill()
        df_voitures[col_seg] = df_voitures[col_seg].ffill()
        df_voitures[col_choice] = df_voitures[col_choice].ffill()
            
        df_voitures = df_voitures.fillna(0.0)
        df_ttw = df_ttw.fillna(0.0)

        # 4. Lecture simultanee des deux tableaux
        for i in range(len(df_voitures)):
            row_voit = df_voitures.iloc[i]
            
            tech_base = str(row_voit.get(col_fuel, "")).strip()
            segment = str(row_voit.get(col_seg, "")).strip()
            choice = str(row_voit.get(col_choice, "")).strip()
            
            # Ignorer les lignes vides
            if tech_base in ["0.0", "nan", ""] or segment in ["0.0", "nan", ""]:
                continue

            # Filtrer le test d'homologation des hybrides (Maintenant ca va marcher !)
            if tech_base == "PHEV-petrol" and choice == "Homologation test":
                continue

            nom_affichage = tech_base
            if choice and choice not in ["0.0", "nan"]:
                nom_affichage = tech_base + " (" + choice + ")"

            # Recuperation securisee du dictionnaire TTW
            dico_ttw = {}
            if i < len(df_ttw):
                row_ttw = df_ttw.iloc[i]
                for ind in self.indicateurs_disponibles:
                    if ind in df_ttw.columns:
                        dico_ttw[ind] = self.parseFloat(row_ttw.get(ind))
                    else:
                        dico_ttw[ind] = 0.0

            nouvelle_voiture = Voiture(
                tech_base, nom_affichage, segment,
                self.parseFloat(row_voit.get("Vehicle mass")),
                self.parseFloat(row_voit.get("Battery capacity")),
                self.parseFloat(row_voit.get("Battery mass")),
                self.parseFloat(row_voit.get("WTT")),
                self.parseFloat(row_voit.get("PHEV WTT")),
                self.parseFloat(row_voit.get("Fuel cell")),
                self.parseFloat(row_voit.get("Road")),
                self.parseFloat(row_voit.get("Road maintenance")),
                self.parseFloat(row_voit.get("Maintenance")),
                dico_ttw, 
                self.parseFloat(row_voit.get("Tyre wear")),
                self.parseFloat(row_voit.get("Brake wear"))
            )
            
            if nouvelle_voiture.isValid():
                self.liste_voitures.append(nouvelle_voiture)

    def calculerImpact(self, voiture, kilometrage, indicateur="Climate change"):
        if not voiture.isValid():
            return {}

        resultats = {}
        tech_base = voiture.technologie_base
        nom_complet = voiture.technologie

        # FABRICATION
        if tech_base == "BEV" or tech_base == "PHEV-petrol" or tech_base == "FCEV":
            glider_name = "passenger car production Recycled content, electric, without battery"
        elif tech_base == "Diesel":
            glider_name = "passenger car production Recycled content, diesel"
        else:
            glider_name = "passenger car production Recycled content, petrol/natural gas"

        resultats["Manufacturing_Glider"] = voiture.getGliderMass() * self.getFacteur(glider_name, indicateur)
        resultats["Manufacturing_Battery"] = voiture.battery_capacity * self.getFacteur("battery production, average europe", indicateur)
        resultats["Manufacturing_FuelCell"] = voiture.fuel_cell_value * self.getFacteur("fuel cell system", indicateur)

        # USAGE WTT
        wtt_impact = 0.0
        if tech_base == "PHEV-petrol":
            elec_factor = self.getFacteur("prospective Electricity", indicateur)
            petrol_factor = self.getFacteur("petrol production", indicateur)
            wtt_impact = ((voiture.wtt_value * elec_factor) + (voiture.phev_wtt_value * petrol_factor)) / 100.0 * kilometrage
        else:
            factor_name = "petrol production"
            if tech_base == "Diesel": factor_name = "diesel production"
            elif tech_base == "CNG": factor_name = "CNG production"
            elif tech_base == "LPG": factor_name = "LPG production"
            elif tech_base == "BEV": factor_name = "Electricity_2050" if "2050" in nom_complet else "prospective Electricity"
            elif tech_base == "FCEV": factor_name = "hydrogen_green" if "Green" in nom_complet else "hydrogen_grey"
            
            wtt_impact = (voiture.wtt_value * self.getFacteur(factor_name, indicateur)) / 100.0 * kilometrage

        resultats["Usage_WTT"] = wtt_impact

        # USAGE TTW (Echappement + Pneus + Freins)
        impact_echappement = voiture.getTTW(indicateur) * kilometrage
        impact_pneus = voiture.tyre_wear_value * self.getFacteur("tyre_wear", indicateur) * kilometrage
        impact_freins = voiture.brake_wear_value * self.getFacteur("brake_wear", indicateur) * kilometrage
        
        resultats["Usage_TTW"] = impact_echappement + impact_pneus + impact_freins
        
        # ROAD & MAINTENANCE
        road_impact = voiture.road_value * self.getFacteur("road_maintenance", indicateur) * kilometrage
        maint_impact = ((voiture.road_maint_value * self.getFacteur("road_maintenance", indicateur)) + (voiture.maintenance_value * self.getFacteur("maintenance, passenger car", indicateur))) * kilometrage
        
        resultats["Usage_Maintenance"] = maint_impact
        resultats["Usage_Road"] = road_impact

        total = 0.0
        for val in resultats.values():
            total += val
        resultats["Total"] = total

        return resultats