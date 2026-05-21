import streamlit as st
import pandas as pd
import plotly.express as px
import os

from src.acv_handler import ACVHandler

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="Passenger Car LCA", page_icon="🚗", layout="wide")

COULEURS_TECH = {
    "Petrol": "#EF553B", "Diesel": "#66C2A5", "CNG": "#8DA0CB", "LPG": "#E78AC3",
    "HEV-petrol": "#A6D854", "PHEV-petrol (UF 2027 - 2050)": "#FFD92F",
    "BEV (Current)": "#E5C494", "BEV (2050)": "#F5DEB3",
    "FCEV (Grey)": "#B3B3B3", "FCEV (Green)": "#D3D3D3"
}

UNITES_IMPACT = {
    "Climate change": "kg CO₂eq",
    "Particulate matter formation": "Disease incidence",
    "Material resources: metals/minerals": "kg Sb eq",
    "Energy ressources: non-renewable": "MJ"
}

@st.cache_resource
def chargerDonnees():
    chemin_fichier = "data/lca_database.xlsx"
    if not os.path.exists(chemin_fichier):
        return None
    return ACVHandler(chemin_fichier)

acv_handler = chargerDonnees()

if acv_handler is None:
    st.error("Error: Excel file not found.")
    st.stop()

# Memoire d'etat
if "page_actuelle" not in st.session_state:
    st.session_state["page_actuelle"] = "home"
if "kilometrage_annuel" not in st.session_state:
    st.session_state["kilometrage_annuel"] = 15000
if "duree_vie" not in st.session_state:
    st.session_state["duree_vie"] = 10
if "segment_choisi" not in st.session_state:
    st.session_state["segment_choisi"] = "Medium"
if "technologies_choisies" not in st.session_state:
    st.session_state["technologies_choisies"] =[]
if "indicateur_choisi" not in st.session_state:
    st.session_state["indicateur_choisi"] = "Climate change"

# ---------------------------------------------------------
# EN-TETE FIXE
# ---------------------------------------------------------
st.title("Passenger Car Life Cycle Assessment")

st.markdown("### What is Life Cycle Assessment (LCA)?")
st.write("LCA is a scientific method that measures the total environmental impact of a product from the extraction of raw materials to its end-of-life (included here via the 'recycled content' approach).")

st.markdown("### What is its role here?")
st.write("It helps us look beyond just tailpipe exhaust. By calculating the impact from manufacturing the car, producing its energy (**Well-to-Tank**), and driving it (**Tank-to-Wheel**), we can compare different technologies **as accurately as possible** across multiple environmental indicators (such as climate change, air quality, resource depletion, etc.).")

st.write("")

# ---------------------------------------------------------
# FONCTION : PANNEAU DE PARAMETRES
# ---------------------------------------------------------
def afficherPanneauParametres():
    toutes_les_voitures = acv_handler.getVoitures()
    tous_les_indicateurs = acv_handler.getIndicateurs()
    
    index_ind = tous_les_indicateurs.index(st.session_state["indicateur_choisi"]) if st.session_state["indicateur_choisi"] in tous_les_indicateurs else 0
    st.session_state["indicateur_choisi"] = st.selectbox("🌍 Select Environmental Impact Indicator", tous_les_indicateurs, index=index_ind)

    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state["kilometrage_annuel"] = st.slider("Annual mileage (km)", 5000, 50000, st.session_state["kilometrage_annuel"], 1000)
        st.session_state["duree_vie"] = st.slider("Lifespan (years)", 2, 20, st.session_state["duree_vie"], 1)
        km_totaux = st.session_state["kilometrage_annuel"] * st.session_state["duree_vie"]
        st.info(f"**Total calculated mileage:** {km_totaux:,} km".replace(',', ' '))
        
    with col2:
        liste_segments = sorted(list(set([v.segment for v in toutes_les_voitures])))
        index_seg = liste_segments.index(st.session_state["segment_choisi"]) if st.session_state["segment_choisi"] in liste_segments else 0
        st.session_state["segment_choisi"] = st.selectbox("Vehicle size (Segment)", liste_segments, index=index_seg)
        
        technologies_disponibles = [v.technologie for v in toutes_les_voitures if v.segment == st.session_state["segment_choisi"]]
        
        st.session_state["technologies_choisies"] = st.multiselect(
            "Technologies to compare (Scenarios are independent)", 
            technologies_disponibles, 
            default=[t for t in st.session_state["technologies_choisies"] if t in technologies_disponibles]
        )

# ---------------------------------------------------------
# PAGE 1 : ACCUEIL
# ---------------------------------------------------------
if st.session_state["page_actuelle"] == "home":
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
    
    with st.expander("⚙️ Modify parameters (Click to expand)"):
        afficherPanneauParametres()
    st.divider()

    kilometrage_total = st.session_state["kilometrage_annuel"] * st.session_state["duree_vie"]
    ind_choisi = st.session_state["indicateur_choisi"]
    unite_impact = UNITES_IMPACT.get(ind_choisi, "Score")

    toutes_les_voitures = acv_handler.getVoitures()
    resultats_bruts = []
    vehicules_utilises =[]

    for tech in st.session_state["technologies_choisies"]:
        voiture_actuelle = None
        for v in toutes_les_voitures:
            if v.segment == st.session_state["segment_choisi"] and v.technologie == tech:
                voiture_actuelle = v
                break
                
        if voiture_actuelle is not None:
            vehicules_utilises.append(voiture_actuelle)
            impacts = acv_handler.calculerImpact(voiture_actuelle, kilometrage_total, indicateur=ind_choisi)
            impacts["Technology"] = tech
            resultats_bruts.append(impacts)

    if len(resultats_bruts) == 0:
        st.error("No data to display.")
        st.stop()

    def trier_par_total(dictionnaire):
        return dictionnaire["Total"]
    resultats_bruts.sort(key=trier_par_total)

    # --- CLASSEMENT ---                            
    st.title("Results")         
    for index in range(len(resultats_bruts)):           
        st.markdown("### " + str(index + 1) + ". " + resultats_bruts[index]["Technology"])          
        
    st.success("The best performing vehicle for your usage on this indicator is the **" + resultats_bruts[0]["Technology"] + "**.")
    st.divider()

    # --- GRAPHE DECOMPOSITION ---  
    st.header("Impact breakdown")           
    st.write("Each bar corresponds to a technology, and each color represents an impact source (production or use).")       

    resultats_propres =[]
    traduction_legendes = {         
        "Manufacturing_Glider": "Glider Manufacturing",         
        "Manufacturing_Battery": "Battery Manufacturing",           
        "Manufacturing_FuelCell": "Fuel Cell Manufacturing",            
        "Usage_WTT": "Energy Production (WTT)",         
        "Usage_TTW": "Tailpipe & Direct Emissions (TTW)",           
        "Usage_Maintenance": "Vehicle Maintenance",         
        "Usage_Road": "Road Wear"               
    }

    for res in resultats_bruts:         
        ligne = {"Technology": res["Technology"]}
        for cle_tech, nom_clair in traduction_legendes.items():
            ligne[nom_clair] = res.get(cle_tech, 0.0)
        resultats_propres.append(ligne)

    df_barres = pd.DataFrame(resultats_propres)
    colonnes_a_afficher = list(traduction_legendes.values())

    for col in colonnes_a_afficher:
        if col not in df_barres.columns:
            df_barres[col] = 0.0

    figure_barres = px.bar(
        df_barres, x="Technology", y=colonnes_a_afficher,
        labels={"value": f"Total Impact ({unite_impact})", "variable": "Lifecycle Phase", "Technology": "Technology"},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    figure_barres.update_layout(legend_title_text='')
    st.plotly_chart(figure_barres, width="stretch")

    # --- GRAPHE EVOLUTION ---
    st.header("Evolution over time")
    st.write("Shows how the environmental impact accumulates throughout the vehicle's life.")

    donnees_lignes =[]
    nb_etapes = 50
    pas_km = kilometrage_total / nb_etapes

    for res in resultats_bruts:
        tech = res["Technology"]
        fabrication = res.get("Manufacturing_Glider", 0) + res.get("Manufacturing_Battery", 0) + res.get("Manufacturing_FuelCell", 0)
        usage = res.get("Usage_WTT", 0) + res.get("Usage_TTW", 0) + res.get("Usage_Maintenance", 0) + res.get("Usage_Road", 0)
        impact_par_km = usage / kilometrage_total if kilometrage_total > 0 else 0
            
        for etape in range(int(nb_etapes) + 1):
            km_actuel = etape * pas_km
            donnees_lignes.append({
                "Technology": tech, "Mileage (km)": km_actuel, "Cumulative Impact": fabrication + (impact_par_km * km_actuel)
            })

    df_lignes = pd.DataFrame(donnees_lignes)
    figure_lignes = px.line(
        df_lignes, x="Mileage (km)", y="Cumulative Impact", color="Technology", color_discrete_map=COULEURS_TECH,
        labels={"Cumulative Impact": f"Cumulative Impact ({unite_impact})"}
    )
    figure_lignes.add_vline(x=kilometrage_total, line_dash="dash", line_color="red", annotation_text="End of life")
    st.plotly_chart(figure_lignes, width="stretch")
    
    # --- INTERPRETATION DYNAMIQUE DU GRAPHIQUE ---
    st.markdown("#### 💡 Graph Interpretation")
    
    max_fabrication = -1.0
    tech_max_fab = ""
    for res in resultats_bruts:
        fab = res.get("Manufacturing_Glider", 0) + res.get("Manufacturing_Battery", 0) + res.get("Manufacturing_FuelCell", 0)
        if fab > max_fabrication:
            max_fabrication = fab
            tech_max_fab = res["Technology"]
            
    st.write(f"- **Initial Phase:** The **{tech_max_fab}** has the highest initial environmental cost due to its manufacturing process.")
    
    croisements_trouves = []
    for i in range(len(resultats_bruts)):
        for j in range(i + 1, len(resultats_bruts)):
            res1 = resultats_bruts[i]
            res2 = resultats_bruts[j]
            
            fab1 = res1.get("Manufacturing_Glider", 0) + res1.get("Manufacturing_Battery", 0) + res1.get("Manufacturing_FuelCell", 0)
            usage1 = res1.get("Usage_WTT", 0) + res1.get("Usage_TTW", 0) + res1.get("Usage_Maintenance", 0) + res1.get("Usage_Road", 0)
            pente1 = usage1 / kilometrage_total if kilometrage_total > 0 else 0
            
            fab2 = res2.get("Manufacturing_Glider", 0) + res2.get("Manufacturing_Battery", 0) + res2.get("Manufacturing_FuelCell", 0)
            usage2 = res2.get("Usage_WTT", 0) + res2.get("Usage_TTW", 0) + res2.get("Usage_Maintenance", 0) + res2.get("Usage_Road", 0)
            pente2 = usage2 / kilometrage_total if kilometrage_total > 0 else 0
            
            if pente1 != pente2:
                km_croisement = (fab2 - fab1) / (pente1 - pente2)
                if 0 < km_croisement < kilometrage_total:
                    if pente1 < pente2:
                        gagnant, perdant = res1["Technology"], res2["Technology"]
                    else:
                        gagnant, perdant = res2["Technology"], res1["Technology"]
                    
                    texte = f"- **Break-even point:** The **{gagnant}** becomes a greener option than the **{perdant}** after **{int(km_croisement):,} km**.".replace(',', ' ')
                    croisements_trouves.append(texte)
                    
    for texte in croisements_trouves:
        st.write(texte)
        
    st.write(f"- **End of life:** Ultimately, the **{resultats_bruts[0]['Technology']}** is the best long-term option for this specific indicator based on your mileage.")

    st.divider()

    # --- EN QUELQUES CHIFFRES (EQUIVALENCES) ---
    st.header("In a few figures...")
    colonnes_metriques = st.columns(len(resultats_bruts))
    
    for i in range(len(resultats_bruts)):
        tech = resultats_bruts[i]["Technology"]
        total_valeur = resultats_bruts[i]["Total"]
        couleur_tech = COULEURS_TECH.get(tech, "#000000")
        
        if total_valeur < 0.01:
            texte_valeur = f"{total_valeur:.2e}" 
        elif total_valeur > 1000:
            texte_valeur = f"{int(total_valeur):,}".replace(',', ' ') 
        else:
            texte_valeur = f"{total_valeur:.2f}" 
        
        with colonnes_metriques[i]:
            with st.container(border=True):
                st.markdown(f"<h3 style='color: {couleur_tech}; margin-bottom: 0;'>■ {tech}</h3>", unsafe_allow_html=True)
                
                if ind_choisi == "Climate change":
                    total_tonnes = total_valeur / 1000.0
                    budget_annees = total_tonnes / 2.0
                    st.metric(label=f"Total ({unite_impact})", value=str(round(total_tonnes, 1)) + " t CO₂eq")
                    st.caption(f"🌍 Consumes **{round(budget_annees, 1)} years** of a person's carbon budget*")
                    
                elif ind_choisi == "Energy ressources: non-renewable":
                    st.metric(label=f"Total ({unite_impact})", value=texte_valeur)
                    foyers = total_valeur / 50000.0
                    st.caption(f"⚡ Equivalent to powering a home for **{round(foyers, 1)} years***")
                    
                elif ind_choisi == "Material resources: metals/minerals":
                    st.metric(label=f"Total ({unite_impact})", value=texte_valeur)
                    smartphones = int(total_valeur / 0.01)
                    st.caption(f"📱 Equivalent to the minerals needed for **{smartphones:,} smartphones***".replace(',', ' '))
                    
                elif ind_choisi == "Particulate matter formation":
                    st.metric(label=f"Total ({unite_impact})", value=texte_valeur)
                    # 1 kg de bois brulé = ~10g PM2.5 = ~0.000006 Disease incidence
                    kg_bois = int(total_valeur / 0.000006)
                    st.caption(f"🔥 Equivalent to the particulate pollution from burning **{kg_bois:,} kg of wood** in an open fire*".replace(',', ' '))

    st.write("")
    if ind_choisi == "Climate change":
        st.caption("*Assumption: Target of 2 tonnes CO₂eq per person per year to limit global warming to +1.5°C (Source: vert.eco)")
    elif ind_choisi == "Energy ressources: non-renewable":
        st.caption("*Assumption: 1 average European household consumes approximately 50,000 MJ of total energy per year for heating and electricity (Source: Eurostat)")
    elif ind_choisi == "Material resources: metals/minerals":
        st.caption("*Assumption: Manufacturing 1 high-end smartphone requires approximately 0.01 kg Sb eq of rare minerals and metals (Source: Fairphone LCA Report / Ecoinvent)")
    elif ind_choisi == "Particulate matter formation":
        st.caption("*Assumption: Burning 1 kg of wood in an open fireplace emits ~10g of PM2.5, equivalent to ~0.000006 Disease incidence (Source: EMEP/EEA Air Pollutant Emission Inventory Guidebook / EF 3.0)")
        
    st.divider()
    
    # --- ASSUMPTIONS (DONNEES TECHNIQUES DU CALCUL) ---
    st.header("Assumptions used for this calculation")
    st.write("Chosen parameters: Segment **" + st.session_state["segment_choisi"] + "** | Total mileage: **" + "{:,}".format(kilometrage_total).replace(',', ' ') + " km**.")
    
    for v in vehicules_utilises:
        chaine_infos = "- **" + v.technologie + "** : Total mass = " + str(v.masse_kg) + " kg"
        
        if v.technologie_base == "PHEV-petrol":
            chaine_infos += " | Energy parameter (Electric) = " + str(v.wtt_value) + " | Energy parameter (Thermal) = " + str(v.phev_wtt_value)
        else:
            chaine_infos += " | Energy parameter = " + str(v.wtt_value)
            
        if v.battery_capacity > 0:
            chaine_infos += " | Battery capacity = " + str(v.battery_capacity) + " kWh"
            
        st.write(chaine_infos)

# ---------------------------------------------------------
# DESCRIPTION DES INDICATEURS
# ---------------------------------------------------------
with st.expander("ℹ️ About the Environmental Impact Categories"):
    st.markdown("""
    To keep the analysis clear and relevant, we have selected the 4 most critical impact categories to illustrate the trade-offs between vehicle technologies:
    
    * **Climate change (`kg CO₂eq`):** Impact on global warming due to greenhouse gas emissions. This is the standard metric for carbon footprint.
    * **Particulate matter formation (`Disease incidence`):** Fine dust emissions impacting human respiratory health. Crucial for urban air quality, it accounts for tailpipe exhaust, but also **tire and brake wear** (which affects even electric vehicles due to their weight).
    * **Material resources: metals/minerals (`kg Sb eq`):** Depletion of mineral resources (measured in Antimony equivalent). This indicator perfectly highlights the hidden environmental cost of manufacturing EV batteries (mining lithium, cobalt, etc.).
    * **Energy ressources: non-renewable (`MJ`):** Depletion of fossil fuels (oil, coal, gas). Highlights the difference between burning petrol daily versus relying on electricity (which can be renewable).
    """)