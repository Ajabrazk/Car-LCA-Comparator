# Classe contenant les informations d'un véhicule
class Voiture:
    # Constructeur
    def __init__(self, tech, segment, masse, cap_batterie, masse_batterie, wtt, phev_wtt, fuel_cell, road, road_maint, maint):
        self.technologie = tech
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

    # Retourne la masse du chassis sans la batterie
    def getGliderMass(self):
        return self.masse_kg - self.battery_mass

    # Vérifie si le modèle de voiture existe vraiment (masse superieure a 0)
    def isValid(self):
        if self.masse_kg > 0:
            return True
        else:
            return False