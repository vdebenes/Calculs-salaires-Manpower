import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time, date as date_class
import io

# Fonction de calcul de salaire

def calcul_salaire(nom, date, tarif_horaire, heure_debut_str, heure_fin_str, pause_decimal, numero_mission):
    ...  # Fonction complète déjà présente

# Fonction d'export Excel
def generate_excel(df):
    ...  # Fonction complète déjà présente

# Fonction de conversion d'une pause (hh:mm ou h.mm) en décimal
def convert_pause_to_decimal(pause_str):
    if ":" in pause_str:
        heures, minutes = map(int, pause_str.split(":"))
        return round(heures + minutes / 60, 2)
    else:
        return float(pause_str)

# Interface utilisateur
st.set_page_config(page_title="Calculateur Salaire Manpower", layout="wide")
st.title("🧾 Calculateur de salaire Manpower")

if "data" not in st.session_state:
    st.session_state.data = []

col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("Données de base")
    numero_mission = st.text_input("Numéro de mission")
    nom = st.text_input("Nom du collaborateur")
    tarif_horaire = st.number_input("Tarif horaire (CHF)", min_value=0.0, format="%.2f")
    date = st.date_input("Date de la mission", value=datetime.today())
    heure_debut = st.time_input("Heure de début", value=time(8, 0))
    heure_fin = st.time_input("Heure de fin", value=time(17, 0))
    pause_str = st.text_input("Pause (hh:mm ou h.mm)", value="0:00")

    if st.button("Calculer"):
        pause_decimal = convert_pause_to_decimal(pause_str)
        result = calcul_salaire(nom, date, tarif_horaire, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"), pause_decimal, numero_mission)
        st.session_state.data.append(result)

    if st.button("Vider le formulaire"):
        st.experimental_rerun()

with col2:
    st.subheader("Résumé de la dernière mission")
    if st.session_state.data:
        dernier = st.session_state.data[-1]
        st.markdown(
            f"""
            <div style='background-color:#ffe6f0;padding:10px;border-radius:10px;'>
                <b>Mission :</b> {dernier['Mission']}  
                <b>Date :</b> {dernier['Date']}  
                <b>Heure de début :</b> {dernier['Heure de début']} — <b>Heure de fin :</b> {dernier['Heure de fin']}  
                <b>Nom :</b> {dernier['Nom']}  
                <b>Tarif horaire :</b> CHF {dernier['Tarif horaire']:.2f}  
                <b>Heures brutes :</b> {dernier['Heures brutes']:.2f} h  
                <b>Pause :</b> {pause_str}  
                <b>Heures totales :</b> {dernier['Heures totales (hh:mm)']} (soit {dernier['Heures totales']} h)  
                <b>Salaire de base :</b> CHF {dernier['Salaire de base']:.2f}  
                <b>Majoration 25% (heure sup) :</b> CHF {dernier['Majoration 25% (heure sup)']:.2f} — <b>Heures sup :</b> {dernier['Heures sup (hh:mm)']}  
                <b>Heures samedi :</b> {dernier['Heures samedi (hh:mm)']} — <b>Majoration samedi :</b> CHF {dernier['Majoration samedi']:.2f}  
                <b>Heures dimanche :</b> {dernier['Heures dimanche (hh:mm)']} — <b>Majoration dimanche :</b> CHF {dernier['Majoration dimanche']:.2f}  
                <b>Heures de nuit :</b> {dernier['Heures de nuit (hh:mm)']} — <b>Majoration nuit :</b> CHF {dernier['Majoration nuit']:.2f}  
                <b>Total brut :</b> <span style='font-weight:bold;'>CHF {dernier['Salaire total brut']:.2f}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

st.subheader("Historique des calculs")
if st.session_state.data:
    df_result = pd.DataFrame(st.session_state.data)
    st.dataframe(df_result, height=300)

    excel_data = generate_excel(df_result)
    st.download_button(
        label="📥 Télécharger en Excel",
        data=excel_data,
        file_name="missions_salaire_manpower.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
