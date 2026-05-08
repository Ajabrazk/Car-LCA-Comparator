import pandas as pd
from src.voiture import Voiture

# Classe qui gère la lecture du fichier Excel et les calculs d'impact
class ACVHandler:
    # Constructeur
    def __init__(self, fichier_excel):
        self.fichier = fichier_excel
        self.facteurs_emission = {}
        self.liste_voitures =[]
        
        # On remplit les données directement à la création de l'objet
        self.loadData()

    # Getters
    def getVoitures(self):
        return self.liste_voitures

    def getFacteur(self, nom_facteur):
        if nom_facteur in self.facteurs_emission:
            return self.facteurs_emission[nom_facteur]
        return 0.0

    # Methode utilitaire interne pour securiser la conversion en nombre (comme un helper C++)
    def parseFloat(self, valeur):
        try:
            valeur_texte = str(valeur).replace(',', '.')
            if valeur_texte == "" or valeur_texte == "nan":
                return 0.0
            return float(valeur_texte)
        except:
            return 0.0

    # Remplis les facteurs d'emission et la liste des voitures à partir de l'excel
    def loadData(self):
        # 1. Chargement des facteurs (sans sauter de ligne)
        df_facteurs = pd.read_excel(self.fichier, sheet_name="Emission factor")
        df_facteurs.columns = df_facteurs.columns.astype(str).str.strip()
        df_facteurs = df_facteurs.dropna(subset=['Index', 'Climate change'])
        
        for index, row in df_facteurs.iterrows():
            nom = str(row['Index']).strip()
            valeur = row['Climate change']
            self.facteurs_emission[nom] = valeur

        # 2. Chargement des voitures
        df_voitures = pd.read_excel(self.fichier, sheet_name="Car parameters")
        df_voitures.columns = df_voitures.columns.astype(str).str.strip()
        col_segment = df_voitures.columns[0] # La premiere colonne contient la taille
        
        # On bouche les trous des cellules fusionnées
        if "Fuel" in df_voitures.columns:
            df_voitures["Fuel"] = df_voitures["Fuel"].ffill()
        if col_segment in df_voitures.columns:
            df_voitures[col_segment] = df_voitures[col_segment].ffill()
            
        df_voitures = df_voitures.fillna(0.0)

        # Remplir la liste_voitures etape par etape
        for index, row in df_voitures.iterrows():
            tech = str(row.get("Fuel", "")).strip()
            segment = str(row.get(col_segment, "")).strip()
            
            if tech == "0.0" or segment == "0.0" or tech == "" or segment == "":
                continue

            nouvelle_voiture = Voiture(
                tech, 
                segment,
                self.parseFloat(row.get("Vehicle mass")),
                self.parseFloat(row.get("Battery capacity")),
                self.parseFloat(row.get("Battery mass")),
                self.parseFloat(row.get("WTT")),
                self.parseFloat(row.get("PHEV WTT")),
                self.parseFloat(row.get("Fuel cell")),
                self.parseFloat(row.get("Road")),
                self.parseFloat(row.get("Road maintenance")),
                self.parseFloat(row.get("Maintenance"))
            )
            
            # A chaque iteration, on ajoute la voiture si elle est valide
            if nouvelle_voiture.isValid():
                self.liste_voitures.append(nouvelle_voiture)

    # Calcule l'impact total de la voiture et renvoie un dictionnaire avec les resultats
    def calculerImpact(self, voiture, kilometrage, mix_type="Current"):
        if not voiture.isValid():
            return {}

        resultats = {}

        # PARTIE FABRICATION
        tech = voiture.technologie
        if tech == "BEV" or tech == "PHEV-petrol" or tech == "FCEV":
            glider_name = "passenger car production Recycled content, electric, without battery"
        elif tech == "Diesel":
            glider_name = "passenger car production Recycled content, diesel"
        else:
            glider_name = "passenger car production Recycled content, petrol/natural gas"

        resultats["Manufacturing_Glider"] = voiture.getGliderMass() * self.getFacteur(glider_name)
        resultats["Manufacturing_Battery"] = voiture.battery_capacity * self.getFacteur("battery production, average europe")
        resultats["Manufacturing_FuelCell"] = voiture.fuel_cell_value * self.getFacteur("fuel cell system")

        # PARTIE USAGE
        wtt_impact = 0.0
        if tech == "PHEV-petrol":
            if mix_type == "Current":
                elec_factor = self.getFacteur("prospective Electricity")
            else:
                elec_factor = self.getFacteur("Electricity_2050")
            petrol_factor = self.getFacteur("petrol production")
            wtt_impact = ((voiture.wtt_value * elec_factor) + (voiture.phev_wtt_value * petrol_factor)) / 100.0 * kilometrage
        else:
            factor_name = "petrol production"
            if tech == "Diesel": 
                factor_name = "diesel production"
            elif tech == "CNG": 
                factor_name = "CNG production"
            elif tech == "LPG": 
                factor_name = "LPG production"
            elif tech == "BEV": 
                if mix_type == "Current":
                    factor_name = "prospective Electricity"
                else:
                    factor_name = "Electricity_2050"
            elif tech == "FCEV": 
                if mix_type == "Grey":
                    factor_name = "hydrogen_grey"
                else:
                    factor_name = "hydrogen_green"
            
            wtt_impact = (voiture.wtt_value * self.getFacteur(factor_name)) / 100.0 * kilometrage

        resultats["Usage_WTT"] = wtt_impact
        resultats["Usage_TTW"] = 0.0 # Il manque encore les donnees d'echappement
        
        road_impact = voiture.road_value * self.getFacteur("road_maintenance") * kilometrage
        maint_impact = ((voiture.road_maint_value * self.getFacteur("road_maintenance")) + (voiture.maintenance_value * self.getFacteur("maintenance, passenger car"))) * kilometrage
        
        resultats["Usage_Maintenance"] = maint_impact
        resultats["Usage_Road"] = road_impact

        # Calcul du total
        total = 0.0
        for val in resultats.values():
            total += val
        resultats["Total"] = total

        return resultats