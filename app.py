import streamlit as st
import pandas as pd
import plotly.express as px
import os

from src.acv_handler import ACVHandler

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="Car LCA Comparator", layout="wide")

# Dictionnaire de couleurs fixes pour chaque technologie (pour synchroniser graphes et cartes)
COULEURS_TECH = {
    "Petrol": "#EF553B",        # Rouge
    "Diesel": "#66C2A5",        # Vert menthe
    "CNG": "#8DA0CB",           # Bleu clair
    "LPG": "#E78AC3",           # Rose
    "HEV-petrol": "#A6D854",    # Vert clair
    "PHEV-petrol": "#FFD92F",   # Jaune
    "BEV": "#E5C494",           # Sable/Beige
    "FCEV": "#B3B3B3"           # Gris
}

@st.cache_resource
def chargerDonnees():
    chemin_fichier = "data/lca_database.xlsx"
    if not os.path.exists(chemin_fichier):
        return None
    handler = ACVHandler(chemin_fichier)
    return handler

acv_handler = chargerDonnees()

if acv_handler is None:
    st.error("Error: Excel file not found. Please check the 'data/' folder.")
    st.stop()

# Gestion de l'etat des pages
if "page_actuelle" not in st.session_state:
    st.session_state["page_actuelle"] = "home"

# Initialisation des parametres par defaut
if "kilometrage_annuel" not in st.session_state:
    st.session_state["kilometrage_annuel"] = 15000
if "duree_vie" not in st.session_state:
    st.session_state["duree_vie"] = 10
if "scenario_energie" not in st.session_state:
    st.session_state["scenario_energie"] = "Current (Current / Grey)"
if "segment_choisi" not in st.session_state:
    st.session_state["segment_choisi"] = "Medium"
if "technologies_choisies" not in st.session_state:
    st.session_state["technologies_choisies"] =[]


# ---------------------------------------------------------
# FONCTION : PANNEAU DE PARAMETRES (Reutilisable)
# ---------------------------------------------------------
def afficherPanneauParametres():
    toutes_les_voitures = acv_handler.getVoitures()
    
    liste_segments =[]
    for v in toutes_les_voitures:
        if v.segment not in liste_segments:
            liste_segments.append(v.segment)
    liste_segments.sort()

    col1, col2 = st.columns(2)
    
    with col1:
        # Ajout des infobulles (help) pour plus de clarte
        st.session_state["kilometrage_annuel"] = st.slider("Annual mileage (km)", 5000, 50000, st.session_state["kilometrage_annuel"], 1000)
        st.session_state["duree_vie"] = st.slider("Lifespan (years)", 2, 20, st.session_state["duree_vie"], 1)
        st.session_state["scenario_energie"] = st.selectbox(
            "Energy scenario (BEV & FCEV)",["Current (Current / Grey)", "Future 2050 (2050 / Green)"], 
            index=0 if "Current" in st.session_state["scenario_energie"] else 1,
            help="Select the origin of electricity or hydrogen. 'Future 2050' simulates a fully decarbonized energy mix."
        )
        
    with col2:
        index_seg = 0
        for i in range(len(liste_segments)):
            if liste_segments[i] == st.session_state["segment_choisi"]:
                index_seg = i
                
        st.session_state["segment_choisi"] = st.selectbox(
            "Vehicle size (Segment)", 
            liste_segments, 
            index=index_seg,
            help="Compare vehicles within the same size category for a fair assessment."
        )
        
        technologies_disponibles =[]
        for v in toutes_les_voitures:
            if v.segment == st.session_state["segment_choisi"]:
                technologies_disponibles.append(v.technologie)
                
        defauts = st.session_state["technologies_choisies"]
        if len(defauts) == 0:
            defauts = technologies_disponibles[:3]
            
        st.session_state["technologies_choisies"] = st.multiselect("Technologies to compare", technologies_disponibles, default=defauts)


# ---------------------------------------------------------
# PAGE 1 : ACCUEIL
# ---------------------------------------------------------
if st.session_state["page_actuelle"] == "home":
    st.title("Automobile Life Cycle Assessment")
    
    st.subheader("What is Life Cycle Assessment (LCA)?")
    st.write("LCA is a scientific method that measures the total environmental impact of a product, from the extraction of raw materials to its end-of-life.")
    
    st.subheader("What is its role here?")
    st.write("It helps us look beyond just tailpipe emissions. By calculating the pollution from manufacturing the car, producing its battery, generating the energy, and driving it, we can fairly compare different technologies.")
    
    st.write("")
    st.write("")
    
    # Encadre centré pour le panneau
    with st.container(border=True):
        st.markdown("<h4 style='text-align: center;'>Simulation Parameters</h4>", unsafe_allow_html=True)
        st.write("")
        afficherPanneauParametres()
        
        st.write("")
        col_vide1, col_bouton, col_vide2 = st.columns([2, 1, 2])
        with col_bouton:
            if st.button("Compare", type="primary", use_container_width=True):
                if len(st.session_state["technologies_choisies"]) > 0:
                    st.session_state["page_actuelle"] = "results"
                    st.rerun()
                else:
                    st.error("Please select at least one technology.")

# ---------------------------------------------------------
# PAGE 2 : RESULTATS
# ---------------------------------------------------------
elif st.session_state["page_actuelle"] == "results":
    
    # Panneau de modification discret en haut
    with st.expander("⚙️ Modify parameters (Click to expand)"):
        afficherPanneauParametres()
        
    st.divider()

    # Calculs du backend
    kilometrage_total = st.session_state["kilometrage_annuel"] * st.session_state["duree_vie"]
    mix_type_standard = "Current"
    mix_type_fcev = "Grey"
    if "2050" in st.session_state["scenario_energie"]:
        mix_type_standard = "2050"
        mix_type_fcev = "Green"

    toutes_les_voitures = acv_handler.getVoitures()
    resultats_bruts = []
    vehicules_utilises =[] # On stocke les objets Voitures pour afficher leurs hypotheses a la fin

    for tech in st.session_state["technologies_choisies"]:
        voiture_actuelle = None
        for v in toutes_les_voitures:
            if v.segment == st.session_state["segment_choisi"] and v.technologie == tech:
                voiture_actuelle = v
                break
                
        if voiture_actuelle is not None:
            vehicules_utilises.append(voiture_actuelle)
            mix_a_envoyer = mix_type_standard
            if tech == "FCEV":
                mix_a_envoyer = mix_type_fcev
                
            impacts = acv_handler.calculerImpact(voiture_actuelle, kilometrage_total, mix_type=mix_a_envoyer)
            impacts["Technology"] = tech
            resultats_bruts.append(impacts)

    if len(resultats_bruts) == 0:
        st.error("No data to display.")
        st.stop()

    # Tri manuel par impact total
    def trier_par_total(dictionnaire):
        return dictionnaire["Total"]
        
    resultats_bruts.sort(key=trier_par_total)

    # --- SECTION : CLASSEMENT ---
    st.title("Results")
    st.write("Based on a total of **" + "{:,}".format(kilometrage_total).replace(',', ' ') + " km** over " + str(st.session_state["duree_vie"]) + " years.")
    
    for index in range(len(resultats_bruts)):
        tech_nom = resultats_bruts[index]["Technology"]
        st.markdown("### " + str(index + 1) + ". " + tech_nom)
        
    st.success("The least polluting vehicle for your usage is the **" + resultats_bruts[0]["Technology"] + "**.")

    st.divider()

    # --- SECTION : GRAPHE DECOMPOSITION ---
    st.header("Emissions breakdown")
    st.write("Each bar corresponds to a technology, and each color represents an emission source (production or use).")

    resultats_propres =[]
    traduction_legendes = {
        "Manufacturing_Glider": "Glider Manufacturing",
        "Manufacturing_Battery": "Battery Manufacturing",
        "Manufacturing_FuelCell": "Fuel Cell Manufacturing",
        "Usage_WTT": "Energy Production (WTT)",
        "Usage_TTW": "Tailpipe Emissions (TTW)",
        "Usage_Maintenance": "Vehicle Maintenance",
        "Usage_Road": "Road Wear"
    }

    for res in resultats_bruts:
        ligne_propre = {"Technology": res["Technology"]}
        for cle_tech, nom_clair in traduction_legendes.items():
            if cle_tech in res:
                ligne_propre[nom_clair] = res[cle_tech]
        resultats_propres.append(ligne_propre)

    df_barres = pd.DataFrame(resultats_propres)
    colonnes_a_afficher =[]
    for val in traduction_legendes.values():
        colonnes_a_afficher.append(val)

    # On utilise Plotly nativement. Les couleurs ici sont pour les PHASES, pas les technos.
    figure_barres = px.bar(
        df_barres, 
        x="Technology", 
        y=colonnes_a_afficher,
        labels={"value": "Emissions (kg CO2 eq)", "variable": "Lifecycle Phase", "Technology": "Technology"},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    figure_barres.update_layout(legend_title_text='')
    st.plotly_chart(figure_barres, width="stretch")


    # --- SECTION : GRAPHE EVOLUTION ---
    st.header("Evolution over time")
    st.write("Shows how much each technology pollutes throughout its life.")

    donnees_lignes =[]
    nb_etapes = 50
    pas_km = kilometrage_total / nb_etapes

    for res in resultats_bruts:
        tech = res["Technology"]
        fabrication = res.get("Manufacturing_Glider", 0) + res.get("Manufacturing_Battery", 0) + res.get("Manufacturing_FuelCell", 0)
        usage = res.get("Usage_WTT", 0) + res.get("Usage_TTW", 0) + res.get("Usage_Maintenance", 0) + res.get("Usage_Road", 0)
        
        impact_par_km = 0
        if kilometrage_total > 0:
            impact_par_km = usage / kilometrage_total
            
        for etape in range(int(nb_etapes) + 1):
            km_actuel = etape * pas_km
            donnees_lignes.append({
                "Technology": tech,
                "Mileage (km)": km_actuel,
                "Cumulative Emissions (kg CO2 eq)": fabrication + (impact_par_km * km_actuel)
            })

    df_lignes = pd.DataFrame(donnees_lignes)

    # Ici, la couleur represente la TECHNOLOGIE. On utilise notre dictionnaire COULEURS_TECH.
    figure_lignes = px.line(
        df_lignes, 
        x="Mileage (km)", 
        y="Cumulative Emissions (kg CO2 eq)", 
        color="Technology",
        color_discrete_map=COULEURS_TECH
    )
    figure_lignes.add_vline(x=kilometrage_total, line_dash="dash", line_color="red", annotation_text="End of life")
    st.plotly_chart(figure_lignes, width="stretch")

    st.divider()

    # --- SECTION : EN QUELQUES CHIFFRES ---
    st.header("In a few figures...")
    
    colonnes_metriques = st.columns(len(resultats_bruts))
    
    for i in range(len(resultats_bruts)):
        tech = resultats_bruts[i]["Technology"]
        total_tonnes = resultats_bruts[i]["Total"] / 1000.0
        vols_ny = int(total_tonnes / 1.5)
        
        # Recuperation de la couleur fixe pour cette technologie
        couleur_tech = COULEURS_TECH.get(tech, "#000000")
        
        with colonnes_metriques[i]:
            # Creation d'une belle "Card" avec une bordure de couleur grace a st.container
            with st.container(border=True):
                st.markdown(f"<h3 style='color: {couleur_tech}; margin-bottom: 0;'>■ {tech}</h3>", unsafe_allow_html=True)
                st.metric(label="Total impact", value=str(round(total_tonnes, 1)) + " t CO2 eq")
                st.caption(f"~ {vols_ny} Brussels-New York round trips*")

    st.write("")
    st.caption("*Assumption: 1 economy class round trip Brussels - New York per passenger emits approximately 1.5 tonnes of CO2 eq. (Source: ICAO / myclimate.org)")

    st.divider()
    
    # Assumption qu'on a fait
    st.header("Assumptions used for this calculation")
    st.write("To ensure transparency, here are the technical specifications used to model the " + st.session_state["segment_choisi"] + " vehicles :")
    
    # On affiche les caracteristiques de chaque voiture utilisee dans le calcul
    for voiture in vehicules_utilises:
        chaine_infos = "- **" + voiture.technologie + "** : Total mass = " + str(voiture.masse_kg) + " kg"
        if voiture.battery_capacity > 0:
            chaine_infos += " | Battery capacity = " + str(voiture.battery_capacity) + " kWh (" + str(voiture.battery_mass) + " kg)"
        st.write(chaine_infos)