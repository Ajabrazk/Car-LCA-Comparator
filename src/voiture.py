# Classe contenant les informations d'un véhicule
class Voiture:
    # Constructeur
    def __init__(self, tech_base, nom_affichage, segment, masse, cap_batterie, masse_batterie, wtt, phev_wtt, fuel_cell, road, road_maint, maint, ttw_dict, tyre, brake):
        self.technologie_base = tech_base       
        self.technologie = nom_affichage        
        self.segment = segment
        self.masse_kg = float(masse)
        self.battery_capacity = float(cap_batterie)
        self.battery_mass = float(masse_batterie)
        self.wtt_value = float(wtt)
        self.phev_wtt_value = float(phev_wtt)
        self.fuel_cell_value = float(fuel_cell)
        self.road_value = float(road)
        self.road_maint_value = float(road_maint)
        self.maintenance_value = float(maint)
        
        # CORRECTION : ttw_dict est un dictionnaire, on ne fait pas float() dessus
        self.ttw_dict = ttw_dict
        
        self.tyre_wear_value = float(tyre)
        self.brake_wear_value = float(brake)

    # Retourne la masse du chassis sans la batterie
    def getGliderMass(self):
        return self.masse_kg - self.battery_mass

    # Methode pour recuperer l'echappement selon l'indicateur choisi
    def getTTW(self, indicateur):
        if indicateur in self.ttw_dict:
            return self.ttw_dict[indicateur]
        return 0.0

    # Vérifie si le modèle de voiture existe vraiment (masse superieure a 0)
    def isValid(self):
        if self.masse_kg > 0:
            return True
        else:
            return False